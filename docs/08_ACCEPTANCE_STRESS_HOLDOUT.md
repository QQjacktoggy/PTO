# 08 — Acceptance, Stress, and Sealed Holdout

## 1. Lane admission

Default minimums:

- pooled OOS trades: 60;
- OOS PnL > 0;
- expectancy > 0;
- PF >= 1.10;
- positive test-fold ratio >= 60%;
- no lookahead;
- no severe concentration;
- no material moderate-cost failure;
- no parameter cliff.

## 2. Full adaptive minimum sample

Default:

- pooled OOS trades >= 150;
- holdout trades must be reported even when below target;
- no-trade days count in daily averages.

## 3. Stress matrix

### Costs

```text
Baseline: maker 0, taker 4, slippage 1 bp
Moderate: maker 1, taker 5, slippage 2 bp
Severe: maker 2, taker 8, slippage 4 bp
```

### Fills

- remove 5%, 10%, 20% of maker fills;
- strict 1-tick and 2-tick cross;
- one- and two-minute entry delay;
- TTL shorter and longer;
- no price improvement.

### Exit timing

- trail activates one minute later;
- emergency exit one and two minutes later;
- stop slippage;
- gap-through-stop approximation;
- partial-fill sensitivity.

### Parameters

- ±10% neighborhood;
- start-date shift;
- fold boundary shift;
- model threshold neighbors.

### Architecture ablation

- no regime;
- no meta model;
- no lane health;
- fixed notional;
- no trail;
- no emergency exit;
- no adaptive sizing;
- rule regime only;
- logistic meta only.

### Generalization

- BTCUSDC with frozen ETH-derived architecture and only allowed symbol normalization.
- Bull, bear, range, compression, and expansion segments.

## 4. Profit concentration

Flag:

- one trade > 10% total PnL;
- one month > 35% total PnL;
- best five days dominate total result;
- one lane dominates without independent stability.

## 5. Final labels

### PASS_SURVIVAL

- pooled OOS after-cost PnL > 0;
- expectancy > 0;
- PF >= 1.15;
- maximum drawdown <= 16 USDC;
- sealed holdout PnL > 0;
- moderate stress not materially negative.

### PASS_TARGET_A

All survival gates plus:

- average calendar-day net PnL >= 0.50 USDC;
- pooled OOS WR >= 75%;
- PF >= 1.20;
- pooled OOS trades >= 150;
- positive fold ratio >= 70%;
- holdout WR >= 70%;
- random 10% fill-drop median remains positive.

### PASS_TARGET_B

All Target A gates plus:

- average calendar-day net PnL >= 1.00 USDC;
- PF >= 1.25;
- full adaptive outperforms or materially lowers drawdown versus best single lane;
- moderate cost and fill stress remain positive.

### PASS_STRETCH

All Target B gates plus:

- average calendar-day net PnL >= 2.00 USDC;
- result does not require effective leverage above 5x;
- no severe concentration;
- severe or near-severe stress is not catastrophic.

### PASS_ADAPTIVE_EV_ONLY

- positive and robust expectancy;
- does not meet the preferred 75% WR or daily target;
- must not be described as meeting Target A/B.

### Failure labels

- `NO_ADAPTIVE_SYSTEM_PASSED`
- `INSUFFICIENT_HISTORY`
- `BLOCKED_BY_DATA_OR_ENGINE`

## 6. Sealed holdout protocol

Before opening holdout, freeze:

- data cutoff and hashes;
- lane definitions;
- lane parameters;
- entry/exit profiles;
- regime model;
- meta model;
- calibration;
- thresholds;
- lane-health formula;
- state transitions;
- arbitration;
- sizing;
- leverage caps;
- fees and slippage;
- execution priority;
- acceptance gates.

Generate a frozen manifest with hashes. The holdout command must refuse to run without this manifest and must append to an access log.

After holdout:

- report the result;
- do not tune and re-open while calling it the same holdout;
- any subsequent research creates a new version and requires a future unseen period.
