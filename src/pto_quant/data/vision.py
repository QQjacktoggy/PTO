"""Binance Vision USD-M monthly archive transport."""

from __future__ import annotations

import csv
import hashlib
import io
import urllib.error
import urllib.request
import zipfile
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from pto_quant.data.client import PublicDataError
from pto_quant.data.models import FundingRate, Kline

BytesGetter = Callable[[str], bytes]


def urllib_bytes_get(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "pto-quant/0.1 public-history-research"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
            return bytes(response.read())
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise FileNotFoundError(url) from exc
        raise PublicDataError(f"GET {url} failed: {exc}") from exc
    except Exception as exc:
        raise PublicDataError(f"GET {url} failed: {exc}") from exc


@dataclass(frozen=True)
class VisionArchive:
    kind: str
    month: str
    url: str
    payload: bytes
    checksum: str


class BinanceVisionClient:
    """Download and verify immutable public monthly archive files."""

    def __init__(
        self,
        base_url: str = "https://data.binance.vision",
        *,
        getter: BytesGetter | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.getter = getter or urllib_bytes_get

    def _archive(self, path: str, *, kind: str, month: str) -> VisionArchive:
        url = f"{self.base_url}/{path}"
        payload = self.getter(url)
        checksum_payload = self.getter(f"{url}.CHECKSUM").decode("ascii").strip()
        expected = checksum_payload.split()[0].lower()
        actual = hashlib.sha256(payload).hexdigest()
        if actual != expected:
            raise PublicDataError(
                f"checksum mismatch for {url}: expected {expected}, received {actual}"
            )
        return VisionArchive(kind=kind, month=month, url=url, payload=payload, checksum=actual)

    def klines(self, symbol: str, month: str) -> VisionArchive:
        filename = f"{symbol}-1m-{month}.zip"
        return self._archive(
            f"data/futures/um/monthly/klines/{symbol}/1m/{filename}",
            kind="klines",
            month=month,
        )

    def funding(self, symbol: str, month: str) -> VisionArchive:
        filename = f"{symbol}-fundingRate-{month}.zip"
        return self._archive(
            f"data/futures/um/monthly/fundingRate/{symbol}/{filename}",
            kind="funding",
            month=month,
        )


def months_between(start_ms: int, end_ms: int) -> list[str]:
    start = datetime.fromtimestamp(start_ms / 1000, tz=UTC)
    end = datetime.fromtimestamp(end_ms / 1000, tz=UTC)
    year, month = start.year, start.month
    values: list[str] = []
    while (year, month) <= (end.year, end.month):
        values.append(f"{year:04d}-{month:02d}")
        month += 1
        if month == 13:
            year += 1
            month = 1
    return values


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            members = [name for name in archive.namelist() if name.endswith(".csv")]
            if len(members) != 1:
                raise PublicDataError(f"expected one CSV in archive, found {len(members)}")
            with archive.open(members[0]) as raw:
                stream = io.TextIOWrapper(raw, encoding="utf-8", newline="")
                return list(csv.DictReader(stream))
    except zipfile.BadZipFile as exc:
        raise PublicDataError("invalid Binance Vision ZIP archive") from exc


def parse_vision_klines(
    archive: VisionArchive,
    *,
    symbol: str,
    start_ms: int,
    end_ms: int,
) -> list[Kline]:
    records: list[Kline] = []
    for row in _csv_rows(archive.payload):
        opened = int(row["open_time"])
        if start_ms <= opened <= end_ms:
            records.append(
                Kline.from_binance(
                    symbol,
                    "1m",
                    [
                        opened,
                        row["open"],
                        row["high"],
                        row["low"],
                        row["close"],
                        row["volume"],
                        int(row["close_time"]),
                        row["quote_volume"],
                        int(row["count"]),
                    ],
                )
            )
    return records


def parse_vision_funding(
    archive: VisionArchive,
    *,
    symbol: str,
    start_ms: int,
    end_ms: int,
) -> list[FundingRate]:
    records: list[FundingRate] = []
    for row in _csv_rows(archive.payload):
        timestamp = int(row["calc_time"])
        if start_ms <= timestamp <= end_ms:
            records.append(
                FundingRate.from_binance(
                    {
                        "symbol": symbol,
                        "fundingTime": timestamp,
                        "fundingRate": row["last_funding_rate"],
                    }
                )
            )
    return records


def save_immutable_archives(archives: Iterable[VisionArchive], directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for archive in archives:
        path = directory / f"{archive.kind}_{archive.month}.zip"
        if path.exists():
            if hashlib.sha256(path.read_bytes()).hexdigest() != archive.checksum:
                raise ValueError(f"immutable raw artifact differs on retry: {path}")
            continue
        path.write_bytes(archive.payload)
        path.chmod(0o444)
