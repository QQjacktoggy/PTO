"""Append-only experiment registry."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
from collections.abc import Iterator, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class DuplicateExperimentError(ValueError):
    """Raised when an experiment ID has already been registered."""


class RegistryIntegrityError(ValueError):
    """Raised when registry history is malformed or self-contradictory."""


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
        "utf-8"
    )


def _utc_text(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("created_at must be timezone-aware")
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _experiment_id(created_at: datetime, nonce: str, payload: Mapping[str, Any]) -> str:
    utc = created_at.astimezone(UTC)
    timestamp = utc.strftime("%Y%m%dT%H%M%S%fZ")
    digest_input = nonce.encode("ascii") + b"\0" + _canonical_json(payload)
    suffix = hashlib.sha256(digest_input).hexdigest()[:16]
    return f"exp-{timestamp}-{suffix}"


@dataclass(frozen=True)
class ExperimentRecord:
    experiment_id: str
    created_at: str
    name: str
    config_hash: str
    seed: int
    metadata: Mapping[str, Any]


class ExperimentRegistry:
    """JSONL registry in which each experiment ID may occur exactly once."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def records(self) -> Iterator[ExperimentRecord]:
        if not self.path.exists():
            return
        seen: set[str] = set()
        with self.path.open("r", encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                try:
                    raw = json.loads(line)
                    record = ExperimentRecord(**raw)
                except (json.JSONDecodeError, TypeError) as exc:
                    raise RegistryIntegrityError(
                        f"invalid registry record at line {line_number}"
                    ) from exc
                if record.experiment_id in seen:
                    raise RegistryIntegrityError("duplicate experiment ID in registry")
                seen.add(record.experiment_id)
                yield record

    def register(
        self,
        *,
        name: str,
        config_hash: str,
        seed: int,
        metadata: Mapping[str, Any] | None = None,
        experiment_id: str | None = None,
        created_at: datetime | None = None,
        nonce: str | None = None,
    ) -> ExperimentRecord:
        timestamp = created_at or datetime.now(UTC)
        created_at_text = _utc_text(timestamp)
        record_payload: dict[str, Any] = {
            "created_at": created_at_text,
            "name": name,
            "config_hash": config_hash,
            "seed": seed,
            "metadata": dict(metadata or {}),
        }
        identifier = experiment_id or _experiment_id(
            timestamp, nonce or secrets.token_hex(16), record_payload
        )
        existing = {record.experiment_id for record in self.records()}
        if identifier in existing:
            raise DuplicateExperimentError(f"experiment already registered: {identifier}")
        record = ExperimentRecord(experiment_id=identifier, **record_payload)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = _canonical_json(asdict(record)) + b"\n"
        descriptor = os.open(self.path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o644)
        try:
            os.write(descriptor, payload)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        return record

    def replace(self, _: ExperimentRecord) -> None:
        """Explicitly reject mutation to make the append-only contract obvious."""

        raise RegistryIntegrityError("experiment registry records are immutable")
