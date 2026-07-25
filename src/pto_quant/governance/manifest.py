"""Immutable, reproducible run manifests."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class ManifestExistsError(FileExistsError):
    """Raised when an immutable manifest path already exists."""


class ManifestValidationError(ValueError):
    """Raised when required reproducibility evidence is missing."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _utc_text(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("created_at must be timezone-aware")
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
        "utf-8"
    )


@dataclass(frozen=True)
class RunManifest:
    schema_version: int
    run_id: str
    config_hash: str
    package_versions: Mapping[str, str]
    git_sha: str
    seed: int
    created_at: str
    artifact_hashes: Mapping[str, str]


def create_run_manifest(
    path: Path,
    *,
    run_id: str,
    config_hash: str,
    package_versions: Mapping[str, str],
    git_sha: str,
    seed: int,
    artifacts: Mapping[str, Path] | None = None,
    artifact_hashes: Mapping[str, str] | None = None,
    created_at: datetime | None = None,
) -> RunManifest:
    """Create a run manifest once, using ``O_EXCL`` to prevent overwrite."""

    if artifacts is not None and artifact_hashes is not None:
        raise ValueError("provide artifacts or artifact_hashes, not both")
    required_text = {
        "run_id": run_id,
        "config_hash": config_hash,
        "git_sha": git_sha,
    }
    missing = [name for name, value in required_text.items() if not value.strip()]
    if missing:
        raise ManifestValidationError(f"required manifest values are empty: {sorted(missing)}")
    if not package_versions or any(
        not name.strip() or not version.strip() for name, version in package_versions.items()
    ):
        raise ManifestValidationError("package_versions must contain non-empty names and versions")
    hashes = (
        {name: sha256_file(item) for name, item in sorted(artifacts.items())}
        if artifacts is not None
        else dict(sorted((artifact_hashes or {}).items()))
    )
    if not hashes or any(not name.strip() or not value.strip() for name, value in hashes.items()):
        raise ManifestValidationError("artifact hashes must contain non-empty names and values")
    manifest = RunManifest(
        schema_version=1,
        run_id=run_id,
        config_hash=config_hash,
        package_versions=dict(sorted(package_versions.items())),
        git_sha=git_sha,
        seed=seed,
        created_at=_utc_text(created_at or datetime.now(UTC)),
        artifact_hashes=hashes,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _canonical_json(asdict(manifest)) + b"\n"
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o444)
    except FileExistsError as exc:
        raise ManifestExistsError(f"manifest already exists: {path}") from exc
    try:
        os.write(descriptor, payload)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return manifest
