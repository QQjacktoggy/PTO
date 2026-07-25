"""Typed loading and cross-file validation for the governed research configuration."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeAlias, cast

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

ConfigMap: TypeAlias = dict[str, Any]

CONFIG_FILES = (
    "acceptance.yaml",
    "adaptive_policy.yaml",
    "entry_exit_profiles.yaml",
    "lanes.yaml",
    "regimes.yaml",
    "research.yaml",
    "risk_targets.yaml",
)


class ConfigValidationError(ValueError):
    """Raised when one or more configuration contracts are invalid."""

    def __init__(self, errors: Iterable[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("\n".join(f"- {error}" for error in self.errors))


@dataclass(frozen=True)
class ResearchScope:
    """Safety-critical research-scope switches."""

    historical_only: bool
    testnet_enabled: bool
    live_enabled: bool
    api_key_required: bool
    dca_enabled: bool
    recovery_enabled: bool
    martingale_enabled: bool


@dataclass(frozen=True)
class MarketContract:
    """Required symbols and timeframes."""

    primary_symbol: str
    generalization_symbols: tuple[str, ...]
    timeframes: Mapping[str, str]


@dataclass(frozen=True)
class CapitalContract:
    """Minimal capital limits needed by later phases."""

    initial_equity_usdc: float
    max_open_positions: int
    max_active_entry_intents: int


@dataclass(frozen=True)
class ProjectInfo:
    """Stable project identity reported by the CLI."""

    name: str
    version: str
    primary_symbol: str
    initial_equity_usdc: float
    holdout_days: int
    holdout_sealed: bool
    config_hash: str


@dataclass(frozen=True)
class ConfigBundle:
    """All Phase 0 configuration, loaded as one validated unit."""

    config_dir: Path
    acceptance: ConfigMap
    adaptive_policy: ConfigMap
    entry_exit_profiles: ConfigMap
    lanes: ConfigMap
    regimes: ConfigMap
    research: ConfigMap
    risk_targets: ConfigMap
    scope: ResearchScope
    markets: MarketContract
    capital: CapitalContract
    project: ProjectInfo


def _mapping(value: Any, location: str, errors: list[str]) -> ConfigMap:
    if not isinstance(value, dict):
        errors.append(f"{location} must be a mapping")
        return {}
    return cast(ConfigMap, value)


def _read_yaml(path: Path) -> ConfigMap:
    try:
        data: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigValidationError([f"cannot load {path}: {exc}"]) from exc
    if not isinstance(data, dict):
        raise ConfigValidationError([f"{path} must contain a top-level mapping"])
    return cast(ConfigMap, data)


def _read_all(config_dir: Path) -> dict[str, ConfigMap]:
    missing = [name for name in CONFIG_FILES if not (config_dir / name).is_file()]
    if missing:
        raise ConfigValidationError([f"missing required config file: {name}" for name in missing])
    return {name: _read_yaml(config_dir / name) for name in CONFIG_FILES}


def config_bundle_hash(config_dir: str | Path = "config") -> str:
    """Hash the exact governed config bytes and final-decision schema."""

    directory = Path(config_dir).resolve()
    digest = hashlib.sha256()
    governed_paths = [directory / name for name in CONFIG_FILES]
    governed_paths.append(directory.parent / "schemas" / "decision.schema.json")
    for path in governed_paths:
        try:
            payload = path.read_bytes()
        except OSError as exc:
            raise ConfigValidationError([f"cannot hash governed file {path}: {exc}"]) from exc
        relative = path.relative_to(directory.parent).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def _required_string(mapping: Mapping[str, Any], key: str, location: str, errors: list[str]) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{location}.{key} must be a non-empty string")
        return ""
    return value


def _required_number(
    mapping: Mapping[str, Any], key: str, location: str, errors: list[str]
) -> float:
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        errors.append(f"{location}.{key} must be numeric")
        return 0.0
    return float(value)


def _required_int(mapping: Mapping[str, Any], key: str, location: str, errors: list[str]) -> int:
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        errors.append(f"{location}.{key} must be an integer")
        return 0
    return value


def _validate_scope(research: ConfigMap, errors: list[str]) -> ResearchScope:
    scope = _mapping(research.get("scope"), "research.scope", errors)
    required = {
        "historical_only": True,
        "testnet_enabled": False,
        "live_enabled": False,
        "api_key_required": False,
        "dca_enabled": False,
        "recovery_enabled": False,
        "martingale_enabled": False,
    }
    for key, expected in required.items():
        actual = scope.get(key)
        if not isinstance(actual, bool):
            errors.append(f"research.scope.{key} must be boolean")
        elif actual is not expected:
            errors.append(
                f"research.scope.{key} must be {str(expected).lower()} in research-only scope"
            )
    return ResearchScope(**{key: scope.get(key) is True for key in required})


def _validate_markets(research: ConfigMap, errors: list[str]) -> MarketContract:
    markets = _mapping(research.get("markets"), "research.markets", errors)
    primary = _mapping(markets.get("primary"), "research.markets.primary", errors)
    symbol = _required_string(primary, "symbol", "research.markets.primary", errors)

    generalization_raw = markets.get("generalization")
    generalization: list[str] = []
    if not isinstance(generalization_raw, list) or not generalization_raw:
        errors.append("research.markets.generalization must be a non-empty list")
    else:
        for index, item in enumerate(generalization_raw):
            item_map = _mapping(item, f"research.markets.generalization[{index}]", errors)
            item_symbol = _required_string(
                item_map, "symbol", f"research.markets.generalization[{index}]", errors
            )
            if item_symbol:
                generalization.append(item_symbol)

    timeframes = _mapping(markets.get("timeframes"), "research.markets.timeframes", errors)
    required_timeframes = ("raw_execution", "micro_support", "signal_decision", "higher_regime")
    for key in required_timeframes:
        _required_string(timeframes, key, "research.markets.timeframes", errors)
    return MarketContract(symbol, tuple(generalization), timeframes)


def _validate_capital(research: ConfigMap, errors: list[str]) -> CapitalContract:
    capital = _mapping(research.get("capital"), "research.capital", errors)
    equity = _required_number(capital, "initial_equity_usdc", "research.capital", errors)
    positions = _required_int(capital, "max_open_positions", "research.capital", errors)
    intents = _required_int(capital, "max_active_entry_intents", "research.capital", errors)
    if equity <= 0:
        errors.append("research.capital.initial_equity_usdc must be greater than zero")
    if positions <= 0:
        errors.append("research.capital.max_open_positions must be greater than zero")
    if intents <= 0:
        errors.append("research.capital.max_active_entry_intents must be greater than zero")
    return CapitalContract(equity, positions, intents)


def _validate_holdout(research: ConfigMap, errors: list[str]) -> tuple[int, bool]:
    splits = _mapping(research.get("splits"), "research.splits", errors)
    governance = _mapping(research.get("governance"), "research.governance", errors)
    days = _required_int(splits, "final_holdout_days", "research.splits", errors)
    sealed = governance.get("final_holdout_sealed")
    if days <= 0:
        errors.append("research.splits.final_holdout_days must be greater than zero")
    if sealed is not True:
        errors.append("research.governance.final_holdout_sealed must be true")
    if governance.get("require_frozen_manifest") is not True:
        errors.append("research.governance.require_frozen_manifest must be true")
    return days, sealed is True


def _id_set(mapping: ConfigMap, key: str, errors: list[str]) -> set[str]:
    values = _mapping(mapping.get(key), f"entry_exit_profiles.{key}", errors)
    return set(values)


def _validate_lane_profiles(
    lanes_config: ConfigMap, profiles: ConfigMap, errors: list[str]
) -> set[str]:
    lanes = _mapping(lanes_config.get("lanes"), "lanes.lanes", errors)
    profile_keys = {
        "entry_candidates": _id_set(profiles, "entry_profiles", errors),
        "stop_candidates": _id_set(profiles, "stop_profiles", errors),
        "profit_candidates": _id_set(profiles, "profit_profiles", errors),
        "trail_candidates": _id_set(profiles, "trail_profiles", errors),
        "emergency_candidates": _id_set(profiles, "emergency_profiles", errors),
    }
    for lane_id, lane_value in lanes.items():
        lane = _mapping(lane_value, f"lanes.lanes.{lane_id}", errors)
        if lane.get("official_no_trade_lane") is True:
            continue
        for candidate_key, known_ids in profile_keys.items():
            candidates = lane.get(candidate_key)
            if not isinstance(candidates, list) or not candidates:
                errors.append(f"lanes.lanes.{lane_id}.{candidate_key} must be a non-empty list")
                continue
            unknown = sorted(
                candidate
                for candidate in candidates
                if not isinstance(candidate, str) or candidate not in known_ids
            )
            if unknown:
                errors.append(
                    f"lanes.lanes.{lane_id}.{candidate_key} references unknown IDs: {unknown}"
                )
    return set(lanes)


def _validate_router(regimes: ConfigMap, lane_ids: set[str], errors: list[str]) -> None:
    regime_ids_raw = regimes.get("regime_ids")
    if not isinstance(regime_ids_raw, list) or not regime_ids_raw:
        errors.append("regimes.regime_ids must be a non-empty list")
        regime_ids: set[str] = set()
    else:
        regime_ids = {item for item in regime_ids_raw if isinstance(item, str)}
    router = _mapping(regimes.get("static_router"), "regimes.static_router", errors)
    missing_regimes = sorted(regime_ids - set(router))
    if missing_regimes:
        errors.append(f"regimes.static_router is missing regimes: {missing_regimes}")
    for regime_id, routing_value in router.items():
        routing = _mapping(routing_value, f"regimes.static_router.{regime_id}", errors)
        for action in ("allow", "shadow", "block"):
            routed = routing.get(action)
            if not isinstance(routed, list):
                errors.append(f"regimes.static_router.{regime_id}.{action} must be a list")
                continue
            unknown = sorted(item for item in routed if item not in lane_ids)
            if unknown:
                errors.append(
                    f"regimes.static_router.{regime_id}.{action} references unknown lane IDs: "
                    f"{unknown}"
                )


def _validate_acceptance(acceptance: ConfigMap, repository_root: Path, errors: list[str]) -> None:
    labels = _mapping(acceptance.get("labels"), "acceptance.labels", errors)
    configured_labels = set(labels.values())
    if not configured_labels or not all(isinstance(label, str) for label in configured_labels):
        errors.append("acceptance.labels values must be non-empty strings")
        return
    schema_path = repository_root / "schemas" / "decision.schema.json"
    try:
        schema: Any = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
    except (OSError, json.JSONDecodeError, SchemaError) as exc:
        errors.append(f"invalid decision schema {schema_path}: {exc}")
        return
    if not isinstance(schema, dict):
        errors.append("decision schema must be a JSON object")
        return
    properties = schema.get("properties")
    label_contract = properties.get("label") if isinstance(properties, dict) else None
    enum = label_contract.get("enum") if isinstance(label_contract, dict) else None
    if not isinstance(enum, list) or not all(isinstance(item, str) for item in enum):
        errors.append("decision schema properties.label.enum must be a string list")
    elif configured_labels != set(enum):
        missing = sorted(configured_labels - set(enum))
        extra = sorted(set(enum) - configured_labels)
        errors.append(
            "acceptance labels and decision schema enum differ "
            f"(missing_from_schema={missing}, extra_in_schema={extra})"
        )


def load_config(config_dir: str | Path = "config") -> ConfigBundle:
    """Load and validate every Phase 0 config file as one contract."""

    directory = Path(config_dir).resolve()
    documents = _read_all(directory)
    errors: list[str] = []
    research = documents["research.yaml"]
    scope = _validate_scope(research, errors)
    markets = _validate_markets(research, errors)
    capital = _validate_capital(research, errors)
    holdout_days, holdout_sealed = _validate_holdout(research, errors)
    lane_ids = _validate_lane_profiles(
        documents["lanes.yaml"], documents["entry_exit_profiles.yaml"], errors
    )
    _validate_router(documents["regimes.yaml"], lane_ids, errors)
    _validate_acceptance(documents["acceptance.yaml"], directory.parent, errors)

    project_raw = _mapping(research.get("project"), "research.project", errors)
    name = _required_string(project_raw, "name", "research.project", errors)
    version = _required_string(project_raw, "version", "research.project", errors)
    project = ProjectInfo(
        name=name,
        version=version,
        primary_symbol=markets.primary_symbol,
        initial_equity_usdc=capital.initial_equity_usdc,
        holdout_days=holdout_days,
        holdout_sealed=holdout_sealed,
        config_hash=config_bundle_hash(directory),
    )
    if errors:
        raise ConfigValidationError(errors)
    return ConfigBundle(
        config_dir=directory,
        acceptance=documents["acceptance.yaml"],
        adaptive_policy=documents["adaptive_policy.yaml"],
        entry_exit_profiles=documents["entry_exit_profiles.yaml"],
        lanes=documents["lanes.yaml"],
        regimes=documents["regimes.yaml"],
        research=research,
        risk_targets=documents["risk_targets.yaml"],
        scope=scope,
        markets=markets,
        capital=capital,
        project=project,
    )
