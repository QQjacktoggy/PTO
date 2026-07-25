"""Fail-closed data quality checks for normalized klines."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal

from pto_quant.data.models import Kline

INTERVAL_MS = {"1m": 60_000, "5m": 300_000, "15m": 900_000, "1h": 3_600_000}


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
) -> QualityResult:
    """Validate order, completeness, symbols, UTC boundaries, and OHLCV invariants."""

    issues: list[QualityIssue] = []
    step = INTERVAL_MS[expected_interval]
    if not records:
        issues.append(QualityIssue("critical", "empty", None, "dataset contains no rows"))
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
        highest = max(row.open, row.close, row.low)
        lowest = min(row.open, row.close, row.high)
        if row.high < highest or row.low > lowest or row.high < row.low:
            issues.append(QualityIssue("critical", "ohlc", row.open_time_ms, "invalid OHLC"))
        if row.volume < Decimal(0) or row.quote_volume < Decimal(0) or row.trades < 0:
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
