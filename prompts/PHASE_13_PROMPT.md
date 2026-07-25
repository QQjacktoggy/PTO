# Phase 13 Prompt — Frozen 180-Day Sealed Holdout

You are executing **only Phase 13** of `ETHUSDC_ADAPTIVE_MULTI_LANE_V2`.

Read `AGENTS.md`, the relevant documents in `docs/`, all configuration files, and the current `STATUS.md`.

## Required work

1. Create a signed/frozen manifest of data, parameters, policies, models, costs, and gates.
2. Open the final 180-day holdout exactly once through the guarded command.
3. Produce holdout ledgers and report.
4. Assign the final truth label from config.

## Required tests and evidence

- Run lint, type checking, pytest, schema validation, and all Phase-specific checks.
- Generate a Phase report under `reports/phase_13/`.
- Update manifests and `STATUS.md`.
- Create a clear Git commit.
- Record blockers honestly.
- Do not start the next Phase.

## Gate

- Holdout access is logged.
- No post-holdout retuning is presented as the same validation.
- Final label is machine-readable and truthful.

## Final response format

1. Phase 13 gate: `PASS`, `FAIL`, or `BLOCKED`.
2. Files created or modified.
3. Tests and exact outcomes.
4. Key metrics or evidence.
5. Known limitations.
6. Commit hash.
7. Next allowed action.

If the gate does not pass, stop and explain the blocking condition. Do not bypass the gate.
