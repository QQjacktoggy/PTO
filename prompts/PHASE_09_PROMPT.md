# Phase 09 Prompt — Meta Model and Adaptive Lane Health

You are executing **only Phase 9** of `ETHUSDC_ADAPTIVE_MULTI_LANE_V2`.

Read `AGENTS.md`, the relevant documents in `docs/`, all configuration files, and the current `STATUS.md`.

## Required work

1. Build point-in-time signal training table.
2. Train/calibrate logistic baseline and optional boosted challenger.
3. Implement delayed daily lane-health snapshots and shrinkage.
4. Implement ACTIVE/REDUCED/SHADOW/DISABLED/RETIRED transitions.
5. Compare static router, meta-only, health-only, and combined variants.

## Required tests and evidence

- Run lint, type checking, pytest, schema validation, and all Phase-specific checks.
- Generate a Phase report under `reports/phase_09/`.
- Update manifests and `STATUS.md`.
- Create a clear Git commit.
- Record blockers honestly.
- Do not start the next Phase.

## Gate

- Calibration is measured.
- Coverage remains meaningful.
- Health never uses future or incomplete trade outcomes.
- Complex model must justify itself.

## Final response format

1. Phase 9 gate: `PASS`, `FAIL`, or `BLOCKED`.
2. Files created or modified.
3. Tests and exact outcomes.
4. Key metrics or evidence.
5. Known limitations.
6. Commit hash.
7. Next allowed action.

If the gate does not pass, stop and explain the blocking condition. Do not bypass the gate.
