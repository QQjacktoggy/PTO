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


def write_klines(path: Path, records: Iterable[Kline]) -> int:
    """Merge by open time and atomically write sorted normalized klines."""

    merged = {row.open_time_ms: row for row in read_klines(path)}
    merged.update({row.open_time_ms: row for row in records})
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
