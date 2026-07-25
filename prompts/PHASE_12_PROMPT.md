# Phase 12 Prompt — Stress, Ablation, and Generalization

You are executing **only Phase 12** of `ETHUSDC_ADAPTIVE_MULTI_LANE_V2`.

Read `AGENTS.md`, the relevant documents in `docs/`, all configuration files, and the current `STATUS.md`.

## Required work

1. Run cost, fill, latency, stop, trail, emergency-exit, and parameter stress.
2. Run block bootstrap and trade-sequence Monte Carlo.
3. Run architecture ablations.
4. Run BTCUSDC generalization without post-hoc BTC tuning.
5. Remove components that fail to justify complexity.

## Required tests and evidence

- Run lint, type checking, pytest, schema validation, and all Phase-specific checks.
- Generate a Phase report under `reports/phase_12/`.
- Update manifests and `STATUS.md`.
- Create a clear Git commit.
- Record blockers honestly.
- Do not start the next Phase.

## Gate

- Moderate stress result is explicit.
- 10% fill-drop median result is explicit.
- Generalization result is explicit.
- Final frozen component set is selected.

## Final response format

1. Phase 12 gate: `PASS`, `FAIL`, or `BLOCKED`.
2. Files created or modified.
3. Tests and exact outcomes.
4. Key metrics or evidence.
5. Known limitations.
6. Commit hash.
7. Next allowed action.

If the gate does not pass, stop and explain the blocking condition. Do not bypass the gate.
