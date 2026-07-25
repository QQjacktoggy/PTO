# Phase 05 Prompt — Entry Policy Lab

You are executing **only Phase 5** of `ETHUSDC_ADAPTIVE_MULTI_LANE_V2`.

Read `AGENTS.md`, the relevant documents in `docs/`, all configuration files, and the current `STATUS.md`.

## Required work

1. Implement E0 through E5.
2. Measure fill rate, missed winners, adverse selection, MFE/MAE, and net expectancy.
3. Evaluate profiles by lane and regime using OOS methods.
4. Retain at most two entry profiles per lane.

## Required tests and evidence

- Run lint, type checking, pytest, schema validation, and all Phase-specific checks.
- Generate a Phase report under `reports/phase_05/`.
- Update manifests and `STATUS.md`.
- Create a clear Git commit.
- Record blockers honestly.
- Do not start the next Phase.

## Gate

- Conservative fill is primary.
- Entry improvements survive costs and are not only lower coverage.
- Retained profile registry is frozen for later phases.

## Final response format

1. Phase 5 gate: `PASS`, `FAIL`, or `BLOCKED`.
2. Files created or modified.
3. Tests and exact outcomes.
4. Key metrics or evidence.
5. Known limitations.
6. Commit hash.
7. Next allowed action.

If the gate does not pass, stop and explain the blocking condition. Do not bypass the gate.
