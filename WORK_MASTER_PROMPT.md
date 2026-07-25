# Work Master Prompt — Adaptive Multi-Lane Quant System

You are the repository's quantitative research engineer, backtest engineer, and QA owner. Build the complete `ETHUSDC_ADAPTIVE_MULTI_LANE_V2` system in the current repository. Do not merely write a proposal.

Read these files first:

- `AGENTS.md`
- `ADAPTIVE_QUANT_MASTER_PLAN.md`
- `docs/00_PROJECT_CHARTER.md`
- `docs/01_ARCHITECTURE.md`
- `docs/02_DATA_EXECUTION_VALIDATION.md`
- `docs/03_LANE_LIBRARY.md`
- `docs/04_ENTRY_EXIT_TRADE_MANAGEMENT.md`
- `docs/05_REGIME_META_ADAPTIVE.md`
- `docs/06_RISK_LEVERAGE_TARGETS.md`
- `docs/07_PHASE_EXECUTION_PLAN.md`
- `docs/08_ACCEPTANCE_STRESS_HOLDOUT.md`
- `docs/09_REPORTING_AND_HANDOFF.md`
- `docs/10_DECISION_AND_LEDGER_CONTRACTS.md`
- all files under `config/`

## Mission

Build a point-in-time, reproducible, after-cost adaptive research system for ETHUSDC with BTCUSDC generalization. The final system must choose among qualified lanes, entry profiles, exit profiles, trailing policies, sudden-reversal exits, and risk budgets—or choose `NO_TRADE`.

The previous single strategy is only `L1_TREND_PULLBACK`; it is not the final system.

## Hard boundaries

- Historical public data only.
- No Testnet.
- No live trading.
- No API key.
- No order submission.
- No DCA, recovery, martingale, or loss chasing.
- Main execution is conservative 1m maker-aware replay.
- Main account basis is 200 USDC.
- Baseline maker fee 0 bps, taker fee 4 bps, slippage 1 bp.
- Daily realized net loss stop is -2 USDC.
- Final holdout is the last 180 days and must remain technically sealed until Phase 13.
- Never use incomplete higher-timeframe bars, centered pivots, future-confirmed swing labels, or test/holdout outcomes at decision time.
- Adaptive updates may use only completed, previously available information.
- Daily targets are evaluation metrics, not quotas.
- Never raise leverage because a daily target was missed.
- Stop risk may not widen after entry.
- A 1m OHLCV reversal detector is minute-resolution, not tick-accurate.
- If the final result fails, output a truthful failure label.

## Required execution style

Complete one Phase at a time. Every Phase requires:

1. implementation;
2. lint/typecheck/tests;
3. phase report;
4. manifests;
5. `STATUS.md` update;
6. clear Git commit;
7. machine-readable gate result.

Do not start the next Phase until the current gate passes or is explicitly closed as blocked.

## First task

Execute only Phase 0 using `prompts/PHASE_00_PROMPT.md`.

Do not download full market history, implement trading lanes, optimize parameters, or open the holdout during Phase 0.

At the end of Phase 0, report:

- files created or changed;
- tests and command outputs;
- holdout guard behavior;
- config/schema validation;
- blockers;
- commit hash;
- next allowed Phase.

Then stop.
