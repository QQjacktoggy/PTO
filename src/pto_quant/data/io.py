"""Deterministic CSV storage for normalized public market data."""

from __future__ import annotations

import csv
import os
import tempfile
from collections.abc import Iterable
from decimal import Decimal
from pathlib import Path

from pto_quant.data.models import (
    FUNDING_HEADER,
    KLINE_HEADER,
    FundingRate,
    Kline,
)


def _atomic_rows(path: Path, header: list[str], rows: Iterable[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
    try:
        with os.fdopen(descriptor, "w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(header)
            writer.writerows(rows)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    except BaseException:
        Path(temp_name).unlink(missing_ok=True)
        raise


def _unique_klines(records: Iterable[Kline]) -> dict[int, Kline]:
    unique: dict[int, Kline] = {}
    for row in records:
        previous = unique.get(row.open_time_ms)
        if previous is not None:
            kind = "identical" if previous == row else "conflicting"
            raise ValueError(f"{kind} duplicate kline at {row.open_time_ms}")
        unique[row.open_time_ms] = row
    return unique


def write_klines(
    path: Path,
    records: Iterable[Kline],
    *,
    range_start_ms: int | None = None,
    range_end_ms: int | None = None,
    replace: bool = False,
) -> int:
    """Merge by open time and atomically write sorted normalized klines."""

    incoming = _unique_klines(records)
    merged = {} if replace else _unique_klines(read_klines(path))
    for timestamp, row in incoming.items():
        previous = merged.get(timestamp)
        if previous is not None and previous != row:
            raise ValueError(f"conflicting persisted kline at {timestamp}")
        merged[timestamp] = row
    if range_start_ms is not None:
        merged = {key: row for key, row in merged.items() if key >= range_start_ms}
    if range_end_ms is not None:
        merged = {key: row for key, row in merged.items() if key <= range_end_ms}
    ordered = [merged[key] for key in sorted(merged)]
    _atomic_rows(path, KLINE_HEADER, (row.csv_row() for row in ordered))
    return len(ordered)


def read_klines(path: Path) -> list[Kline]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != KLINE_HEADER:
            raise ValueError(f"unexpected kline CSV header: {reader.fieldnames}")
        return [
            Kline(
                open_time_ms=int(row["open_time_ms"]),
                close_time_ms=int(row["close_time_ms"]),
                symbol=row["symbol"],
                interval=row["interval"],
                open=Decimal(row["open"]),
                high=Decimal(row["high"]),
                low=Decimal(row["low"]),
                close=Decimal(row["close"]),
                volume=Decimal(row["volume"]),
                quote_volume=Decimal(row["quote_volume"]),
                trades=int(row["trades"]),
            )
            for row in reader
        ]


def write_funding(path: Path, records: Iterable[FundingRate]) -> int:
    """Merge by funding timestamp and atomically write sorted funding data."""

    merged = {row.funding_time_ms: row for row in read_funding(path)}
    merged.update({row.funding_time_ms: row for row in records})
    ordered = [merged[key] for key in sorted(merged)]
    _atomic_rows(path, FUNDING_HEADER, (row.csv_row() for row in ordered))
    return len(ordered)


def read_funding(path: Path) -> list[FundingRate]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != FUNDING_HEADER:
            raise ValueError(f"unexpected funding CSV header: {reader.fieldnames}")
        return [
            FundingRate(
                funding_time_ms=int(row["funding_time_ms"]),
                symbol=row["symbol"],
                funding_rate=Decimal(row["funding_rate"]),
                mark_price=Decimal(row["mark_price"]) if row["mark_price"] else None,
            )
            for row in reader
        ]
