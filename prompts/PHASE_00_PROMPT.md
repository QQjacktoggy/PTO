# Phase 00 Prompt — Governance, Scaffold, and Holdout Guard

You are executing **only Phase 0** of `ETHUSDC_ADAPTIVE_MULTI_LANE_V2`.

Read `AGENTS.md`, the relevant documents in `docs/`, all configuration files, and the current `STATUS.md`.

## Required work

1. Create the complete repository tree and Python project scaffold.
2. Copy or preserve all supplied governance and config files.
3. Create typed config loaders and JSON/YAML schema validation.
4. Create an experiment registry with unique IDs and immutable run manifests.
5. Implement a sealed-holdout guard that denies access by default.
6. Create CLI skeleton, Makefile, lint, typecheck, pytest, and CI-friendly fixtures.
7. Create STATUS.md from STATUS_TEMPLATE.md.
8. Do not download full market data or implement strategy logic.

## Required tests and evidence

- Run lint, type checking, pytest, schema validation, and all Phase-specific checks.
- Generate a Phase report under `reports/phase_00/`.
- Update manifests and `STATUS.md`.
- Create a clear Git commit.
- Record blockers honestly.
- Do not start the next Phase.

## Gate

- All config files validate.
- Normal commands cannot read holdout dates or files.
- Tests prove the holdout guard denies access.
- make lint, make typecheck, and make test run.
- A Phase 0 report and commit exist.

## Final response format

1. Phase 0 gate: `PASS`, `FAIL`, or `BLOCKED`.
2. Files created or modified.
3. Tests and exact outcomes.
4. Key metrics or evidence.
5. Known limitations.
6. Commit hash.
7. Next allowed action.

If the gate does not pass, stop and explain the blocking condition. Do not bypass the gate.
