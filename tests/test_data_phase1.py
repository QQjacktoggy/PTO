from __future__ import annotations

import hashlib
import io
import json
import subprocess
import zipfile
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from pto_quant.data.client import BinancePublicClient, PublicDataError
from pto_quant.data.io import read_klines, write_klines
from pto_quant.data.models import Kline
from pto_quant.data.pipeline import acquire_symbol
from pto_quant.data.qa import validate_klines
from pto_quant.data.resample import resample_completed
from pto_quant.data.vision import (
    BinanceVisionClient,
    VisionArchive,
    months_between,
    parse_vision_funding,
    parse_vision_klines,
    save_immutable_archives,
)


def _minute(index: int, *, symbol: str = "ETHUSDC") -> list[Any]:
    opened = index * 60_000
    price = Decimal("100") + index
    return [
        opened,
        str(price),
        str(price + 2),
        str(price - 1),
        str(price + 1),
        "2",
        opened + 59_999,
        "202",
        3,
        "1",
        "101",
        "0",
    ]


def _records(count: int) -> list[Kline]:
    return [Kline.from_binance("ETHUSDC", "1m", _minute(index)) for index in range(count)]


def test_normalized_write_is_sorted_deduplicated_and_idempotent(tmp_path: Path) -> None:
    target = tmp_path / "klines.csv"
    assert write_klines(target, [_records(3)[2], _records(3)[0]]) == 2
    assert write_klines(target, [_records(3)[1], _records(3)[2]]) == 3
    rows = read_klines(target)
    assert [row.open_time_ms for row in rows] == [0, 60_000, 120_000]


def test_qa_fails_closed_on_gap_duplicate_symbol_and_ohlc() -> None:
    rows = _records(3)
    bad = Kline(
        **{
            **rows[2].__dict__,
            "open_time_ms": 180_000,
            "close_time_ms": 239_999,
            "symbol": "BTCUSDC",
            "high": Decimal("1"),
        }
    )
    result = validate_klines(
        [rows[0], rows[0], bad],
        expected_symbol="ETHUSDC",
        expected_interval="1m",
    )
    codes = {issue.code for issue in result.issues}
    assert {"duplicate", "ordering", "gap", "symbol", "ohlc"} <= codes
    assert result.critical_count >= 5


def test_qa_fails_closed_on_empty_dataset() -> None:
    result = validate_klines([], expected_symbol="ETHUSDC", expected_interval="1m")
    assert result.critical_count == 1
    assert result.issues[0].code == "empty"


def test_qa_checks_requested_edges_and_invalid_decimals() -> None:
    rows = _records(3)
    partial = validate_klines(
        rows[1:],
        expected_symbol="ETHUSDC",
        expected_interval="1m",
        expected_start_ms=0,
        expected_end_ms=179_999,
    )
    assert {issue.code for issue in partial.issues} == {"range_start"}
    bad = Kline(
        **{
            **rows[0].__dict__,
            "open": Decimal("-1"),
            "high": Decimal("Infinity"),
        }
    )
    numeric = validate_klines([bad], expected_symbol="ETHUSDC", expected_interval="1m")
    assert {"non_finite", "price"} <= {issue.code for issue in numeric.issues}


def test_resample_uses_only_complete_contiguous_windows() -> None:
    complete = _records(16)
    output = resample_completed(complete, "5m")
    assert len(output) == 3
    assert output[0].open == Decimal("100")
    assert output[0].close == Decimal("105")
    assert output[0].high == Decimal("106")
    assert output[0].low == Decimal("99")
    assert output[0].volume == Decimal("10")
    assert output[0].trades == 15


def test_client_paginates_without_credentials() -> None:
    calls: list[dict[str, str | int]] = []

    def getter(path: str, params: dict[str, str | int]) -> Any:
        calls.append(params)
        start = int(params["startTime"])
        if path.endswith("klines") and start == 0:
            return [_minute(index) for index in range(1500)]
        if path.endswith("klines"):
            return [_minute(1500)]
        raise AssertionError(path)

    client = BinancePublicClient(getter=getter, pause_seconds=0)
    rows = client.klines("ETHUSDC", start_ms=0, end_ms=100_000_000)
    assert len(rows) == 1501
    assert calls[1]["startTime"] == 90_000_000


def _zip_csv(name: str, content: str) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr(name, content)
    return stream.getvalue()


def test_vision_archive_checksum_parsing_and_month_range() -> None:
    kline_csv = (
        "open_time,open,high,low,close,volume,close_time,quote_volume,count,"
        "taker_buy_volume,taker_buy_quote_volume,ignore\n"
        "0,100,102,99,101,2,59999,202,3,1,101,0\n"
    )
    funding_csv = "calc_time,funding_interval_hours,last_funding_rate\n0,8,0.0001\n"
    payloads = {
        "klines": _zip_csv("ETHUSDC-1m-1970-01.csv", kline_csv),
        "fundingRate": _zip_csv("ETHUSDC-fundingRate-1970-01.csv", funding_csv),
    }

    def getter(url: str) -> bytes:
        kind = "fundingRate" if "fundingRate" in url else "klines"
        payload = payloads[kind]
        if url.endswith(".CHECKSUM"):
            return f"{hashlib.sha256(payload).hexdigest()}  fixture.zip\n".encode()
        return payload

    client = BinanceVisionClient(getter=getter)
    kline_archive = client.klines("ETHUSDC", "1970-01")
    funding_archive = client.funding("ETHUSDC", "1970-01")
    assert parse_vision_klines(
        kline_archive, symbol="ETHUSDC", start_ms=0, end_ms=59_999
    ) == _records(1)
    funding = parse_vision_funding(funding_archive, symbol="ETHUSDC", start_ms=0, end_ms=59_999)
    assert funding[0].funding_rate == Decimal("0.0001")
    assert funding[0].mark_price is None
    assert months_between(0, 2_678_400_000) == ["1970-01", "1970-02"]


