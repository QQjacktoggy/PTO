from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from pto_quant.governance.manifest import (
    ManifestExistsError,
    ManifestValidationError,
    create_run_manifest,
    sha256_file,
)


def test_run_manifest_records_reproducibility_fields_and_artifact_hashes(
    tmp_path: Path,
) -> None:
    artifact = tmp_path / "result.json"
    artifact.write_text('{"pnl": 1.25}\n', encoding="utf-8")
    path = tmp_path / "run-manifest.json"
    manifest = create_run_manifest(
        path,
        run_id="exp-1",
        config_hash="config-sha",
        package_versions={"python": "3.12", "pto-quant": "0.1.0"},
        git_sha="deadbeef",
        seed=42,
        artifacts={"result": artifact},
        created_at=datetime(2025, 1, 1, tzinfo=UTC),
    )
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["config_hash"] == "config-sha"
    assert raw["package_versions"]["python"] == "3.12"
    assert raw["git_sha"] == "deadbeef"
    assert raw["seed"] == 42
    assert raw["created_at"] == "2025-01-01T00:00:00Z"
    assert raw["artifact_hashes"] == {"result": sha256_file(artifact)}
    assert manifest.artifact_hashes == raw["artifact_hashes"]


def test_existing_manifest_is_never_overwritten(tmp_path: Path) -> None:
    path = tmp_path / "run-manifest.json"
    create_run_manifest(
        path,
        run_id="exp-1",
        config_hash="a",
        package_versions={"python": "3.12"},
        git_sha="deadbeef",
        seed=42,
        artifact_hashes={"phase-report": "report-sha"},
    )
    before = path.read_bytes()
    with pytest.raises(ManifestExistsError):
        create_run_manifest(
            path,
            run_id="exp-2",
            config_hash="b",
            package_versions={"python": "3.12"},
            git_sha="cafebabe",
            seed=99,
            artifact_hashes={"phase-report": "new-report-sha"},
        )
    assert path.read_bytes() == before


def test_artifacts_and_precomputed_hashes_are_mutually_exclusive(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError):
        create_run_manifest(
            tmp_path / "manifest.json",
            run_id="exp",
            config_hash="a",
            package_versions={},
            git_sha="deadbeef",
            seed=1,
            artifacts={},
            artifact_hashes={},
        )


@pytest.mark.parametrize(
    "overrides",
    [
        {"run_id": ""},
        {"config_hash": ""},
        {"git_sha": ""},
        {"package_versions": {}},
        {"artifact_hashes": {}},
    ],
)
def test_missing_reproducibility_evidence_is_rejected(
    tmp_path: Path, overrides: dict[str, object]
) -> None:
    kwargs: dict[str, object] = {
        "run_id": "exp",
        "config_hash": "config-sha",
        "package_versions": {"python": "3.12"},
        "git_sha": "deadbeef",
        "seed": 1,
        "artifact_hashes": {"report": "report-sha"},
    }
    kwargs.update(overrides)
    with pytest.raises(ManifestValidationError):
        create_run_manifest(tmp_path / "manifest.json", **kwargs)  # type: ignore[arg-type]
