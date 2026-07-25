# 00 — Project Charter

## 1. Problem statement

The project must determine whether a 200 USDC account can support a repeatable, after-cost adaptive futures strategy on ETHUSDC without relying on hidden lookahead, unrealistic fills, uncontrolled leverage, or a single overfit lane.

The project is not complete when a profitable equity curve is found. It is complete when the repository can explain:

1. Which market regime was identified at each decision.
2. Which lanes were eligible.
3. Why a specific lane was selected or suppressed.
4. Which entry and exit profile was frozen for that trade.
5. Why position size and effective leverage were allowed.
6. Whether trail, break-even, partial exit, or emergency reversal improved after-cost OOS performance.
7. Whether 200 USDC achieved average calendar-day net profit targets of 0.50, 1.00, or 2.00 USDC without violating risk gates.
8. Whether the result survives the sealed holdout and stress tests.
9. When the correct action was `NO_TRADE`.

## 2. Scope

### Included

- Public historical market data.
- ETHUSDC primary research.
- BTCUSDC generalization.
- 1m event replay.
- Multi-timeframe features.
- Seven candidate trading lanes plus `L0_NO_TRADE`.
- Regime classification.
- Entry and exit profile labs.
- Trail and sudden-reversal exits.
- Funding, fee, and slippage accounting.
- Effective leverage and risk-based sizing research.
- Walk-forward and nested walk-forward.
- Stress testing and ablation.
- 180-day sealed holdout.
- Shadow research package.

### Excluded

- Testnet.
- Live exchange API.
- API secrets.
- Real-money orders.
- Automated re-training in production.
- Reinforcement learning.
- Unlimited parameter search.
- Claims of guaranteed daily income.
- Tick-accurate or order-book-accurate behavior unless later data supports it.

## 3. Primary research questions

1. Do any individual lanes have positive pooled OOS expectancy?
2. Does regime filtering improve lane performance after costs?
3. Does meta filtering improve expectancy without reducing coverage to a meaningless level?
4. Do adaptive lane health and state transitions improve performance or reduce drawdown?
5. Which entry profiles improve fill quality?
6. Which exit profiles improve after-cost PnL?
7. Does trail help trend lanes but harm range lanes?
8. Does emergency reversal exit reduce loss tails without over-exiting winners?
9. What effective leverage range offers the best risk-adjusted outcome?
10. Can the final system meet `PASS_TARGET_A`, `PASS_TARGET_B`, or `PASS_STRETCH`?
11. Does adaptive complexity outperform simple baselines?
12. Does the system generalize to BTCUSDC?

## 4. Non-negotiable principles

- Point-in-time correctness before optimization.
- Conservative execution before profitability claims.
- Simple baseline before complex model.
- Pre-registration before holdout.
- Risk-based exposure before leverage-driven return targets.
- `NO_TRADE` is a valid and often preferable outcome.
