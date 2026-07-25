# 06 — Risk, Effective Leverage, and 200 USDC Targets

## 1. Exchange leverage versus effective leverage

The research variable is:

```text
effective_leverage =
open_position_notional / account_equity
```

Exchange initial leverage is an implementation setting that affects margin use and liquidation safety. It does not create additional price PnL when notional is unchanged.

For 200 USDC equity:

| Notional | Effective leverage |
|---:|---:|
| 50 USDC | 0.25x |
| 100 USDC | 0.50x |
| 200 USDC | 1.00x |
| 300 USDC | 1.50x |
| 400 USDC | 2.00x |
| 600 USDC | 3.00x |
| 1,000 USDC | 5.00x |

## 2. Effective leverage candidates

Formal OOS candidates:

```text
0.25x, 0.50x, 1.00x, 1.50x, 2.00x, 3.00x, 5.00x
```

Stress only:

```text
7.50x, 10.00x
```

Do not promote 20x, 50x, or 75x in this first adaptive research package.

## 3. Risk-based sizing

```text
risk_budget_usdc = equity × risk_per_trade
raw_notional = risk_budget_usdc / stop_distance_fraction
```

Then cap by:

- maximum effective leverage;
- lane state;
- lane confidence;
- regime confidence;
- daily risk remaining;
- drawdown state;
- liquidity and minimum-order rules.

Risk-per-trade candidates:

```text
0.25%, 0.50%, 0.75%, 1.00%
```

Baseline:

```text
0.50%
```

For 200 USDC, this is 1 USDC planned risk before adverse gap/slippage.

## 4. Discrete allocation bands

```text
SHADOW: 0
LOW: 25–50 USDC
NORMAL: 75–150 USDC
HIGH: 150–300 USDC
```

The stop-based risk cap always overrides the band.

## 5. Portfolio safety

Baseline:

- Daily realized net loss stop: -2 USDC.
- At -8 USDC drawdown: all lanes at most `REDUCED`.
- At -12 USDC drawdown: only the highest-quality eligible lane may trade at reduced exposure.
- At -16 USDC drawdown: all official trading decisions disabled.
- No loss-based sizing increase.
- No daily-target-based leverage increase.
- No DCA.

## 6. Daily profit targets

Daily targets are evaluated over all calendar days, including no-trade days.

### Target definitions

| Label | Average calendar-day net PnL | 200 USDC simple daily return |
|---|---:|---:|
| Survival | > 0 | > 0% |
| Target A | >= 0.50 USDC | >= 0.25% |
| Target B | >= 1.00 USDC | >= 0.50% |
| Stretch | >= 2.00 USDC | >= 1.00% |

Do not treat 4–6 USDC per day as a baseline requirement. It may be displayed only as an extreme-risk scenario and cannot pass if risk gates fail.

## 7. Required daily metrics

- average calendar-day net PnL;
- average active-day net PnL;
- median daily PnL;
- positive-day ratio;
- no-trade-day ratio;
- worst day;
- best day;
- rolling 7-day PnL;
- rolling 30-day PnL;
- 30-day target hit rate;
- percentage of total PnL from best five days;
- daily drawdown distribution.

## 8. Leverage research comparisons

For each exposure method, report:

```text
fixed 50 USDC notional
fixed effective leverage
fixed percentage risk
adaptive risk sizing
```

Control for the same signal set and policy where possible. Adaptive must not claim improvement that comes solely from taking more risk.

## 9. Liquidation and margin caveat

The initial historical model may focus on price PnL and effective exposure. Before any later deployment phase, add symbol-specific maintenance margin, liquidation, mark-price, and margin-mode modeling. Until then, label leverage outputs as exposure research rather than complete liquidation simulation.
