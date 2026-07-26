"""A fail-closed gate for sealed holdout data.

Holdout coordinates are deliberately supplied to :class:`HoldoutGuard` by the
trusted bootstrap layer and are never included in ordinary denial messages.
The public audit trail contains hashes rather than holdout paths or dates.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any


class HoldoutAccessDenied(PermissionError):
    """Raised when sealed holdout access is not explicitly authorized."""


class HoldoutManifestError(ValueError):
    """Raised when the frozen holdout manifest is absent or invalid."""


# These coordinates are part of the trusted Phase 1 bootstrap.  They are
# intentionally not read from a user-provided config directory: a normal data
# command must not be able to move its own research boundary around a sealed
# holdout by editing YAML.
TRUSTED_PHASE1_START_MS = 1_704_412_800_000  # 2024-01-05T00:00:00Z
TRUSTED_PHASE1_END_MS = 1_751_327_999_999  # 2025-06-30T23:59:59.999Z
TRUSTED_PHASE1_SYMBOLS = ("ETHUSDC", "BTCUSDC")


def trusted_phase1_guard() -> HoldoutGuard:
    """Build the default-deny guard used by ordinary Phase 1 commands."""

    return HoldoutGuard(
        trusted_research_range=(TRUSTED_PHASE1_START_MS, TRUSTED_PHASE1_END_MS),
        # The final holdout is deliberately represented as a sealed date
        # range, not as an editable CLI/config upper bound.  The exact
        # holdout bootstrap remains a later, explicit workflow.
        sealed_date_ranges=((date(2026, 1, 1), date(9999, 12, 31)),),
    )


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _utc_text(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("timestamps must be timezone-aware")
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
        "utf-8"
    )


def _digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _append_jsonl(path: Path, record: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _canonical_json(record) + b"\n"
    descriptor = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, payload)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def create_frozen_holdout_manifest(
    path: Path,
    *,
    policy_hashes: Mapping[str, str],
    data_hashes: Mapping[str, str],
    created_at: datetime | None = None,
) -> Mapping[str, Any]:
    """Atomically create the declaration required before holdout access.

    This manifest intentionally contains no holdout date range or filesystem
    location. Those coordinates remain in the sealed bootstrap configuration.
    """

    if not policy_hashes or not data_hashes:
        raise ValueError("policy_hashes and data_hashes must be non-empty")
    timestamp = created_at or _utc_now()
    body: dict[str, Any] = {
        "schema_version": 1,
        "frozen": True,
        "created_at": _utc_text(timestamp),
        "policy_hashes": dict(sorted(policy_hashes.items())),
        "data_hashes": dict(sorted(data_hashes.items())),
    }
    body["freeze_hash"] = hashlib.sha256(_canonical_json(body)).hexdigest()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o444)
    try:
        os.write(descriptor, _canonical_json(body) + b"\n")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return body


def _read_frozen_manifest(path: Path) -> Mapping[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError) as exc:
        raise HoldoutManifestError("valid frozen manifest required") from exc
    if not isinstance(raw, dict):
        raise HoldoutManifestError("valid frozen manifest required")
    supplied_hash = raw.get("freeze_hash")
    unsigned = dict(raw)
    unsigned.pop("freeze_hash", None)
    expected_hash = hashlib.sha256(_canonical_json(unsigned)).hexdigest()
    required = {
        "schema_version",
        "frozen",
        "created_at",
        "policy_hashes",
        "data_hashes",
        "freeze_hash",
    }
    if (
        set(raw) != required
        or raw.get("schema_version") != 1
        or raw.get("frozen") is not True
        or not isinstance(raw.get("policy_hashes"), dict)
        or not raw["policy_hashes"]
        or not isinstance(raw.get("data_hashes"), dict)
        or not raw["data_hashes"]
        or supplied_hash != expected_hash
    ):
        raise HoldoutManifestError("valid frozen manifest required")
    try:
        parsed = datetime.fromisoformat(str(raw["created_at"]).replace("Z", "+00:00"))
    except ValueError as exc:
        raise HoldoutManifestError("valid frozen manifest required") from exc
    if parsed.tzinfo is None:
        raise HoldoutManifestError("valid frozen manifest required")
    return raw


@dataclass(frozen=True)
class _SealedDateRange:
    start: date
    end: date

    def contains(self, value: date) -> bool:
        return self.start <= value <= self.end


class HoldoutGuard:
    """Recognize sealed coordinates and require an explicit, audited unlock."""

    def __init__(
        self,
        *,
        sealed_roots: Sequence[Path] = (),
        sealed_date_ranges: Sequence[tuple[date, date]] = (),
        trusted_research_range: tuple[int, int] | None = None,
    ) -> None:
        self._sealed_roots = tuple(path.resolve(strict=False) for path in sealed_roots)
        ranges: list[_SealedDateRange] = []
        for start, end in sealed_date_ranges:
            if end < start:
                raise ValueError("sealed date range end precedes start")
            ranges.append(_SealedDateRange(start, end))
        self._sealed_date_ranges = tuple(ranges)
        if trusted_research_range is not None:
            start_ms, end_ms = trusted_research_range
            if end_ms < start_ms:
                raise ValueError("trusted research range end precedes start")
        self._trusted_research_range = trusted_research_range

    def assert_research_interval(self, start_ms: int, end_ms: int) -> None:
        """Reject intervals outside the trusted ordinary-research window."""

        trusted = self._trusted_research_range
        if trusted is None or start_ms > end_ms:
            raise HoldoutAccessDenied("requested interval is outside the trusted research boundary")
        trusted_start_ms, trusted_end_ms = trusted
        if start_ms < trusted_start_ms or end_ms > trusted_end_ms:
            raise HoldoutAccessDenied("requested interval is outside the trusted research boundary")

    def assert_configured_research_interval(self, start_ms: int, end_ms: int) -> None:
        """Require editable governance settings to match the trusted bootstrap."""

        trusted = self._trusted_research_range
        if trusted is None or (start_ms, end_ms) != trusted:
            raise HoldoutAccessDenied("configured research boundary is not trusted")

    def is_sealed_path(self, path: Path) -> bool:
        candidate = path.resolve(strict=False)
        return any(candidate == root or root in candidate.parents for root in self._sealed_roots)

    def is_sealed_date(self, value: date) -> bool:
        return any(period.contains(value) for period in self._sealed_date_ranges)

    def assert_path_access(
        self,
        path: Path,
        *,
        allow_holdout: bool = False,
        frozen_manifest: Path | None = None,
        audit_log: Path | None = None,
        now: datetime | None = None,
    ) -> None:
        if not self.is_sealed_path(path):
            return
        self._authorize(
            subject_kind="path",
            subject_fingerprint=_digest_text(str(path.resolve(strict=False))),
            allow_holdout=allow_holdout,
            frozen_manifest=frozen_manifest,
            audit_log=audit_log,
            now=now,
        )

    def assert_date_access(
        self,
        value: date,
        *,
        allow_holdout: bool = False,
        frozen_manifest: Path | None = None,
        audit_log: Path | None = None,
        now: datetime | None = None,
    ) -> None:
        if not self.is_sealed_date(value):
            return
        self._authorize(
            subject_kind="date",
            subject_fingerprint=_digest_text(value.isoformat()),
            allow_holdout=allow_holdout,
            frozen_manifest=frozen_manifest,
            audit_log=audit_log,
            now=now,
        )

    def _authorize(
        self,
        *,
        subject_kind: str,
        subject_fingerprint: str,
        allow_holdout: bool,
        frozen_manifest: Path | None,
        audit_log: Path | None,
        now: datetime | None,
    ) -> None:
        if not allow_holdout:
            raise HoldoutAccessDenied("sealed holdout access denied")
        if frozen_manifest is None:
            raise HoldoutManifestError("valid frozen manifest required")
        manifest = _read_frozen_manifest(frozen_manifest)
        if audit_log is None:
            raise HoldoutAccessDenied("append-only holdout audit log required")
        timestamp = now or _utc_now()
        _append_jsonl(
            audit_log,
            {
                "event": "HOLDOUT_ACCESS_GRANTED",
                "created_at": _utc_text(timestamp),
                "subject_kind": subject_kind,
                "subject_sha256": subject_fingerprint,
                "freeze_hash": manifest["freeze_hash"],
            },
        )
