"""Unauthenticated Binance USD-M public REST client."""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import Any

JsonGetter = Callable[[str, dict[str, str | int]], Any]


class PublicDataError(RuntimeError):
    """Raised when a public-data response is unavailable or malformed."""


def urllib_json_get(base_url: str, path: str, params: dict[str, str | int]) -> Any:
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}{path}?{query}",
        headers={"User-Agent": "pto-quant/0.1 public-history-research"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
            return json.load(response)
    except Exception as exc:
        raise PublicDataError(f"GET {path} failed: {exc}") from exc


class BinancePublicClient:
    """Minimal paginated client; no credentials or private endpoints."""

    def __init__(
        self,
        base_url: str = "https://fapi.binance.com",
        *,
        getter: JsonGetter | None = None,
        pause_seconds: float = 0.05,
    ) -> None:
        self.base_url = base_url
        self.getter = getter or (lambda path, params: urllib_json_get(self.base_url, path, params))
        self.pause_seconds = pause_seconds

    def exchange_info(self) -> dict[str, Any]:
        payload = self.getter("/fapi/v1/exchangeInfo", {})
        if not isinstance(payload, dict) or not isinstance(payload.get("symbols"), list):
            raise PublicDataError("invalid exchangeInfo response")
        return payload

    def klines(
        self, symbol: str, *, start_ms: int, end_ms: int, interval: str = "1m"
    ) -> list[list[Any]]:
        rows: list[list[Any]] = []
        cursor = start_ms
        while cursor <= end_ms:
            payload = self.getter(
                "/fapi/v1/klines",
                {
                    "symbol": symbol,
                    "interval": interval,
                    "startTime": cursor,
                    "endTime": end_ms,
                    "limit": 1500,
                },
            )
            if not isinstance(payload, list):
                raise PublicDataError("invalid klines response")
            page = [row for row in payload if isinstance(row, list)]
            if not page:
                break
            rows.extend(page)
            next_cursor = int(page[-1][0]) + 60_000
            if next_cursor <= cursor:
                raise PublicDataError("kline pagination made no progress")
            cursor = next_cursor
            if len(page) < 1500:
                break
            time.sleep(self.pause_seconds)
        return rows

    def funding(self, symbol: str, *, start_ms: int, end_ms: int) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        cursor = start_ms
        while cursor <= end_ms:
            payload = self.getter(
                "/fapi/v1/fundingRate",
                {
                    "symbol": symbol,
                    "startTime": cursor,
                    "endTime": end_ms,
                    "limit": 1000,
                },
            )
            if not isinstance(payload, list):
                raise PublicDataError("invalid funding response")
            page = [row for row in payload if isinstance(row, dict)]
            if not page:
                break
            rows.extend(page)
            next_cursor = int(page[-1]["fundingTime"]) + 1
            if next_cursor <= cursor:
                raise PublicDataError("funding pagination made no progress")
            cursor = next_cursor
            if len(page) < 1000:
                break
            time.sleep(self.pause_seconds)
        return rows
