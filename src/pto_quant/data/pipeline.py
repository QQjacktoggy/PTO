"""Phase 1 public data acquisition, normalization, QA, and manifests."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pto_quant.data.client import BinancePublicClient
from pto_quant.data.io import read_funding, read_klines, write_funding, write_klines
from pto_quant.data.models import FundingRate, Kline
from pto_quant.data.qa import (
    INTERVAL_MS,
    QualityIssue,
    QualityResult,
    last_complete_open_time,
    validate_klines,
)
from pto_quant.data.resample import resample_completed
from pto_quant.data.vision import (
    BinanceVisionClient,
    parse_vision_funding,
    parse_vision_klines,
)
from pto_quant.governance.manifest import sha256_file


@dataclass(frozen=True)
class DatasetManifest:
    schema_version: int
    source: str
    symbol: str
    interval: str
    range_start_ms: int
    range_end_ms: int
    rows: int
    checksum_sha256: str
    git_sha: str
    config_hash: str
    created_at: str
    market: str
    file_size_bytes: int
    quality_status: str
    source_artifacts: tuple[str, ...]


DAY_MS = 86_400_000
KLINE_STEP_MS = INTERVAL_MS["1m"]


def _atomic_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    except BaseException:
        Path(temp_name).unlink(missing_ok=True)
        raise


def _write_json(path: Path, value: object) -> None:
    _atomic_bytes(path, (json.dumps(value, indent=2, sort_keys=True) + "\n").encode())


def _write_immutable_json(path: Path, value: object) -> None:
    """Create raw evidence once; identical retries are accepted, changes are rejected."""

    payload = json.dumps(value, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text(encoding="utf-8") != payload:
            raise ValueError(f"immutable raw artifact differs on retry: {path}")
        return
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload.encode())
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
        path.chmod(0o444)
    except FileExistsError:
        Path(temp_name).unlink(missing_ok=True)
        if path.read_text(encoding="utf-8") != payload:
            raise ValueError(f"immutable raw artifact differs on retry: {path}") from None
    except BaseException:
        Path(temp_name).unlink(missing_ok=True)
        raise


def _relative_path(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _first_complete_open(start_ms: int) -> int:
    return ((start_ms + KLINE_STEP_MS - 1) // KLINE_STEP_MS) * KLINE_STEP_MS


def _missing_ranges(
    existing: Iterable[Kline], *, start_ms: int, end_ms: int
) -> list[tuple[int, int]]:
    """Return contiguous missing 1m-open ranges, including a missing prefix."""

    first = _first_complete_open(start_ms)
    last = last_complete_open_time(end_ms, "1m")
    if last is None or first > last:
        return []
    existing_times = sorted(
        {row.open_time_ms for row in existing if first <= row.open_time_ms <= last}
    )
    ranges: list[tuple[int, int]] = []
    cursor = first
    for timestamp in existing_times:
        if timestamp < cursor:
            continue
        if timestamp > cursor:
            ranges.append((cursor, min(timestamp - KLINE_STEP_MS, last)))
        cursor = timestamp + KLINE_STEP_MS
        if cursor > last:
            break
    if cursor <= last:
        ranges.append((cursor, last))
    return [
        (range_start, range_end) for range_start, range_end in ranges if range_start <= range_end
    ]


def git_sha(repo: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _manifest(
    path: Path,
    *,
    source: str,
    symbol: str,
    interval: str,
    start_ms: int,
    end_ms: int,
    rows: int,
    artifact: Path,
    revision: str,
    config_hash: str,
    quality_status: str,
    source_artifacts: tuple[str, ...] = (),
) -> DatasetManifest:
    value = DatasetManifest(
        schema_version=1,
        source=source,
        symbol=symbol,
        interval=interval,
        range_start_ms=start_ms,
        range_end_ms=end_ms,
        rows=rows,
        checksum_sha256=sha256_file(artifact),
        git_sha=revision,
        config_hash=config_hash,
        created_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        market="binance_usd_m_futures",
        file_size_bytes=artifact.stat().st_size,
        quality_status=quality_status,
        source_artifacts=source_artifacts,
    )
    _write_json(path, asdict(value))
    return value


def acquire_symbol(
    client: BinancePublicClient,
    *,
    root: Path,
    symbol: str,
    start_ms: int,
    end_ms: int,
    config_hash: str,
    revision: str,
) -> dict[str, Any]:
    """Acquire one bounded range and repair missing prefixes, suffixes, and gaps."""

    normalized = root / "data" / "normalized" / symbol
    raw = root / "data" / "raw" / "binance_futures" / symbol
    manifests = root / "data" / "manifests" / symbol
    kline_path = normalized / "1m.csv"
    funding_path = normalized / "funding.csv"
    existing = read_klines(kline_path)
    _unique_existing = {row.open_time_ms: row for row in existing}
    if len(_unique_existing) != len(existing):
        raise ValueError(f"duplicate persisted kline at {kline_path}")

    requested_ranges = _missing_ranges(existing, start_ms=start_ms, end_ms=end_ms)
    raw_kline_paths: list[Path] = []
    raw_kline_row_counts: dict[Path, int] = {}
    parsed: list[Kline] = []
    downloaded_raw_rows = 0
    raw_kline_ranges: dict[Path, tuple[int, int]] = {}
    for request_start, request_last_open in requested_ranges:
        request_end = request_last_open + KLINE_STEP_MS - 1
        raw_rows = client.klines(symbol, start_ms=request_start, end_ms=request_end)
        downloaded_raw_rows += len(raw_rows)
        parsed.extend(
            Kline.from_binance(symbol, "1m", row)
            for row in raw_rows
            if request_start <= int(row[0]) <= request_last_open and int(row[6]) <= end_ms
        )
        raw_path = raw / f"klines_1m_{request_start}_{request_end}.json"
        _write_immutable_json(raw_path, raw_rows)
        raw_kline_paths.append(raw_path)
        raw_kline_row_counts[raw_path] = len(raw_rows)
        raw_kline_ranges[raw_path] = (request_start, request_end)

    kline_first = _first_complete_open(start_ms)
    kline_last = last_complete_open_time(end_ms, "1m")
    effective_kline_end = kline_last if kline_last is not None else kline_first - 1
    kline_count = write_klines(
        kline_path,
        parsed,
        range_start_ms=kline_first,
        range_end_ms=effective_kline_end,
    )
    funding_rows = client.funding(symbol, start_ms=start_ms, end_ms=end_ms)
    raw_funding_path = raw / f"funding_{start_ms}_{end_ms}.json"
    _write_immutable_json(raw_funding_path, funding_rows)
    funding_count = write_funding(
        funding_path,
        (FundingRate.from_binance(row) for row in funding_rows),
        range_start_ms=start_ms,
        range_end_ms=end_ms,
    )
    acquired_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    metadata = client.exchange_info()
    selected = next(
        (item for item in metadata["symbols"] if item.get("symbol") == symbol),
        None,
    )
    if selected is None:
        raise ValueError(f"symbol absent from exchangeInfo: {symbol}")
    metadata_path = normalized / "metadata.json"
    metadata_record = {
        "metadata_kind": "current_provenance_only",
        "acquired_at": acquired_at,
        "effective_at": None,
        "eligible_for_point_in_time_research": False,
        "exchange_info": selected,
    }
    _write_json(metadata_path, metadata_record)
    raw_metadata_path = raw / f"exchange_info_acquired_{acquired_at.replace(':', '-')}.json"
    _write_immutable_json(raw_metadata_path, metadata_record)
    final = read_klines(kline_path)
    qa = validate_klines(
        final,
        expected_symbol=symbol,
        expected_interval="1m",
        expected_start_ms=start_ms,
        expected_end_ms=end_ms,
    )
    qa_path = normalized / "qa.json"
    _write_json(qa_path, qa.to_dict())
    status = "PASS" if qa.critical_count == 0 else "REJECTED"
    outputs: dict[str, int] = {"1m": kline_count}
    raw_kline_manifest_paths: list[Path] = []
    for raw_path in raw_kline_paths:
        raw_manifest_path = manifests / "raw" / f"{raw_path.stem}.manifest.json"
        _manifest(
            raw_manifest_path,
            source="binance:fapi/v1/klines:raw",
            symbol=symbol,
            interval="1m",
            start_ms=raw_kline_ranges[raw_path][0],
            end_ms=raw_kline_ranges[raw_path][1],
            rows=raw_kline_row_counts[raw_path],
            artifact=raw_path,
            revision=revision,
            config_hash=config_hash,
            quality_status=status,
        )
        raw_kline_manifest_paths.append(raw_manifest_path)
    raw_funding_manifest_path = manifests / "raw" / f"{raw_funding_path.stem}.manifest.json"
    _manifest(
        raw_funding_manifest_path,
        source="binance:fapi/v1/fundingRate:raw",
        symbol=symbol,
        interval="funding",
        start_ms=start_ms,
        end_ms=end_ms,
        rows=len(funding_rows),
        artifact=raw_funding_path,
        revision=revision,
        config_hash=config_hash,
        quality_status=status,
    )
    raw_funding_manifest_paths = [raw_funding_manifest_path]
    raw_kline_manifest_paths.extend(
        path
        for path in sorted((manifests / "raw").glob("klines_*.manifest.json"))
        if path not in raw_kline_manifest_paths
    )
    if qa.critical_count:
        _manifest(
            manifests / "1m.manifest.json",
            source="binance:fapi/v1/klines",
            symbol=symbol,
            interval="1m",
            start_ms=start_ms,
            end_ms=end_ms,
            rows=kline_count,
            artifact=kline_path,
            revision=revision,
            config_hash=config_hash,
            quality_status=status,
            source_artifacts=tuple(_relative_path(root, path) for path in raw_kline_manifest_paths),
        )
        return {
            "symbol": symbol,
            "resume_start_ms": requested_ranges[0][0]
            if requested_ranges
            else (kline_last + KLINE_STEP_MS if kline_last is not None else kline_first),
            "downloaded_1m_rows": downloaded_raw_rows,
            "rows": outputs,
            "funding_rows": funding_count,
            "qa": qa.to_dict(),
            "quality_status": status,
        }
    for interval in ("5m", "15m", "1h"):
        path = normalized / f"{interval}.csv"
        outputs[interval] = write_klines(path, resample_completed(final, interval), replace=True)
        _manifest(
            manifests / f"{interval}.manifest.json",
            source="derived:completed-window-resample",
            symbol=symbol,
            interval=interval,
            start_ms=start_ms,
            end_ms=end_ms,
            rows=outputs[interval],
            artifact=path,
            revision=revision,
            config_hash=config_hash,
            quality_status=status,
            source_artifacts=(_relative_path(root, kline_path),),
        )
    for name, interval, rows, artifact, source in (
        ("1m", "1m", kline_count, kline_path, "binance:fapi/v1/klines"),
        ("funding", "funding", funding_count, funding_path, "binance:fapi/v1/fundingRate"),
        ("metadata", "current-provenance", 1, metadata_path, "binance:fapi/v1/exchangeInfo"),
        ("qa", "point-in-time", qa.rows, qa_path, "pto:phase1-validation"),
        (
            "raw_metadata",
            "point-in-time",
            1,
            raw_metadata_path,
            "binance:fapi/v1/exchangeInfo:raw",
        ),
    ):
        manifest_name = (
            f"raw/{artifact.stem}.manifest.json"
            if name.startswith("raw_")
            else f"{name}.manifest.json"
        )
        _manifest(
            manifests / manifest_name,
            source=source,
            symbol=symbol,
            interval=interval,
            start_ms=start_ms,
            end_ms=end_ms,
            rows=rows,
            artifact=artifact,
            revision=revision,
            config_hash=config_hash,
            quality_status=status,
            source_artifacts=(
                tuple(_relative_path(root, path) for path in raw_kline_manifest_paths)
                if name == "1m"
                else tuple(_relative_path(root, path) for path in raw_funding_manifest_paths)
                if name == "funding"
                else ()
            ),
        )
    one_manifest_path = manifests / "1m.manifest.json"
    one_manifest = json.loads(one_manifest_path.read_text(encoding="utf-8"))
    one_manifest["source_artifacts"] = sorted(
        _relative_path(root, path) for path in (manifests / "raw").glob("klines_*.manifest.json")
    )
    _write_json(one_manifest_path, one_manifest)
    return {
        "symbol": symbol,
        "resume_start_ms": requested_ranges[0][0]
        if requested_ranges
        else (kline_last + KLINE_STEP_MS if kline_last is not None else kline_first),
        "downloaded_1m_rows": downloaded_raw_rows,
        "rows": outputs,
        "funding_rows": funding_count,
        "qa": qa.to_dict(),
        "quality_status": status,
    }


def _resolve_source_path(root: Path, source: str) -> Path:
    root_resolved = root.resolve()
    candidate = Path(source)
    resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError("source artifact escapes repository root") from exc
    return resolved


def _raw_artifact_for_manifest(root: Path, manifest_path: Path) -> Path:
    name = manifest_path.name.removesuffix(".manifest.json")
    if "binance_vision" in manifest_path.parts:
        return manifest_path.with_name(f"{name}.zip")
    try:
        manifests_index = manifest_path.parts.index("manifests")
        symbol = manifest_path.parts[manifests_index + 1]
    except (ValueError, IndexError) as exc:
        raise ValueError(f"cannot derive raw artifact for {manifest_path}") from exc
    return root / "data" / "raw" / "binance_futures" / symbol / name


def _validate_source_artifact(root: Path, source: str) -> None:
    source_path = _resolve_source_path(root, source)
    if not source_path.is_file():
        raise ValueError("source manifest is missing")
    if not source_path.name.endswith(".manifest.json"):
        return
    try:
        source_manifest = json.loads(source_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("source manifest is not valid JSON") from exc
    if not isinstance(source_manifest, dict):
        raise ValueError("source manifest is not an object")
    if "checksum_sha256" not in source_manifest or not (
        "file_size_bytes" in source_manifest or "bytes" in source_manifest
    ):
        raise ValueError("source manifest governance fields missing")
    artifact = _raw_artifact_for_manifest(root, source_path)
    if not artifact.is_file():
        raise ValueError(f"raw artifact is missing: {artifact.name}")
    expected_bytes = source_manifest.get("file_size_bytes", source_manifest.get("bytes"))
    if not isinstance(expected_bytes, int):
        raise ValueError("source manifest byte count is invalid")
    if expected_bytes != artifact.stat().st_size:
        raise ValueError("raw artifact byte count mismatch")
    if str(source_manifest["checksum_sha256"]) != sha256_file(artifact):
        raise ValueError("raw artifact checksum mismatch")
    if "binance_vision" in source_path.parts and (
        not source_manifest.get("member_name") or not source_manifest.get("url")
    ):
        raise ValueError("Vision raw manifest provenance is incomplete")


def validate_symbol(
    root: Path,
    symbol: str,
    *,
    expected_start_ms: int,
    expected_end_ms: int,
    minimum_history_days: int,
    expected_config_hash: str,
) -> QualityResult:
    """Validate one complete, governed symbol dataset and its raw lineage."""

    normalized = root / "data" / "normalized" / symbol
    manifests = root / "data" / "manifests" / symbol
    issues: list[QualityIssue] = []
    one_manifest_path = manifests / "1m.manifest.json"
    one_rows: list[Kline] = []
    try:
        one_manifest = json.loads(one_manifest_path.read_text(encoding="utf-8"))
        if not isinstance(one_manifest, dict):
            raise ValueError("1m manifest is not an object")
        if int(one_manifest["range_start_ms"]) != expected_start_ms:
            raise ValueError("1m manifest start does not match governed range")
        if int(one_manifest["range_end_ms"]) != expected_end_ms:
            raise ValueError("1m manifest end does not match governed range")
        if one_manifest.get("config_hash") != expected_config_hash:
            raise ValueError("1m manifest config hash mismatch")
        one_rows = read_klines(normalized / "1m.csv")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        return QualityResult(
            0, None, None, 1, 0, (QualityIssue("critical", "manifest", None, str(exc)),)
        )

    base = validate_klines(
        one_rows,
        expected_symbol=symbol,
        expected_interval="1m",
        expected_start_ms=expected_start_ms,
        expected_end_ms=expected_end_ms,
    )
    issues.extend(base.issues)
    expected_days = (expected_end_ms + 1 - expected_start_ms) // DAY_MS
    if expected_days < minimum_history_days:
        issues.append(
            QualityIssue(
                "critical",
                "insufficient_history",
                None,
                (
                    f"expected governed range has {expected_days} days, "
                    f"requires {minimum_history_days}"
                ),
            )
        )

    required = ("1m", "5m", "15m", "1h", "funding", "metadata", "qa")
    for name in required:
        suffix = "csv" if name in {"1m", "5m", "15m", "1h", "funding"} else "json"
        artifact = normalized / f"{name}.{suffix}"
        manifest_path = manifests / f"{name}.manifest.json"
        if not artifact.is_file() or not manifest_path.is_file():
            issues.append(QualityIssue("critical", "missing_artifact", None, name))
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if not isinstance(manifest, dict):
                raise ValueError("manifest is not an object")
            required_fields = {
                "market",
                "file_size_bytes",
                "quality_status",
                "checksum_sha256",
                "rows",
                "range_start_ms",
                "range_end_ms",
                "config_hash",
                "symbol",
                "interval",
                "source_artifacts",
            }
            if not required_fields <= set(manifest):
                raise ValueError("manifest governance fields missing")
            expected_intervals: tuple[str, ...] = {
                "metadata": ("current-provenance", "point-in-time"),
                "qa": ("point-in-time",),
            }.get(name, ("funding" if name == "funding" else name,))
            if (
                manifest["symbol"] != symbol
                or manifest["config_hash"] != expected_config_hash
                or manifest["interval"] not in expected_intervals
            ):
                raise ValueError("manifest symbol or config hash mismatch")
            if (
                int(manifest["range_start_ms"]) != expected_start_ms
                or int(manifest["range_end_ms"]) != expected_end_ms
            ):
                raise ValueError("manifest range does not match governed range")
            if manifest["checksum_sha256"] != sha256_file(artifact):
                raise ValueError("checksum mismatch")
            if manifest["file_size_bytes"] != artifact.stat().st_size:
                raise ValueError("file size mismatch")
            if manifest["quality_status"] != "PASS":
                raise ValueError(f"quality status is {manifest['quality_status']}")
            sources = manifest["source_artifacts"]
            if not isinstance(sources, list) or (name in {"1m", "funding"} and not sources):
                raise ValueError("source artifacts are missing")
            for source in sources:
                if not isinstance(source, str):
                    raise ValueError("source artifact path is not text")
                _validate_source_artifact(root, source)
            if name in {"1m", "5m", "15m", "1h"}:
                rows = read_klines(artifact)
                if len(rows) != int(manifest["rows"]):
                    raise ValueError("row count mismatch")
                expected = one_rows if name == "1m" else resample_completed(one_rows, name)
                if rows != expected:
                    raise ValueError("derived data mismatch")
            elif name == "funding":
                funding = read_funding(artifact)
                if not funding:
                    raise ValueError("funding dataset is empty")
                if len(funding) != int(manifest["rows"]):
                    raise ValueError("funding row count mismatch")
                previous_time: int | None = None
                for row in funding:
                    if row.symbol != symbol:
                        raise ValueError("funding symbol mismatch")
                    if not expected_start_ms <= row.funding_time_ms <= expected_end_ms:
                        raise ValueError("funding timestamp outside governed range")
                    if previous_time is not None and row.funding_time_ms <= previous_time:
                        raise ValueError("funding timestamps are not strictly increasing")
                    previous_time = row.funding_time_ms
                    if not row.funding_rate.is_finite():
                        raise ValueError("funding rate is non-finite")
                    if row.mark_price is not None and (
                        not row.mark_price.is_finite() or row.mark_price <= 0
                    ):
                        raise ValueError("funding mark price is invalid")
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            issues.append(QualityIssue("critical", "artifact_validation", None, f"{name}: {exc}"))
    critical = sum(issue.severity == "critical" for issue in issues)
    warnings = sum(issue.severity == "warning" for issue in issues)
    return QualityResult(
        len(one_rows),
        one_rows[0].open_time_ms if one_rows else None,
        one_rows[-1].open_time_ms if one_rows else None,
        critical,
        warnings,
        tuple(issues),
    )


def acquire_symbol_vision(
    client: BinanceVisionClient,
    *,
    root: Path,
    symbol: str,
    months: list[str],
    start_ms: int,
    end_ms: int,
    config_hash: str,
    revision: str,
) -> dict[str, Any]:
    """Acquire a bounded range from checksum-verified Binance Vision archives."""

    normalized = root / "data" / "normalized" / symbol
    raw = root / "data" / "raw" / "binance_vision" / symbol
    manifests = root / "data" / "manifests" / symbol
    kline_archives = [client.klines(symbol, month, directory=raw) for month in months]
    funding_archives = [client.funding(symbol, month, directory=raw) for month in months]

    kline_records = [
        record
        for archive in kline_archives
        for record in parse_vision_klines(archive, symbol=symbol, start_ms=start_ms, end_ms=end_ms)
    ]
    funding_records = [
        record
        for archive in funding_archives
        for record in parse_vision_funding(archive, symbol=symbol, start_ms=start_ms, end_ms=end_ms)
    ]
    kline_path = normalized / "1m.csv"
    funding_path = normalized / "funding.csv"
    kline_last = last_complete_open_time(end_ms, "1m")
    effective_kline_end = kline_last if kline_last is not None else start_ms - 1
    kline_count = write_klines(
        kline_path,
        kline_records,
        range_start_ms=start_ms,
        range_end_ms=effective_kline_end,
        replace=True,
    )
    funding_count = write_funding(
        funding_path,
        funding_records,
        range_start_ms=start_ms,
        range_end_ms=end_ms,
        replace=True,
    )

    metadata = {
        "symbol": symbol,
        "market_type": "usd_m_futures",
        "interval": "1m",
        "transport": "binance_vision_monthly_archive",
        "archive_months": months,
        "range_start_ms": start_ms,
        "range_end_ms": end_ms,
    }
    metadata_path = normalized / "metadata.json"
    _write_json(metadata_path, metadata)
    final = read_klines(kline_path)
    qa = validate_klines(
        final,
        expected_symbol=symbol,
        expected_interval="1m",
        expected_start_ms=start_ms,
        expected_end_ms=end_ms,
    )
    qa_path = normalized / "qa.json"
    _write_json(qa_path, qa.to_dict())

    status = "PASS" if qa.critical_count == 0 else "REJECTED"
    outputs: dict[str, int] = {"1m": kline_count}
    kline_raw_sources = tuple(
        _relative_path(root, raw / f"{archive.kind}_{archive.month}.manifest.json")
        for archive in kline_archives
    )
    funding_raw_sources = tuple(
        _relative_path(root, raw / f"{archive.kind}_{archive.month}.manifest.json")
        for archive in funding_archives
    )
    if qa.critical_count:
        _manifest(
            manifests / "1m.manifest.json",
            source="binance-vision:monthly/klines",
            symbol=symbol,
            interval="1m",
            start_ms=start_ms,
            end_ms=end_ms,
            rows=kline_count,
            artifact=kline_path,
            revision=revision,
            config_hash=config_hash,
            quality_status=status,
            source_artifacts=kline_raw_sources,
        )
        return {
            "symbol": symbol,
            "transport": "binance_vision",
            "months": months,
            "downloaded_1m_rows": len(kline_records),
            "rows": outputs,
            "funding_rows": funding_count,
            "qa": qa.to_dict(),
            "quality_status": status,
        }
    for interval in ("5m", "15m", "1h"):
        path = normalized / f"{interval}.csv"
        outputs[interval] = write_klines(path, resample_completed(final, interval), replace=True)
        _manifest(
            manifests / f"{interval}.manifest.json",
            source="derived:completed-window-resample",
            symbol=symbol,
            interval=interval,
            start_ms=start_ms,
            end_ms=end_ms,
            rows=outputs[interval],
            artifact=path,
            revision=revision,
            config_hash=config_hash,
            quality_status=status,
            source_artifacts=(_relative_path(root, kline_path),),
        )
    for name, interval, rows, artifact, source in (
        ("1m", "1m", kline_count, kline_path, "binance-vision:monthly/klines"),
        (
            "funding",
            "funding",
            funding_count,
            funding_path,
            "binance-vision:monthly/fundingRate",
        ),
        ("metadata", "point-in-time", 1, metadata_path, "pto:archive-provenance"),
        ("qa", "point-in-time", qa.rows, qa_path, "pto:phase1-validation"),
    ):
        _manifest(
            manifests / f"{name}.manifest.json",
            source=source,
            symbol=symbol,
            interval=interval,
            start_ms=start_ms,
            end_ms=end_ms,
            rows=rows,
            artifact=artifact,
            revision=revision,
            config_hash=config_hash,
            quality_status=status,
            source_artifacts=(
                kline_raw_sources
                if name == "1m"
                else funding_raw_sources
                if name == "funding"
                else ()
            ),
        )
    return {
        "symbol": symbol,
        "transport": "binance_vision",
        "months": months,
        "downloaded_1m_rows": len(kline_records),
        "rows": outputs,
        "funding_rows": funding_count,
        "qa": qa.to_dict(),
        "quality_status": status,
    }
