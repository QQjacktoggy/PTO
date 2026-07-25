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
    unknown = sorted(set(symbols) - set(configured_symbols))
    if unknown:
        raise ValueError(f"symbols outside governed universe: {', '.join(unknown)}")
    if len(set(symbols)) != len(symbols):
        raise ValueError("duplicate --symbol values are not allowed")
    if start_ms is not None and end_ms is not None:
        governance = research.get("governance")
        if not isinstance(governance, dict):
            raise ValueError("research.governance is missing")
        lower = _timestamp_ms(str(governance["phase1_research_start_utc"]))
        upper = _timestamp_ms(str(governance["phase1_research_end_utc"]))
        if start_ms < lower or end_ms > upper:
            raise ValueError("requested interval is outside the governed Phase 1 research boundary")
    return symbols


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
            symbols = _governed_request(
                requested_symbols=args.symbols,
                configured_symbols=configured_symbols,
                research=bundle.research,
            )
        except ValueError as exc:
            print(f"data validation failed: {exc}", file=sys.stderr)
            return 2
        validation_results = {symbol: validate_symbol(root, symbol).to_dict() for symbol in symbols}
        print(json.dumps(validation_results, indent=2, sort_keys=True))
        return 2 if any(result["critical_count"] for result in validation_results.values()) else 0
    if args.command == "data" and args.data_command == "gate":
        root = Path(args.root).resolve()
        validation_results = {
            symbol: validate_symbol(root, symbol).to_dict() for symbol in configured_symbols
        }
        passed = not any(result["critical_count"] for result in validation_results.values())
        evidence = {
            "schema_version": 2,
            "phase": 1,
            "status": "PASS" if passed else "FAIL",
            "implementation_git_sha": git_sha(root),
            "config_hash": bundle.project.config_hash,
            "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "symbols": validation_results,
        }
        manifest_files = sorted(
            (
                *(root / "data" / "manifests").rglob("*.manifest.json"),
                *(root / "data" / "raw" / "binance_vision").rglob("*.manifest.json"),
            )
        )
        evidence_index = {
            "schema_version": 1,
            "generated_at": evidence["generated_at"],
            "implementation_git_sha": evidence["implementation_git_sha"],
            "manifests": [
                {
                    "path": path.relative_to(root).as_posix(),
                    "checksum_sha256": sha256_file(path),
                    "bytes": path.stat().st_size,
                    "manifest": json.loads(path.read_text(encoding="utf-8")),
                }
                for path in manifest_files
            ],
        }
        index_path = root / "data" / "manifests" / "evidence-index.json"
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(
            json.dumps(evidence_index, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        output = root / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temp_name = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(evidence, stream, indent=2, sort_keys=True)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_name, output)
        except BaseException:
            Path(temp_name).unlink(missing_ok=True)
            raise
        print(json.dumps(evidence, indent=2, sort_keys=True))
        return 0 if passed else 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