def test_vision_rejects_wrong_member_and_out_of_month_timestamp() -> None:
    wrong = VisionArchive(
        "klines",
        "1970-01",
        "fixture",
        _zip_csv(
            "BTCUSDC-1m-1970-01.csv",
            "open_time,open,high,low,close,volume,close_time,quote_volume,count\n"
            "0,1,1,1,1,1,59999,1,1\n",
        ),
        "unused",
        "ETHUSDC-1m-1970-01.csv",
    )
    with pytest.raises(PublicDataError, match="unexpected CSV member"):
        parse_vision_klines(wrong, symbol="ETHUSDC", start_ms=0, end_ms=59_999)
    outside = VisionArchive(
        **{
            **wrong.__dict__,
            "payload": _zip_csv(
                "ETHUSDC-1m-1970-01.csv",
                "open_time,open,high,low,close,volume,close_time,quote_volume,count\n"
                "2678400000,1,1,1,1,1,2678459999,1,1\n",
            ),
        }
    )
    with pytest.raises(PublicDataError, match="outside archive month"):
        parse_vision_klines(
            outside,
            symbol="ETHUSDC",
            start_ms=0,
            end_ms=3_000_000_000,
        )


def test_vision_archive_atomic_retry_and_manifest(tmp_path: Path) -> None:
    payload = _zip_csv("ETHUSDC-1m-1970-01.csv", "open_time\n")
    archive = VisionArchive(
        "klines",
        "1970-01",
        "fixture",
        payload,
        hashlib.sha256(payload).hexdigest(),
        "ETHUSDC-1m-1970-01.csv",
    )
    target = tmp_path / "klines_1970-01.zip"
    target.write_bytes(b"interrupted")
    save_immutable_archives([archive], tmp_path)
    assert target.read_bytes() == payload
    evidence = json.loads((tmp_path / "klines_1970-01.manifest.json").read_text())
    assert evidence["checksum_sha256"] == archive.checksum


def test_pipeline_resume_manifests_and_critical_gate(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "--allow-empty",
            "-qm",
            "init",
        ],
        cwd=tmp_path,
        check=True,
    )
    fixture = json.loads(
        (Path(__file__).parent / "fixtures" / "binance_exchange_info.json").read_text()
    )
    requests: list[tuple[str, int]] = []

    def getter(path: str, params: dict[str, str | int]) -> Any:
        if path.endswith("exchangeInfo"):
            return fixture
        start = int(params["startTime"])
        requests.append((path, start))
        if path.endswith("klines"):
            return [_minute(index) for index in range(start // 60_000, 60)]
        if path.endswith("fundingRate"):
            return [
                {
                    "symbol": "ETHUSDC",
                    "fundingTime": 0,
                    "fundingRate": "0.0001",
                    "markPrice": "100",
                }
            ]
        raise AssertionError(path)

    client = BinancePublicClient(getter=getter, pause_seconds=0)
    first = acquire_symbol(
        client,
        root=tmp_path,
        symbol="ETHUSDC",
        start_ms=0,
        end_ms=3_599_999,
        config_hash="abc",
        revision="deadbeef",
    )
    second = acquire_symbol(
        client,
        root=tmp_path,
        symbol="ETHUSDC",
        start_ms=0,
        end_ms=3_599_999,
        config_hash="abc",
        revision="deadbeef",
    )
    assert first["rows"] == {"1m": 60, "5m": 12, "15m": 4, "1h": 1}
    assert first["qa"]["critical_count"] == 0
    assert second["downloaded_1m_rows"] == 0
    assert ("/fapi/v1/klines", 3_600_000) not in requests
    manifest = json.loads((tmp_path / "data/manifests/ETHUSDC/1m.manifest.json").read_text())
    assert manifest["rows"] == 60
    assert manifest["source"] == "binance:fapi/v1/klines"
    assert manifest["git_sha"] == "deadbeef"
    assert manifest["config_hash"] == "abc"
    assert len(manifest["checksum_sha256"]) == 64
    assert manifest["market"] == "binance_usd_m_futures"
    assert manifest["quality_status"] == "PASS"
    assert manifest["file_size_bytes"] > 0


def test_write_rejects_duplicates_conflicts_and_crops_range(tmp_path: Path) -> None:
    target = tmp_path / "range.csv"
    rows = _records(4)
    with pytest.raises(ValueError, match="identical duplicate"):
        write_klines(target, [rows[0], rows[0]])
    write_klines(target, rows)
    write_klines(target, [], range_start_ms=60_000, range_end_ms=120_000)
    assert [row.open_time_ms for row in read_klines(target)] == [60_000, 120_000]
    conflict = Kline(**{**rows[1].__dict__, "close": Decimal("999")})
    with pytest.raises(ValueError, match="conflicting persisted"):
        write_klines(target, [conflict])


@pytest.mark.parametrize("target", ["5m", "15m", "1h"])
def test_resampled_output_passes_its_own_qa(target: str) -> None:
    output = resample_completed(_records(60), target)
    result = validate_klines(output, expected_symbol="ETHUSDC", expected_interval=target)
    assert result.critical_count == 0
