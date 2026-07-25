# Phase 11 Prompt — Full Nested Walk-Forward Adaptive Simulation

You are executing **only Phase 11** of `ETHUSDC_ADAPTIVE_MULTI_LANE_V2`.

Read `AGENTS.md`, the relevant documents in `docs/`, all configuration files, and the current `STATUS.md`.

## Required work

1. Run the full adaptive process as historical time advances.
2. Refit only at allowed fold boundaries.
3. Freeze all test-period artifacts before evaluation.
4. Record complete decision, health, policy, and trade ledgers.
5. Report lane, policy, regime, daily target, and no-trade contributions.

## Required tests and evidence

- Run lint, type checking, pytest, schema validation, and all Phase-specific checks.
- Generate a Phase report under `reports/phase_11/`.
- Update manifests and `STATUS.md`.
- Create a clear Git commit.
- Record blockers honestly.
- Do not start the next Phase.

## Gate

- All test periods are untouched until their turn.
- Full adaptive is compared to simple baselines.
- Every decision is replayable.

## Final response format

1. Phase 11 gate: `PASS`, `FAIL`, or `BLOCKED`.
2. Files created or modified.
3. Tests and exact outcomes.
4. Key metrics or evidence.
5. Known limitations.
6. Commit hash.
7. Next allowed action.

If the gate does not pass, stop and explain the blocking condition. Do not bypass the gate.
