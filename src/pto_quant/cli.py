"""Command-line entry point for governed PTO research operations."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from pto_quant.config import ConfigValidationError, load_config
from pto_quant.data.client import BinancePublicClient, PublicDataError
from pto_quant.data.pipeline import (
    acquire_symbol,
    acquire_symbol_vision,
    git_sha,
    validate_symbol,
)
from pto_quant.data.vision import BinanceVisionClient, months_between
from pto_quant.governance.holdout import (
    TRUSTED_PHASE1_END_MS,
    TRUSTED_PHASE1_START_MS,
    TRUSTED_PHASE1_SYMBOLS,
    HoldoutAccessDenied,
    trusted_phase1_guard,
)
from pto_quant.governance.manifest import sha256_file


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pto", description="PTO adaptive quant research CLI")
    commands = parser.add_subparsers(dest="command", required=True)

    config = commands.add_parser("config", help="configuration operations")
    config_commands = config.add_subparsers(dest="config_command", required=True)
    validate = config_commands.add_parser("validate", help="validate all config contracts")
    validate.add_argument("--config-dir", default="config")

    project = commands.add_parser("project", help="project metadata")
    project_commands = project.add_subparsers(dest="project_command", required=True)
    info = project_commands.add_parser("info", help="print validated project information")
    info.add_argument("--config-dir", default="config")

    data = commands.add_parser("data", help="Phase 1 public-data operations")
    data_commands = data.add_subparsers(dest="data_command", required=True)
    acquire = data_commands.add_parser("acquire", help="download and normalize bounded public data")
    acquire.add_argument("--config-dir", default="config")
    acquire.add_argument("--root", default=".")
    acquire.add_argument("--symbol", action="append", dest="symbols")
    acquire.add_argument("--start", required=True, help="inclusive UTC timestamp")
    acquire.add_argument("--end", required=True, help="inclusive UTC timestamp")
    acquire.add_argument("--base-url", default="https://fapi.binance.com")
    acquire.add_argument(
        "--transport",
        choices=("rest", "vision"),
        default="rest",
        help="public historical-data transport",
    )
    validate_data = data_commands.add_parser("validate", help="fail on critical normalized defects")
    validate_data.add_argument("--config-dir", default="config")
    validate_data.add_argument("--root", default=".")
    validate_data.add_argument("--symbol", action="append", dest="symbols")
    gate = data_commands.add_parser("gate", help="atomically generate the Phase 1 data gate")
    gate.add_argument("--config-dir", default="config")
    gate.add_argument("--root", default=".")
    gate.add_argument("--output", default="reports/phase_01/gate.json")
    return parser


def _timestamp_ms(value: str) -> int:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamps must include a timezone")
    return int(parsed.astimezone(UTC).timestamp() * 1000)


def _governed_request(
    *,
    requested_symbols: list[str] | None,
    configured_symbols: tuple[str, ...],
    start_ms: int | None = None,
    end_ms: int | None = None,
    research: dict[str, object],
) -> tuple[str, ...]:
    symbols = tuple(requested_symbols or configured_symbols)
    if tuple(configured_symbols) != TRUSTED_PHASE1_SYMBOLS:
        raise ValueError("configured market universe is not trusted")
    unknown = sorted(set(symbols) - set(configured_symbols))
    if unknown:
        raise ValueError(f"symbols outside governed universe: {', '.join(unknown)}")
    if len(set(symbols)) != len(symbols):
        raise ValueError("duplicate --symbol values are not allowed")
    if start_ms is not None and end_ms is not None:
        guard = trusted_phase1_guard()
        try:
            guard.assert_research_interval(start_ms, end_ms)
        except HoldoutAccessDenied as exc:
            raise ValueError(
                "requested interval is outside the governed Phase 1 research boundary"
            ) from exc
        governance = research.get("governance")
        if not isinstance(governance, dict):
            raise ValueError("research.governance is missing")
        lower = _timestamp_ms(str(governance["phase1_research_start_utc"]))
        upper = _timestamp_ms(str(governance["phase1_research_end_utc"]))
        try:
            guard.assert_configured_research_interval(lower, upper)
        except HoldoutAccessDenied as exc:
            raise ValueError("configured Phase 1 research boundary is not trusted") from exc
    return symbols


def _trusted_phase1_window(research: dict[str, object]) -> tuple[int, int]:
    """Return the immutable Phase 1 window after checking editable config."""

    governance = research.get("governance")
    if not isinstance(governance, dict):
        raise ValueError("research.governance is missing")
    lower = _timestamp_ms(str(governance["phase1_research_start_utc"]))
    upper = _timestamp_ms(str(governance["phase1_research_end_utc"]))
    try:
        trusted_phase1_guard().assert_configured_research_interval(lower, upper)
    except HoldoutAccessDenied as exc:
        raise ValueError("configured Phase 1 research boundary is not trusted") from exc
    return TRUSTED_PHASE1_START_MS, TRUSTED_PHASE1_END_MS


def _atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    except BaseException:
        Path(temp_name).unlink(missing_ok=True)
        raise


def _manifest_paths(root: Path) -> list[Path]:
    return sorted(
        (
            *(root / "data" / "manifests").rglob("*.manifest.json"),
            *(root / "data" / "raw" / "binance_vision").rglob("*.manifest.json"),
        )
    )


def _build_evidence_index(
    root: Path, *, generated_at: str, implementation_git_sha: str
) -> dict[str, object]:
    entries: list[dict[str, object]] = []
    for path in _manifest_paths(root):
        try:
            manifest: object = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            manifest = {"parse_error": str(exc)}
        entries.append(
            {
                "path": path.relative_to(root).as_posix(),
                "checksum_sha256": sha256_file(path),
                "bytes": path.stat().st_size,
                "manifest": manifest,
            }
        )
    return {
        "schema_version": 2,
        "generated_at": generated_at,
        "implementation_git_sha": implementation_git_sha,
        "manifests": entries,
    }


def _build_phase_manifest(
    root: Path,
    *,
    gate_path: Path,
    evidence_index_path: Path,
    implementation_git_sha: str,
    config_hash: str,
    status: str,
    generated_at: str,
) -> dict[str, object]:
    artifacts = {"gate": gate_path, "evidence_index": evidence_index_path}
    for key, path in (
        ("phase_report", root / "reports" / "phase_01" / "PHASE_01_REPORT.md"),
        ("status", root / "STATUS.md"),
    ):
        if path.is_file():
            artifacts[key] = path
    return {
        "schema_version": 3,
        "phase": 1,
        "status": status,
        "created_at": generated_at,
        "implementation_git_sha": implementation_git_sha,
        "git_sha": implementation_git_sha,
        "config_hash": config_hash,
        "artifact_hashes": {key: sha256_file(path) for key, path in sorted(artifacts.items())},
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process-compatible status code."""

    args = _parser().parse_args(argv)
    try:
        bundle = load_config(args.config_dir)
    except ConfigValidationError as exc:
        print(f"configuration validation failed:\n{exc}", file=sys.stderr)
        return 2

    if args.command == "config" and args.config_command == "validate":
        print(f"configuration valid: {bundle.config_dir}")
        return 0
    if args.command == "project" and args.project_command == "info":
        print(json.dumps(asdict(bundle.project), indent=2, sort_keys=True))
        return 0
    configured_symbols = (
        bundle.markets.primary_symbol,
        *bundle.markets.generalization_symbols,
    )
    if args.command == "data" and args.data_command == "acquire":
        try:
            start_ms = _timestamp_ms(args.start)
            end_ms = _timestamp_ms(args.end)
            if end_ms < start_ms:
                raise ValueError("--end must be at or after --start")
            symbols = _governed_request(
                requested_symbols=args.symbols,
                configured_symbols=configured_symbols,
                start_ms=start_ms,
                end_ms=end_ms,
                research=bundle.research,
            )
            root = Path(args.root).resolve()
            revision = git_sha(root)
            if args.transport == "vision":
                vision_client = BinanceVisionClient(
                    args.base_url
                    if args.base_url != "https://fapi.binance.com"
                    else "https://data.binance.vision"
                )
                months = months_between(start_ms, end_ms)
                results = [
                    acquire_symbol_vision(
                        vision_client,
                        root=root,
                        symbol=symbol,
                        months=months,
                        start_ms=start_ms,
                        end_ms=end_ms,
                        config_hash=bundle.project.config_hash,
                        revision=revision,
                    )
                    for symbol in symbols
                ]
            else:
                rest_client = BinancePublicClient(args.base_url)
                results = [
                    acquire_symbol(
                        rest_client,
                        root=root,
                        symbol=symbol,
                        start_ms=start_ms,
                        end_ms=end_ms,
                        config_hash=bundle.project.config_hash,
                        revision=revision,
                    )
                    for symbol in symbols
                ]
        except (OSError, ValueError, PublicDataError) as exc:
            print(f"data acquisition failed: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(results, indent=2, sort_keys=True))
        return 2 if any(result["qa"]["critical_count"] for result in results) else 0
    if args.command == "data" and args.data_command == "validate":
        root = Path(args.root).resolve()
        try:
            start_ms, end_ms = _trusted_phase1_window(bundle.research)
            symbols = _governed_request(
                requested_symbols=args.symbols,
                configured_symbols=configured_symbols,
                start_ms=start_ms,
                end_ms=end_ms,
                research=bundle.research,
            )
        except ValueError as exc:
            print(f"data validation failed: {exc}", file=sys.stderr)
            return 2
        validation_results = {
            symbol: validate_symbol(
                root,
                symbol,
                expected_start_ms=start_ms,
                expected_end_ms=end_ms,
                minimum_history_days=bundle.markets.minimum_history_days_research,
                expected_config_hash=bundle.project.config_hash,
            ).to_dict()
            for symbol in symbols
        }
        print(json.dumps(validation_results, indent=2, sort_keys=True))
        return 2 if any(result["critical_count"] for result in validation_results.values()) else 0
    if args.command == "data" and args.data_command == "gate":
        root = Path(args.root).resolve()
        try:
            start_ms, end_ms = _trusted_phase1_window(bundle.research)
            _governed_request(
                requested_symbols=None,
                configured_symbols=configured_symbols,
                start_ms=start_ms,
                end_ms=end_ms,
                research=bundle.research,
            )
            implementation = git_sha(root)
            validation_results = {
                symbol: validate_symbol(
                    root,
                    symbol,
                    expected_start_ms=start_ms,
                    expected_end_ms=end_ms,
                    minimum_history_days=bundle.markets.minimum_history_days_research,
                    expected_config_hash=bundle.project.config_hash,
                ).to_dict()
                for symbol in configured_symbols
            }
            passed = bool(configured_symbols) and not any(
                result["critical_count"] for result in validation_results.values()
            )
            gate_status = "PASS" if passed else "FAIL"
            generated_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
            index_path = root / "data" / "manifests" / "evidence-index.json"
            evidence_index = _build_evidence_index(
                root, generated_at=generated_at, implementation_git_sha=implementation
            )
            _atomic_json(index_path, evidence_index)
            output = root / args.output
            evidence = {
                "schema_version": 3,
                "phase": 1,
                "status": gate_status,
                "implementation_git_sha": implementation,
                "config_hash": bundle.project.config_hash,
                "expected_start_ms": start_ms,
                "expected_end_ms": end_ms,
                "minimum_history_days": bundle.markets.minimum_history_days_research,
                "generated_at": generated_at,
                "evidence_index_path": index_path.relative_to(root).as_posix(),
                "evidence_index_sha256": sha256_file(index_path),
                "symbols": validation_results,
            }
            _atomic_json(output, evidence)
            phase_manifest_path = root / "reports" / "phase_01" / "phase_manifest.json"
            _atomic_json(
                phase_manifest_path,
                _build_phase_manifest(
                    root,
                    gate_path=output,
                    evidence_index_path=index_path,
                    implementation_git_sha=implementation,
                    config_hash=bundle.project.config_hash,
                    status=gate_status,
                    generated_at=generated_at,
                ),
            )
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            print(f"data gate failed: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(evidence, indent=2, sort_keys=True))
        return 0 if passed else 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
