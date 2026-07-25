# AGENTS.md — Adaptive Multi-Lane Quant Research Rules

## Mission

Build, validate, and truthfully evaluate an `ETHUSDC` adaptive multi-lane futures research system. The system must select among prequalified lanes and trade-management policies using point-in-time information. It must be able to choose `NO_TRADE`.

## Hard scope

- Historical public data only.
- No Binance API key.
- No Testnet.
- No live trading or order submission.
- Primary market: Binance USD-M Futures `ETHUSDC`.
- Generalization market: `BTCUSDC`.
- Raw execution timeframe: 1m.
- Supporting timeframe: 5m.
- Main signal and decision timeframe: 15m.
- Higher-timeframe regime: 1h.
- Initial research equity: 200 USDC.
- Maximum one open position and one active entry intent in the primary research path.
- DCA, recovery, martingale, and loss-chasing are prohibited.
- Baseline maker fee: 0 bps.
- Baseline taker fee: 4 bps.
- Baseline taker slippage: 1 bp.
- Daily realized net loss cap: -2 USDC, reset at 00:00 UTC.
- Portfolio hard drawdown cap: -16 USDC from the applicable high-water mark or initial-equity reference defined in config.

## Meaning of adaptive

Adaptive means choosing from frozen, prequalified components based only on information available at the decision time:

- regime;
- eligible lane;
- entry profile;
- stop profile;
- profit profile;
- trailing profile;
- emergency-exit profile;
- lane health state;
- meta score;
- notional and risk budget;
- or `NO_TRADE`.

Adaptive does **not** mean unrestricted online optimization, post-hoc rule creation, reinforcement learning, or using future trade outcomes.

## Research integrity

1. Raw data is immutable.
2. Every dataset, feature table, model, policy, run, and report has a manifest and checksum.
3. No random train/test split for time series.
4. The final 180-day holdout stays sealed until all policies, parameters, models, costs, state transitions, and acceptance gates are frozen.
5. No lookahead, centered pivots, incomplete higher-timeframe candles, or future-confirmed labels at decision time.
6. Main performance comes from conservative 1m maker-aware event replay.
7. Same-minute event ambiguity uses the conservative priority documented in the execution contract.
8. Emergency reversal exits using OHLCV may act only after a completed decision candle and at the next executable point; do not claim tick-level reaction.
9. A stop may stay unchanged or tighten after entry; it may never widen.
10. Once break-even or trailing is active, risk may not be reopened.
11. Adaptive health may update only after the underlying trades are complete and after the configured effective timestamp.
12. No hidden data imputation.
13. Failed folds, losing months, rejected lanes, and failed models must remain visible.
14. Never loosen gates to manufacture a pass.
15. Daily profit targets are evaluation metrics, not order quotas.
16. Never increase leverage merely because the daily target has not been reached.
17. Do not claim profitability before full OOS, stress, and sealed holdout validation.

## Required simple baselines

Every complex component must beat or justify itself against a simpler baseline:

- Rule-based regime before probabilistic regime.
- Static router before adaptive router.
- Logistic meta model before boosted-tree model.
- Fixed notional before adaptive risk sizing.
- Fixed TP/SL before trail and emergency exits.
- Best single lane and equal-weight qualified lanes before full adaptive portfolio.

If a complex component fails to improve OOS performance, risk, calibration, or robustness, remove it.

## Development rules

- Typed Python where practical.
- Deterministic seeds.
- `pytest`, linting, type checking, and schema validation.
- Production logic belongs in `src/`; notebooks are exploratory only.
- Commands are idempotent and non-zero on failure.
- Maintain `STATUS.md` after each Phase.
- Commit phase-level work with clear messages.
- Record package versions, Git SHA, config hash, data hash, model hash, and policy hash.
- Never open the sealed holdout from a normal research command.
- Every adaptive decision must be replayable from a decision ledger.

## Final truth labels

Only use the labels defined in `config/acceptance.yaml`. A positive backtest without all gates is not a production-ready result.
