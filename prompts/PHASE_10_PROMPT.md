# Phase 10 Prompt — Conflict Arbitration, Risk Budget, and Leverage

You are executing **only Phase 10** of `ETHUSDC_ADAPTIVE_MULTI_LANE_V2`.

Read `AGENTS.md`, the relevant documents in `docs/`, all configuration files, and the current `STATUS.md`.

## Required work

1. Implement same-direction and opposite-direction arbitration.
2. Implement one-position constraint and NO_TRADE score-gap behavior.
3. Implement fixed notional, fixed leverage, fixed risk, and adaptive sizing.
4. Evaluate effective leverage 0.25x to 5x; 7.5x and 10x stress only.
5. Calculate calendar-day Target A/B/Stretch metrics.
6. Apply daily and drawdown risk states.

## Required tests and evidence

- Run lint, type checking, pytest, schema validation, and all Phase-specific checks.
- Generate a Phase report under `reports/phase_10/`.
- Update manifests and `STATUS.md`.
- Create a clear Git commit.
- Record blockers honestly.
- Do not start the next Phase.

## Gate

- Adaptive performance is risk-normalized.
- No loss-chasing or target-chasing leverage.
- Drawdown and daily stops work deterministically.

## Final response format

1. Phase 10 gate: `PASS`, `FAIL`, or `BLOCKED`.
2. Files created or modified.
3. Tests and exact outcomes.
4. Key metrics or evidence.
5. Known limitations.
6. Commit hash.
7. Next allowed action.

If the gate does not pass, stop and explain the blocking condition. Do not bypass the gate.
