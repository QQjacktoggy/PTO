"""Fail-closed data quality checks for normalized klines."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal

from pto_quant.data.models import Kline

INTERVAL_MS = {"1m": 60_000, "5m": 300_000, "15m": 900_000, "1h": 3_600_000}


def last_complete_open_time(end_ms: int, interval: str) -> int | None:
    """Return the last candle open whose close is at or before ``end_ms``."""

    step = INTERVAL_MS[interval]
    if end_ms < step - 1:
        return None
    return ((end_ms + 1) // step - 1) * step


@dataclass(frozen=True)
class QualityIssue:
    severity: str
    code: str
    timestamp_ms: int | None
    detail: str


@dataclass(frozen=True)
class QualityResult:
    rows: int
    first_open_time_ms: int | None
    last_open_time_ms: int | None
    critical_count: int
    warning_count: int
    issues: tuple[QualityIssue, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def validate_klines(
    records: list[Kline],
    *,
    expected_symbol: str,
    expected_interval: str,
    expected_start_ms: int | None = None,
    expected_end_ms: int | None = None,
) -> QualityResult:
    """Validate order, completeness, symbols, UTC boundaries, and OHLCV invariants."""

    issues: list[QualityIssue] = []
    step = INTERVAL_MS[expected_interval]
    if not records:
        issues.append(QualityIssue("critical", "empty", None, "dataset contains no rows"))
    else:
        if expected_start_ms is not None and records[0].open_time_ms != expected_start_ms:
            issues.append(
                QualityIssue(
                    "critical",
                    "range_start",
                    records[0].open_time_ms,
                    f"expected {expected_start_ms}, got {records[0].open_time_ms}",
                )
            )
        if expected_end_ms is not None:
            expected_last = last_complete_open_time(expected_end_ms, expected_interval)
            actual_last = records[-1].open_time_ms
            if expected_last is None or actual_last != expected_last:
                issues.append(
                    QualityIssue(
                        "critical",
                        "range_end",
                        actual_last,
                        f"expected {expected_last}, got {actual_last}",
                    )
                )
    seen: set[int] = set()
    previous: Kline | None = None
    for row in records:
        if row.open_time_ms in seen:
            issues.append(QualityIssue("critical", "duplicate", row.open_time_ms, "duplicate open"))
        seen.add(row.open_time_ms)
        if row.symbol != expected_symbol:
            issues.append(QualityIssue("critical", "symbol", row.open_time_ms, row.symbol))
        if row.interval != expected_interval:
            issues.append(QualityIssue("critical", "interval", row.open_time_ms, row.interval))
        if row.open_time_ms % step:
            issues.append(QualityIssue("critical", "boundary", row.open_time_ms, "not UTC-aligned"))
        expected_close = row.open_time_ms + step - 1
        if row.close_time_ms != expected_close:
            issues.append(
                QualityIssue(
                    "critical",
                    "close_time",
                    row.open_time_ms,
                    f"expected {expected_close}, got {row.close_time_ms}",
                )
            )
        decimals = (
            row.open,
            row.high,
            row.low,
            row.close,
            row.volume,
            row.quote_volume,
        )
        all_finite = all(value.is_finite() for value in decimals)
        if not all_finite:
            issues.append(
                QualityIssue("critical", "non_finite", row.open_time_ms, "non-finite OHLCV")
            )
        prices = (row.open, row.high, row.low, row.close)
        finite_prices = tuple(value for value in prices if value.is_finite())
        if any(value <= 0 for value in finite_prices):
            issues.append(QualityIssue("critical", "price", row.open_time_ms, "non-positive price"))
        if all_finite:
            highest = max(row.open, row.close, row.low)
            lowest = min(row.open, row.close, row.high)
            if row.high < highest or row.low > lowest or row.high < row.low:
                issues.append(QualityIssue("critical", "ohlc", row.open_time_ms, "invalid OHLC"))
        finite_volumes = (row.volume, row.quote_volume)
        if (
            any(value.is_finite() and value < Decimal(0) for value in finite_volumes)
            or row.trades < 0
        ):
            issues.append(QualityIssue("critical", "volume", row.open_time_ms, "negative value"))
        if previous is not None:
            delta = row.open_time_ms - previous.open_time_ms
            if delta <= 0:
                issues.append(
                    QualityIssue("critical", "ordering", row.open_time_ms, f"delta={delta}")
                )
            elif delta != step:
                missing = delta // step - 1
                issues.append(
                    QualityIssue(
                        "critical",
                        "gap",
                        previous.open_time_ms,
                        f"{missing} missing interval(s)",
                    )
                )
        previous = row
    critical = sum(issue.severity == "critical" for issue in issues)
    warnings = sum(issue.severity == "warning" for issue in issues)
    return QualityResult(
        rows=len(records),
        first_open_time_ms=records[0].open_time_ms if records else None,
        last_open_time_ms=records[-1].open_time_ms if records else None,
        critical_count=critical,
        warning_count=warnings,
        issues=tuple(issues),
    )
