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
