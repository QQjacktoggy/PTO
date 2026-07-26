"""Binance Vision USD-M monthly archive transport."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import tempfile
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
    member_name: str


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

    def _archive(self, path: str, *, kind: str, month: str, member_name: str) -> VisionArchive:
        url = f"{self.base_url}/{path}"
        payload = self.getter(url)
        checksum_payload = self.getter(f"{url}.CHECKSUM").decode("ascii").strip()
        expected = checksum_payload.split()[0].lower()
        actual = hashlib.sha256(payload).hexdigest()
        if actual != expected:
            raise PublicDataError(
                f"checksum mismatch for {url}: expected {expected}, received {actual}"
            )
        return VisionArchive(
            kind=kind,
            month=month,
            url=url,
            payload=payload,
            checksum=actual,
            member_name=member_name,
        )

    def _cached_archive(
        self,
        *,
        path: str,
        kind: str,
        month: str,
        member_name: str,
        directory: Path | None,
    ) -> VisionArchive:
        url = f"{self.base_url}/{path}"
        target = directory / f"{kind}_{month}.zip" if directory is not None else None
        manifest = target.with_suffix(".manifest.json") if target is not None else None
        if target is not None and manifest is not None and target.is_file() and manifest.is_file():
            try:
                evidence = json.loads(manifest.read_text(encoding="utf-8"))
                payload = target.read_bytes()
                actual = hashlib.sha256(payload).hexdigest()
                if (
                    isinstance(evidence, dict)
                    and evidence.get("checksum_sha256") == actual
                    and evidence.get("url") == url
                    and evidence.get("member_name") == member_name
                    and evidence.get("kind") == kind
                    and evidence.get("month") == month
                    and evidence.get("bytes") == len(payload)
                ):
                    return VisionArchive(kind, month, url, payload, actual, member_name)
            except (OSError, TypeError, ValueError, json.JSONDecodeError):
                # A partial or malformed sidecar is recoverable evidence, not
                # a reason to make the valid archive permanently unusable.
                pass
        archive = self._archive(path, kind=kind, month=month, member_name=member_name)
        if directory is not None:
            save_immutable_archives([archive], directory)
        return archive

    def klines(self, symbol: str, month: str, *, directory: Path | None = None) -> VisionArchive:
        filename = f"{symbol}-1m-{month}.zip"
        return self._cached_archive(
            path=f"data/futures/um/monthly/klines/{symbol}/1m/{filename}",
            kind="klines",
            month=month,
            member_name=filename.removesuffix(".zip") + ".csv",
            directory=directory,
        )

    def funding(self, symbol: str, month: str, *, directory: Path | None = None) -> VisionArchive:
        filename = f"{symbol}-fundingRate-{month}.zip"
        return self._cached_archive(
            path=f"data/futures/um/monthly/fundingRate/{symbol}/{filename}",
            kind="funding",
            month=month,
            member_name=filename.removesuffix(".zip") + ".csv",
            directory=directory,
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


def _csv_rows(archive_record: VisionArchive) -> list[dict[str, str]]:
    try:
        with zipfile.ZipFile(io.BytesIO(archive_record.payload)) as archive:
            members = [name for name in archive.namelist() if name.endswith(".csv")]
            if len(members) != 1:
                raise PublicDataError(f"expected one CSV in archive, found {len(members)}")
            if Path(members[0]).name != archive_record.member_name:
                raise PublicDataError(
                    "unexpected CSV member: "
                    f"expected {archive_record.member_name}, got {members[0]}"
                )
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
    month_prefix = archive.month
    for row in _csv_rows(archive):
        opened = int(row["open_time"])
        if datetime.fromtimestamp(opened / 1000, tz=UTC).strftime("%Y-%m") != month_prefix:
            raise PublicDataError(f"kline timestamp outside archive month {archive.month}")
        close_time = int(row["close_time"])
        if start_ms <= opened and close_time <= end_ms:
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
                        close_time,
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
    for row in _csv_rows(archive):
        timestamp = int(row["calc_time"])
        if datetime.fromtimestamp(timestamp / 1000, tz=UTC).strftime("%Y-%m") != archive.month:
            raise PublicDataError(f"funding timestamp outside archive month {archive.month}")
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
        manifest_path = path.with_suffix(".manifest.json")
        evidence = {
            "schema_version": 1,
            "kind": archive.kind,
            "month": archive.month,
            "url": archive.url,
            "member_name": archive.member_name,
            "checksum_sha256": archive.checksum,
            "bytes": len(archive.payload),
        }
        existing_manifest: dict[str, object] | None = None
        if manifest_path.is_file():
            try:
                parsed = json.loads(manifest_path.read_text(encoding="utf-8"))
                if isinstance(parsed, dict):
                    existing_manifest = parsed
            except (OSError, TypeError, ValueError, json.JSONDecodeError):
                existing_manifest = None

        existing_hash = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        if existing_hash == archive.checksum and existing_manifest == evidence:
            continue
        if existing_manifest is not None and existing_manifest != evidence:
            raise ValueError(f"immutable raw artifact differs on retry: {path}")

        descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=directory)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(archive.payload)
                stream.flush()
                os.fsync(stream.fileno())
            temporary = Path(temp_name)
            if hashlib.sha256(temporary.read_bytes()).hexdigest() != archive.checksum:
                raise ValueError(f"temporary archive checksum mismatch: {path}")
            os.replace(temp_name, path)
        except BaseException:
            Path(temp_name).unlink(missing_ok=True)
            raise
        path.chmod(0o444)

        evidence["bytes"] = path.stat().st_size
        manifest_payload = json.dumps(evidence, indent=2, sort_keys=True).encode() + b"\n"
        descriptor, temp_name = tempfile.mkstemp(prefix=f".{manifest_path.name}.", dir=directory)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(manifest_payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_name, manifest_path)
        except BaseException:
            Path(temp_name).unlink(missing_ok=True)
            raise
        manifest_path.chmod(0o444)
