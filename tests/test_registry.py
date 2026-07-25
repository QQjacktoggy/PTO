from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from pto_quant.governance.registry import (
    DuplicateExperimentError,
    ExperimentRegistry,
    RegistryIntegrityError,
)


def test_registry_ids_are_unique_and_lexically_time_sortable(tmp_path: Path) -> None:
    registry = ExperimentRegistry(tmp_path / "experiments.jsonl")
    first = registry.register(
        name="baseline",
        config_hash="a",
        seed=7,
        created_at=datetime(2025, 1, 1, tzinfo=UTC),
        nonce="first",
    )
    second = registry.register(
        name="challenger",
        config_hash="b",
        seed=7,
        created_at=datetime(2025, 1, 2, tzinfo=UTC),
        nonce="second",
    )
    assert first.experiment_id != second.experiment_id
    assert sorted([second.experiment_id, first.experiment_id]) == [
        first.experiment_id,
        second.experiment_id,
    ]
    assert [record.experiment_id for record in registry.records()] == [
        first.experiment_id,
        second.experiment_id,
    ]


def test_explicit_id_is_deterministically_rejected_on_duplicate(
    tmp_path: Path,
) -> None:
    registry = ExperimentRegistry(tmp_path / "experiments.jsonl")
    registry.register(
        experiment_id="exp-fixed",
        name="baseline",
        config_hash="a",
        seed=7,
    )
    with pytest.raises(DuplicateExperimentError):
        registry.register(
            experiment_id="exp-fixed",
            name="modified",
            config_hash="b",
            seed=8,
        )
    assert len(list(registry.records())) == 1


def test_registry_rejects_replace_and_detects_history_tampering(
    tmp_path: Path,
) -> None:
    registry = ExperimentRegistry(tmp_path / "experiments.jsonl")
    record = registry.register(
        experiment_id="exp-fixed",
        name="baseline",
        config_hash="a",
        seed=7,
    )
    with pytest.raises(RegistryIntegrityError):
        registry.replace(record)
    with registry.path.open("a", encoding="utf-8") as stream:
        stream.write(registry.path.read_text(encoding="utf-8"))
    with pytest.raises(RegistryIntegrityError):
        list(registry.records())
