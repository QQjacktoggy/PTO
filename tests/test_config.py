from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from pto_quant.config import ConfigValidationError, config_bundle_hash, load_config

try:
    from yaml import CSafeLoader as FastSafeLoader
except ImportError:
    from yaml import SafeLoader as FastSafeLoader

ROOT = Path(__file__).resolve().parents[1]


def copy_config(tmp_path: Path) -> Path:
    target = tmp_path / "project"
    shutil.copytree(ROOT / "config", target / "config")
    shutil.copytree(ROOT / "schemas", target / "schemas")
    return target / "config"


def mutate_yaml(path: Path, mutation: object) -> None:
    data = yaml.load(path.read_text(encoding="utf-8"), Loader=FastSafeLoader)
    mutation(data)  # type: ignore[operator]
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def test_loads_supplied_configuration() -> None:
    bundle = load_config(ROOT / "config")

    assert bundle.project.name == "ETHUSDC_ADAPTIVE_MULTI_LANE_V2"
    assert bundle.project.primary_symbol == "ETHUSDC"
    assert bundle.project.holdout_sealed is True
    assert bundle.scope.live_enabled is False
    assert bundle.project.config_hash == config_bundle_hash(ROOT / "config")
    assert len(bundle.project.config_hash) == 64


def test_config_hash_changes_when_governed_input_changes(tmp_path: Path) -> None:
    config_dir = copy_config(tmp_path)
    before = config_bundle_hash(config_dir)
    mutate_yaml(
        config_dir / "research.yaml",
        lambda data: data["project"].__setitem__("version", "2.0.1"),
    )

    assert config_bundle_hash(config_dir) != before


@pytest.mark.parametrize(
    ("field", "unsafe_value"),
    [
        ("historical_only", False),
        ("testnet_enabled", True),
        ("live_enabled", True),
        ("api_key_required", True),
        ("dca_enabled", True),
        ("recovery_enabled", True),
        ("martingale_enabled", True),
    ],
)
def test_rejects_unsafe_research_scope(tmp_path: Path, field: str, unsafe_value: bool) -> None:
    config_dir = copy_config(tmp_path)
    mutate_yaml(
        config_dir / "research.yaml",
        lambda data: data["scope"].__setitem__(field, unsafe_value),
    )

    with pytest.raises(ConfigValidationError, match=field):
        load_config(config_dir)


def test_rejects_unsealed_holdout(tmp_path: Path) -> None:
    config_dir = copy_config(tmp_path)
    mutate_yaml(
        config_dir / "research.yaml",
        lambda data: data["governance"].__setitem__("final_holdout_sealed", False),
    )

    with pytest.raises(ConfigValidationError, match="final_holdout_sealed"):
        load_config(config_dir)


def test_rejects_unknown_lane_profile_reference(tmp_path: Path) -> None:
    config_dir = copy_config(tmp_path)
    mutate_yaml(
        config_dir / "lanes.yaml",
        lambda data: data["lanes"]["L1_TREND_PULLBACK"]["entry_candidates"].append(
            "E_DOES_NOT_EXIST"
        ),
    )

    with pytest.raises(ConfigValidationError, match="E_DOES_NOT_EXIST"):
        load_config(config_dir)


def test_rejects_unknown_router_lane(tmp_path: Path) -> None:
    config_dir = copy_config(tmp_path)
    mutate_yaml(
        config_dir / "regimes.yaml",
        lambda data: data["static_router"]["RANGE"]["allow"].append("L_DOES_NOT_EXIST"),
    )

    with pytest.raises(ConfigValidationError, match="L_DOES_NOT_EXIST"):
        load_config(config_dir)


def test_rejects_acceptance_label_schema_drift(tmp_path: Path) -> None:
    config_dir = copy_config(tmp_path)
    mutate_yaml(
        config_dir / "acceptance.yaml",
        lambda data: data["labels"].__setitem__("new_label", "UNDECLARED_RESULT"),
    )

    with pytest.raises(ConfigValidationError, match="decision schema enum differ"):
        load_config(config_dir)
