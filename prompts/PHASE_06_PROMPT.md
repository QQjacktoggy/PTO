# Phase 06 Prompt — Exit and Trade-Management Lab

You are executing **only Phase 6** of `ETHUSDC_ADAPTIVE_MULTI_LANE_V2`.

Read `AGENTS.md`, the relevant documents in `docs/`, all configuration files, and the current `STATUS.md`.

## Required work

1. Implement S0–S3, P0–P2, break-even, T0–T6, R0–R5, and time exits.
2. Evaluate modules before bounded combinations.
3. Measure trail benefit/harm and emergency-exit loss saved versus profit sacrificed.
4. Enforce no stop widening and delayed activation.
5. Retain a bounded profile set per lane.

## Required tests and evidence

- Run lint, type checking, pytest, schema validation, and all Phase-specific checks.
- Generate a Phase report under `reports/phase_06/`.
- Update manifests and `STATUS.md`.
- Create a clear Git commit.
- Record blockers honestly.
- Do not start the next Phase.

## Gate

- No full Cartesian search.
- Every exit has a reason code.
- OHLCV emergency exits are labeled minute-resolution.
- Retained policies are preregistered.

## Final response format

1. Phase 6 gate: `PASS`, `FAIL`, or `BLOCKED`.
2. Files created or modified.
3. Tests and exact outcomes.
4. Key metrics or evidence.
5. Known limitations.
6. Commit hash.
7. Next allowed action.

If the gate does not pass, stop and explain the blocking condition. Do not bypass the gate.
