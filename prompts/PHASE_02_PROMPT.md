# Phase 02 Prompt — Point-in-Time Features and Replay Engine

You are executing **only Phase 2** of `ETHUSDC_ADAPTIVE_MULTI_LANE_V2`.

Read `AGENTS.md`, the relevant documents in `docs/`, all configuration files, and the current `STATUS.md`.

## Required work

1. Implement lag-safe technical and multi-timeframe features.
2. Implement signal, decision, order, fill, position-event, trade, equity, and health ledgers.
3. Implement conservative maker fill, TTL, fees, slippage, funding, and event priority.
4. Implement position state machine with monotonic risk.
5. Test entry-minute, same-minute TP/SL, break-even delay, trail delay, and emergency-exit scheduling.
6. Create deterministic replay and PnL parity tests.

## Required tests and evidence

- Run lint, type checking, pytest, schema validation, and all Phase-specific checks.
- Generate a Phase report under `reports/phase_02/`.
- Update manifests and `STATUS.md`.
- Create a clear Git commit.
- Record blockers honestly.
- Do not start the next Phase.

## Gate

- Same inputs produce deterministic outputs.
- Every trade traces to signal, decision, orders, fills, and position events.
- Equity and PnL reconcile.
- No illegal state transition or risk widening.

## Final response format

1. Phase 2 gate: `PASS`, `FAIL`, or `BLOCKED`.
2. Files created or modified.
3. Tests and exact outcomes.
4. Key metrics or evidence.
5. Known limitations.
6. Commit hash.
7. Next allowed action.

If the gate does not pass, stop and explain the blocking condition. Do not bypass the gate.
