# Phase 08 Prompt — Regime System and Static Router

You are executing **only Phase 8** of `ETHUSDC_ADAPTIVE_MULTI_LANE_V2`.

Read `AGENTS.md`, the relevant documents in `docs/`, all configuration files, and the current `STATUS.md`.

## Required work

1. Build RuleBasedRegimeV1 and transition analysis.
2. Create lane × regime performance matrix.
3. Build static eligibility router and UNKNOWN/CHAOTIC behavior.
4. Optionally build a probabilistic challenger and calibration.
5. Compare to all-lanes, best-lane, equal-weight, and no-regime baselines.

## Required tests and evidence

- Run lint, type checking, pytest, schema validation, and all Phase-specific checks.
- Generate a Phase report under `reports/phase_08/`.
- Update manifests and `STATUS.md`.
- Create a clear Git commit.
- Record blockers honestly.
- Do not start the next Phase.

## Gate

- Probabilistic model replaces baseline only with OOS evidence.
- UNKNOWN and NO_TRADE are functional.
- Regime does not flicker without control.

## Final response format

1. Phase 8 gate: `PASS`, `FAIL`, or `BLOCKED`.
2. Files created or modified.
3. Tests and exact outcomes.
4. Key metrics or evidence.
5. Known limitations.
6. Commit hash.
7. Next allowed action.

If the gate does not pass, stop and explain the blocking condition. Do not bypass the gate.
