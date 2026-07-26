"""Typed market-data records used by acquisition, QA, and resampling."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


def utc_iso(timestamp_ms: int) -> str:
    """Convert a Unix millisecond timestamp to canonical UTC text."""

    return datetime.fromtimestamp(timestamp_ms / 1000, tz=UTC).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, order=True)
class Kline:
    open_time_ms: int
    close_time_ms: int
    symbol: str
    interval: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    quote_volume: Decimal
    trades: int

    @classmethod
    def from_binance(cls, symbol: str, interval: str, row: list[Any]) -> Kline:
        """Parse one Binance REST kline row."""

        return cls(
            open_time_ms=int(row[0]),
            close_time_ms=int(row[6]),
            symbol=symbol,
            interval=interval,
            open=Decimal(str(row[1])),
            high=Decimal(str(row[2])),
            low=Decimal(str(row[3])),
            close=Decimal(str(row[4])),
            volume=Decimal(str(row[5])),
            quote_volume=Decimal(str(row[7])),
            trades=int(row[8]),
        )

    def csv_row(self) -> list[str]:
        return [
            str(self.open_time_ms),
            utc_iso(self.open_time_ms),
            str(self.close_time_ms),
            utc_iso(self.close_time_ms),
            self.symbol,
            self.interval,
            str(self.open),
            str(self.high),
            str(self.low),
            str(self.close),
            str(self.volume),
            str(self.quote_volume),
            str(self.trades),
        ]


@dataclass(frozen=True, order=True)
class FundingRate:
    funding_time_ms: int
    symbol: str
    funding_rate: Decimal
    mark_price: Decimal | None

    @classmethod
    def from_binance(cls, row: dict[str, Any]) -> FundingRate:
        mark = row.get("markPrice")
        return cls(
            funding_time_ms=int(row["fundingTime"]),
            symbol=str(row["symbol"]),
            funding_rate=Decimal(str(row["fundingRate"])),
            mark_price=Decimal(str(mark)) if mark not in (None, "") else None,
        )

    def csv_row(self) -> list[str]:
        return [
            str(self.funding_time_ms),
            utc_iso(self.funding_time_ms),
            self.symbol,
            str(self.funding_rate),
            "" if self.mark_price is None else str(self.mark_price),
        ]


KLINE_HEADER = [
    "open_time_ms",
    "open_time_utc",
    "close_time_ms",
    "close_time_utc",
    "symbol",
    "interval",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "quote_volume",
    "trades",
]

FUNDING_HEADER = [
    "funding_time_ms",
    "funding_time_utc",
    "symbol",
    "funding_rate",
    "mark_price",
]
