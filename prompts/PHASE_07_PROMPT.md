# Phase 07 Prompt — Individual Lane Walk-Forward Qualification

You are executing **only Phase 7** of `ETHUSDC_ADAPTIVE_MULTI_LANE_V2`.

Read `AGENTS.md`, the relevant documents in `docs/`, all configuration files, and the current `STATUS.md`.

## Required work

1. Run anchored/rolling walk-forward with embargo and the final 180 days excluded.
2. Use train for fitting, validation for bounded selection, and test for frozen evaluation.
3. Produce fold-level and pooled OOS scorecards.
4. Assign lane states based on admission gates.

## Required tests and evidence

- Run lint, type checking, pytest, schema validation, and all Phase-specific checks.
- Generate a Phase report under `reports/phase_07/`.
- Update manifests and `STATUS.md`.
- Create a clear Git commit.
- Record blockers honestly.
- Do not start the next Phase.

## Gate

- Only qualified lanes can enter official routing.
- Failed lanes remain visible.
- No parameter cliff or severe concentration for admitted lanes.

## Final response format

1. Phase 7 gate: `PASS`, `FAIL`, or `BLOCKED`.
2. Files created or modified.
3. Tests and exact outcomes.
4. Key metrics or evidence.
5. Known limitations.
6. Commit hash.
7. Next allowed action.

If the gate does not pass, stop and explain the blocking condition. Do not bypass the gate.
