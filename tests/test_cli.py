from __future__ import annotations

import json
from pathlib import Path

from pto_quant.cli import main

ROOT = Path(__file__).resolve().parents[1]


def test_config_validate_success(capsys: object) -> None:
    assert main(["config", "validate", "--config-dir", str(ROOT / "config")]) == 0
    output = capsys.readouterr()  # type: ignore[attr-defined]
    assert "configuration valid" in output.out


def test_config_validate_failure(tmp_path: Path, capsys: object) -> None:
    missing = tmp_path / "missing"
    assert main(["config", "validate", "--config-dir", str(missing)]) != 0
    output = capsys.readouterr()  # type: ignore[attr-defined]
    assert "configuration validation failed" in output.err


def test_project_info(capsys: object) -> None:
    assert main(["project", "info", "--config-dir", str(ROOT / "config")]) == 0
    output = capsys.readouterr()  # type: ignore[attr-defined]
    info = json.loads(output.out)
    assert info["name"] == "ETHUSDC_ADAPTIVE_MULTI_LANE_V2"
    assert info["holdout_sealed"] is True


def test_data_acquire_rejects_holdout_before_network(capsys: object) -> None:
    result = main(
        [
            "data",
            "acquire",
            "--config-dir",
            str(ROOT / "config"),
            "--start",
            "2026-01-01T00:00:00Z",
            "--end",
            "2026-01-02T00:00:00Z",
        ]
    )
    assert result == 2
    assert "outside the governed Phase 1 research boundary" in capsys.readouterr().err  # type: ignore[attr-defined]


def test_data_acquire_rejects_unknown_and_duplicate_symbols(capsys: object) -> None:
    common = [
        "data",
        "acquire",
        "--config-dir",
        str(ROOT / "config"),
        "--start",
        "2024-01-05T00:00:00Z",
        "--end",
        "2024-01-05T00:01:00Z",
    ]
    assert main([*common, "--symbol", "BTCUSDT"]) == 2
    assert "outside governed universe" in capsys.readouterr().err  # type: ignore[attr-defined]
    assert main([*common, "--symbol", "ETHUSDC", "--symbol", "ETHUSDC"]) == 2
    assert "duplicate --symbol" in capsys.readouterr().err  # type: ignore[attr-defined]
