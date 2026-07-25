# 05 — Regime, Meta Scoring, and Adaptive Policy

## 1. Regime taxonomy

```text
TREND_UP
TREND_DOWN
RANGE
COMPRESSION
EXPANSION_UP
EXPANSION_DOWN
CHAOTIC_HIGH_VOL
QUIET_LOW_VOL
UNKNOWN
```

`UNKNOWN` is mandatory.

## 2. Point-in-time regime features

- EMA structure and slopes;
- ADX;
- ATR percentage and percentile;
- Bollinger width and percentile;
- realized volatility;
- trend efficiency;
- rolling returns;
- volume percentile;
- candle body/range;
- VWAP distance;
- rolling high/low distance;
- short-term autocorrelation;
- regime duration and transition persistence.

## 3. Regime models

### Baseline

`RuleBasedRegimeV1`

Must be interpretable and deterministic.

### Challenger

`ProbabilisticRegimeV2`

Allowed candidates:

- logistic regression;
- histogram gradient boosting;
- HMM as a challenger only.

A challenger replaces the rule model only if it improves OOS routing, calibration, or risk.

Output:

```text
regime_id
regime_probabilities
unknown_probability
transition_confidence
regime_duration
previous_regime
```

## 4. Static router baseline

Map regime to:

```text
allow
shadow
block
```

Compare against:

- all qualified lanes enabled;
- best single lane;
- equal-weight lanes;
- no regime filter.

## 5. Meta signal scoring

### Inputs

- lane and direction;
- regime probabilities;
- current market features;
- signal strength;
- entry distance;
- predicted fill probability;
- stop and target distances;
- time of day;
- lane historical OOS health in similar regimes;
- uncertainty;
- current drawdown state.

### Outputs

```text
p_win
expected_gross_pnl
expected_fee
expected_slippage
expected_net_pnl
predicted_mae
predicted_mfe
predicted_holding_time
uncertainty
```

### Models

1. `MetaLogisticV1`.
2. `MetaBoostedTreeV2` challenger.

Calibrate probabilities on validation data only.

Pre-register p-win candidates:

```text
0.60, 0.65, 0.70, 0.75
```

A signal requires positive predicted after-cost PnL as well as the selected confidence threshold.

## 6. Lane health

Daily point-in-time metrics:

- rolling 20-trade and 50-trade expectancy;
- rolling 30-day expectancy;
- regime-specific expectancy;
- PF;
- win rate;
- average win/loss;
- fill quality;
- fee ratio;
- MFE/MAE;
- drawdown;
- losing streak;
- fold stability;
- stress-test sensitivity;
- sample size;
- concentration.

Use Bayesian or empirical shrinkage so small recent samples do not dominate.

Initial conceptual score:

```text
+ shrunk expectancy
+ PF
+ regime fit
+ calibrated win rate
+ fill quality
+ fold stability
+ sample confidence
- drawdown penalty
- cost sensitivity
- concentration penalty
```

All components require bounded normalization.

## 7. Lane state transitions

### ACTIVE

Qualified and healthy.

### REDUCED

Still valid but recent performance, drawdown, or fill quality has weakened.

Actions may include:

- lower notional;
- higher entry threshold;
- lower router weight.

### SHADOW

New, insufficient sample, degraded, or stress-sensitive. Continue simulated signals but allocate zero official capital.

### DISABLED

Hard blocker, material negative expectancy, data issue, or risk event.

### RETIRED

Persistent multi-fold failure or redundant underperformance.

State transitions must log effective time, data cutoff, metrics snapshot, old state, new state, and reason codes.

## 8. Final signal score

A bounded example:

```text
final_score =
expected_net_pnl
× calibrated_p_win
× regime_compatibility
× lane_health_multiplier
× predicted_fill_probability
× uncertainty_discount
```

Bounds:

```text
regime_compatibility: 0.00–1.00
lane_health_multiplier: 0.50–1.30
uncertainty_discount: 0.50–1.00
```

## 9. Conflict arbitration

### Same direction

Select the highest final score. Record others as suppressed.

### Opposite direction

If score difference is below a frozen margin, choose `NO_TRADE`.

### Existing position

A new same-direction signal cannot stack exposure in the primary path. An opposite signal can only invoke a preregistered emergency-exit rule; it cannot immediately reverse.

## 10. Adaptive evaluation groups

Compare:

```text
A. Best single qualified lane
B. Equal-weight qualified lanes
C. Static regime router
D. Static router + meta filter
E. Static router + lane health
F. Full adaptive router
```

Full adaptive is retained only if it improves after-cost OOS results, drawdown, calibration, or robustness. Complexity alone is not evidence.
