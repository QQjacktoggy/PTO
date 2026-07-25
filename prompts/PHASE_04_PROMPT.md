# Phase 04 Prompt — Multi-Lane Library

You are executing **only Phase 4** of `ETHUSDC_ADAPTIVE_MULTI_LANE_V2`.

Read `AGENTS.md`, the relevant documents in `docs/`, all configuration files, and the current `STATUS.md`.

## Required work

1. Implement L2_BREAKOUT_RETEST through L7_MICRO_MOMENTUM independently.
2. Create lane-specific tags, specifications, unit tests, and leakage tests.
3. Run untuned baselines with common execution and costs.
4. Mark experimental or insufficient-history lanes clearly.

## Required tests and evidence

- Run lint, type checking, pytest, schema validation, and all Phase-specific checks.
- Generate a Phase report under `reports/phase_04/`.
- Update manifests and `STATUS.md`.
- Create a clear Git commit.
- Record blockers honestly.
- Do not start the next Phase.

## Gate

- Each lane is logically independent.
- No cosmetic duplicate lanes.
- All signal timestamps are point-in-time.
- Each lane has a baseline scorecard.

## Final response format

1. Phase 4 gate: `PASS`, `FAIL`, or `BLOCKED`.
2. Files created or modified.
3. Tests and exact outcomes.
4. Key metrics or evidence.
5. Known limitations.
6. Commit hash.
7. Next allowed action.

If the gate does not pass, stop and explain the blocking condition. Do not bypass the gate.
