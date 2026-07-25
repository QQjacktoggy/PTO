"""Research-governance primitives for PTO Quant."""

from .holdout import (
    HoldoutAccessDenied,
    HoldoutGuard,
    HoldoutManifestError,
    create_frozen_holdout_manifest,
)
from .manifest import (
    ManifestExistsError,
    ManifestValidationError,
    RunManifest,
    create_run_manifest,
    sha256_file,
)
from .registry import (
    DuplicateExperimentError,
    ExperimentRecord,
    ExperimentRegistry,
    RegistryIntegrityError,
)

__all__ = [
    "DuplicateExperimentError",
    "ExperimentRecord",
    "ExperimentRegistry",
    "HoldoutAccessDenied",
    "HoldoutGuard",
    "HoldoutManifestError",
    "ManifestExistsError",
    "ManifestValidationError",
    "RegistryIntegrityError",
    "RunManifest",
    "create_frozen_holdout_manifest",
    "create_run_manifest",
    "sha256_file",
]
