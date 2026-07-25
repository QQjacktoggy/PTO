"""Phase 1 public data acquisition, normalization, QA, and manifests."""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pto_quant.data.client import BinancePublicClient
from pto_quant.data.io import read_klines, write_funding, write_klines
from pto_quant.data.models import FundingRate, Kline
from pto_quant.data.qa import QualityResult, validate_klines
from pto_quant.data.resample import resample_completed
from pto_quant.data.vision import (
    BinanceVisionClient,
    parse_vision_funding,
    parse_vision_klines,
    save_immutable_archives,
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


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_immutable_json(path: Path, value: object) -> None:
    """Create raw evidence once; identical retries are accepted, changes are rejected."""

    payload = json.dumps(value, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text(encoding="utf-8") != payload:
            raise ValueError(f"immutable raw artifact differs on retry: {path}")
        return
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o444)
    try:
        os.write(descriptor, payload.encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


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
    """Acquire one bounded range. Re-running merges by timestamp without duplicates."""

    normalized = root / "data" / "normalized" / symbol
    raw = root / "data" / "raw" / "binance_futures" / symbol
    manifests = root / "data" / "manifests" / symbol
    kline_path = normalized / "1m.csv"
    funding_path = normalized / "funding.csv"
    existing = read_klines(kline_path)
    resume_start = max(start_ms, existing[-1].open_time_ms + 60_000) if existing else start_ms
    raw_rows = (
        client.klines(symbol, start_ms=resume_start, end_ms=end_ms)
        if resume_start <= end_ms
        else []
    )
    parsed = [Kline.from_binance(symbol, "1m", row) for row in raw_rows]
    raw_kline_path = raw / f"klines_1m_{resume_start}_{end_ms}.json"
    _write_immutable_json(raw_kline_path, raw_rows)
    kline_count = write_klines(kline_path, parsed)
    funding_rows = client.funding(symbol, start_ms=start_ms, end_ms=end_ms)
    raw_funding_path = raw / f"funding_{start_ms}_{end_ms}.json"
    _write_immutable_json(raw_funding_path, funding_rows)
    funding_count = write_funding(
        funding_path, (FundingRate.from_binance(row) for row in funding_rows)
    )
    metadata = client.exchange_info()
    selected = next(
        (item for item in metadata["symbols"] if item.get("symbol") == symbol),
        None,
    )
    if selected is None:
        raise ValueError(f"symbol absent from exchangeInfo: {symbol}")
    metadata_path = normalized / "metadata.json"
    _write_json(metadata_path, selected)
    raw_metadata_path = raw / f"exchange_info_{end_ms}.json"
    _write_immutable_json(raw_metadata_path, selected)
    final = read_klines(kline_path)
    qa = validate_klines(final, expected_symbol=symbol, expected_interval="1m")
    qa_path = normalized / "qa.json"
    _write_json(qa_path, qa.to_dict())
    outputs: dict[str, int] = {"1m": kline_count}
    for interval in ("5m", "15m", "1h"):
        path = normalized / f"{interval}.csv"
        outputs[interval] = write_klines(path, resample_completed(final, interval))
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
        )
    for name, interval, rows, artifact, source in (
        ("1m", "1m", kline_count, kline_path, "binance:fapi/v1/klines"),
        ("funding", "funding", funding_count, funding_path, "binance:fapi/v1/fundingRate"),
        ("metadata", "point-in-time", 1, metadata_path, "binance:fapi/v1/exchangeInfo"),
        ("qa", "point-in-time", qa.rows, qa_path, "pto:phase1-validation"),
        (
            "raw_klines",
            "1m",
            len(raw_rows),
            raw_kline_path,
            "binance:fapi/v1/klines:raw",
        ),
        (
            "raw_funding",
            "funding",
            len(funding_rows),
            raw_funding_path,
            "binance:fapi/v1/fundingRate:raw",
        ),
        (
            "raw_metadata",
            "point-in-time",
            1,
            raw_metadata_path,
            "binance:fapi/v1/exchangeInfo:raw",
        ),
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
        )
    return {
        "symbol": symbol,
        "resume_start_ms": resume_start,
        "downloaded_1m_rows": len(parsed),
        "rows": outputs,
        "funding_rows": funding_count,
        "qa": qa.to_dict(),
    }


def validate_symbol(root: Path, symbol: str) -> QualityResult:
    path = root / "data" / "normalized" / symbol / "1m.csv"
    return validate_klines(read_klines(path), expected_symbol=symbol, expected_interval="1m")


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
    kline_archives = [client.klines(symbol, month) for month in months]
    funding_archives = [client.funding(symbol, month) for month in months]
    save_immutable_archives(kline_archives + funding_archives, raw)

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
    kline_count = write_klines(kline_path, kline_records)
    funding_count = write_funding(funding_path, funding_records)

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
    qa = validate_klines(final, expected_symbol=symbol, expected_interval="1m")
    qa_path = normalized / "qa.json"
    _write_json(qa_path, qa.to_dict())

    outputs: dict[str, int] = {"1m": kline_count}
    for interval in ("5m", "15m", "1h"):
        path = normalized / f"{interval}.csv"
        outputs[interval] = write_klines(path, resample_completed(final, interval))
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
        )
    return {
        "symbol": symbol,
        "transport": "binance_vision",
        "months": months,
        "downloaded_1m_rows": len(kline_records),
        "rows": outputs,
        "funding_rows": funding_count,
        "qa": qa.to_dict(),
    }
