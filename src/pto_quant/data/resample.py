"""Conservative completed-window OHLCV resampling."""

from __future__ import annotations

from pto_quant.data.models import Kline
from pto_quant.data.qa import INTERVAL_MS


def resample_completed(records: list[Kline], target_interval: str) -> list[Kline]:
    """Aggregate 1m records, excluding partial or non-contiguous target windows."""

    target_ms = INTERVAL_MS[target_interval]
    expected = target_ms // INTERVAL_MS["1m"]
    groups: dict[int, list[Kline]] = {}
    for row in records:
        bucket = row.open_time_ms - (row.open_time_ms % target_ms)
        groups.setdefault(bucket, []).append(row)
    result: list[Kline] = []
    for bucket, group in sorted(groups.items()):
        group.sort()
        times = [row.open_time_ms for row in group]
        expected_times = [bucket + index * 60_000 for index in range(expected)]
        if times != expected_times:
            continue
        first, last = group[0], group[-1]
        result.append(
            Kline(
                open_time_ms=bucket,
                close_time_ms=bucket + target_ms - 1,
                symbol=first.symbol,
                interval=target_interval,
                open=first.open,
                high=max(row.high for row in group),
                low=min(row.low for row in group),
                close=last.close,
                volume=sum((row.volume for row in group), start=first.volume * 0),
                quote_volume=sum((row.quote_volume for row in group), start=first.quote_volume * 0),
                trades=sum(row.trades for row in group),
            )
        )
    return result
