from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from pto_quant.governance.holdout import (
    HoldoutAccessDenied,
    HoldoutGuard,
    HoldoutManifestError,
    create_frozen_holdout_manifest,
)


def _guard(tmp_path: Path) -> HoldoutGuard:
    return HoldoutGuard(
        sealed_roots=[tmp_path / "sealed"],
        sealed_date_ranges=[(date(2025, 1, 1), date(2025, 6, 29))],
    )


def test_holdout_path_and_date_are_denied_by_default_without_disclosure(
    tmp_path: Path,
) -> None:
    guard = _guard(tmp_path)
    for subject in (tmp_path / "sealed" / "bars.parquet", date(2025, 3, 1)):
        with pytest.raises(HoldoutAccessDenied) as caught:
            if isinstance(subject, Path):
                guard.assert_path_access(subject)
            else:
                guard.assert_date_access(subject)
        message = str(caught.value)
        assert "2025" not in message
        assert "bars.parquet" not in message


def test_non_holdout_coordinates_are_allowed_normally(tmp_path: Path) -> None:
    guard = _guard(tmp_path)
    guard.assert_path_access(tmp_path / "research" / "bars.parquet")
    guard.assert_date_access(date(2024, 12, 31))


def test_flag_without_manifest_and_manifest_without_flag_are_denied(
    tmp_path: Path,
) -> None:
    guard = _guard(tmp_path)
    manifest = tmp_path / "freeze.json"
    create_frozen_holdout_manifest(
        manifest, policy_hashes={"policy": "abc"}, data_hashes={"data": "def"}
    )
    with pytest.raises(HoldoutManifestError):
        guard.assert_path_access(tmp_path / "sealed", allow_holdout=True)
    with pytest.raises(HoldoutAccessDenied):
        guard.assert_path_access(
            tmp_path / "sealed",
            frozen_manifest=manifest,
            audit_log=tmp_path / "audit.jsonl",
        )


def test_tampered_manifest_is_denied(tmp_path: Path) -> None:
    guard = _guard(tmp_path)
    manifest = tmp_path / "bad-freeze.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "frozen": True,
                "created_at": "2025-01-01T00:00:00Z",
                "policy_hashes": {"policy": "changed"},
                "data_hashes": {"data": "def"},
                "freeze_hash": "not-the-right-hash",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(HoldoutManifestError):
        guard.assert_path_access(
            tmp_path / "sealed",
            allow_holdout=True,
            frozen_manifest=manifest,
            audit_log=tmp_path / "audit.jsonl",
        )


def test_valid_unlock_appends_redacted_audit_record(tmp_path: Path) -> None:
    guard = _guard(tmp_path)
    manifest = tmp_path / "freeze.json"
    audit = tmp_path / "audit.jsonl"
    create_frozen_holdout_manifest(
        manifest,
        policy_hashes={"policy": "abc"},
        data_hashes={"data": "def"},
        created_at=datetime(2025, 1, 1, tzinfo=UTC),
    )
    target = tmp_path / "sealed" / "bars.parquet"
    guard.assert_path_access(
        target,
        allow_holdout=True,
        frozen_manifest=manifest,
        audit_log=audit,
        now=datetime(2025, 7, 1, tzinfo=UTC),
    )
    guard.assert_date_access(
        date(2025, 3, 1),
        allow_holdout=True,
        frozen_manifest=manifest,
        audit_log=audit,
        now=datetime(2025, 7, 1, 0, 0, 1, tzinfo=UTC),
    )
    records = [json.loads(line) for line in audit.read_text().splitlines()]
    assert len(records) == 2
    assert all(record["event"] == "HOLDOUT_ACCESS_GRANTED" for record in records)
    assert all("subject_sha256" in record for record in records)
    raw_audit = audit.read_text(encoding="utf-8")
    assert "bars.parquet" not in raw_audit
    assert "2025-03-01" not in raw_audit
