# ETHUSDC Adaptive Multi-Lane Quant Research System — Complete Work Handoff Plan

**版本：** 2.0.0  
**日期：** 2026-07-25  
**資金基準：** 200 USDC  
**最終目標：** 可驗證的 adaptive lane、進出場、trail、反向停損、風險與倍率系統。


---


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


---


# 01 — System Architecture

## 1. Logical flow

```text
Public market data
  ↓
Immutable raw store + manifest
  ↓
Normalized 1m timeline
  ↓
Lag-safe 5m / 15m / 1h features
  ↓
Regime classifier
  ↓
Independent lane signal engines
  ↓
Regime eligibility
  ↓
Entry-profile candidates
  ↓
Meta score and uncertainty
  ↓
Lane health and state
  ↓
Conflict arbitration
  ↓
Risk budget and effective leverage
  ↓
Maker order replay
  ↓
Position state machine
  ↓
TP / SL / BE / trail / emergency exit
  ↓
Ledgers and equity
  ↓
Delayed health update
  ↓
Reports and decision
```

## 2. Proposed source tree

```text
src/
├─ data/
│  ├─ download.py
│  ├─ normalize.py
│  ├─ resample.py
│  ├─ funding.py
│  ├─ metadata.py
│  └─ quality.py
├─ features/
│  ├─ technical.py
│  ├─ multi_timeframe.py
│  ├─ point_in_time.py
│  └─ registry.py
├─ regimes/
│  ├─ rules_v1.py
│  ├─ probabilistic_v2.py
│  ├─ transitions.py
│  └─ calibration.py
├─ lanes/
│  ├─ base.py
│  ├─ l1_trend_pullback.py
│  ├─ l2_breakout_retest.py
│  ├─ l3_range_mean_reversion.py
│  ├─ l4_volatility_expansion.py
│  ├─ l5_exhaustion_reversal.py
│  ├─ l6_liquidity_sweep.py
│  └─ l7_micro_momentum.py
├─ policies/
│  ├─ entry.py
│  ├─ stops.py
│  ├─ profit.py
│  ├─ break_even.py
│  ├─ trailing.py
│  ├─ emergency.py
│  └─ time_exit.py
├─ execution/
│  ├─ events.py
│  ├─ order_state.py
│  ├─ fill_model.py
│  ├─ position_state.py
│  ├─ intrabar_priority.py
│  ├─ fees.py
│  └─ replay.py
├─ meta/
│  ├─ training_table.py
│  ├─ logistic.py
│  ├─ boosted.py
│  ├─ calibration.py
│  └─ inference.py
├─ adaptive/
│  ├─ eligibility.py
│  ├─ lane_health.py
│  ├─ shrinkage.py
│  ├─ state_machine.py
│  ├─ router.py
│  └─ decision.py
├─ portfolio/
│  ├─ arbitration.py
│  ├─ risk_budget.py
│  ├─ sizing.py
│  ├─ drawdown.py
│  └─ daily_limits.py
├─ evaluation/
│  ├─ metrics.py
│  ├─ walk_forward.py
│  ├─ nested_walk_forward.py
│  ├─ stress.py
│  ├─ ablation.py
│  ├─ bootstrap.py
│  └─ holdout_guard.py
├─ reporting/
│  ├─ tables.py
│  ├─ charts.py
│  ├─ html.py
│  └─ decision_report.py
└─ cli/
   └─ main.py
```

## 3. Component boundaries

### Signal engine

Produces a raw, timestamped hypothesis. It does not decide position size or mutate an open trade.

### Entry policy

Converts a qualified signal into an order intent with limit price, TTL, and at most one allowed reprice when the selected profile permits it.

### Execution engine

Determines whether an order is filled under conservative 1m rules. It must not inspect later bars beyond the current replay event.

### Position state machine

Owns stop, target, break-even, trailing, partial exits, emergency exit, and time exit. It must enforce monotonic risk reduction.

### Adaptive router

Selects among prequalified signals and policies. It cannot invent new parameters during test or holdout.

### Portfolio layer

Owns the one-position constraint, signal conflict resolution, daily stop, drawdown degradation, notional cap, and effective leverage cap.

### Evaluation layer

Owns time splits, fold freezing, stress tests, target labels, and sealed holdout protection.

## 4. Required ledgers

- `data_manifest`
- `feature_manifest`
- `experiment_registry`
- `signal_ledger`
- `decision_ledger`
- `order_ledger`
- `fill_ledger`
- `position_event_ledger`
- `trade_ledger`
- `equity_ledger`
- `lane_health_ledger`
- `model_manifest`
- `policy_manifest`
- `holdout_access_log`

Every final trade must be traceable backward to data version, feature version, signal, decision, order, fill, position events, and final PnL.


---


# 02 — Data, Replay, and Validation Contract

## 1. Data requirements

### Primary

- ETHUSDC USD-M Futures 1m OHLCV.
- Historical funding rates.
- Exchange metadata:
  - tick size;
  - quantity step;
  - minimum quantity;
  - contract status and listing history when available.

### Generalization

- BTCUSDC with identical pipeline and no BTC-specific post-hoc tuning.

### Storage

```text
data/raw/          immutable downloads
data/normalized/   normalized 1m timeline
data/features/     lag-safe feature tables
data/manifests/    source and checksum manifests
```

## 2. Time rules

- Store and compute in UTC.
- Reports may additionally display Asia/Taipei.
- A 15m feature row becomes usable only after the full 15m bar closes.
- A 1h feature row becomes usable only after the full 1h bar closes.
- Informative timeframe joins use backward/as-of joins with tests proving the source timestamp is not later than the decision timestamp.
- Warm-up rows cannot trade.
- The current incomplete UTC day is excluded from historical batch research unless a dedicated partial-day mode is explicitly selected.

## 3. Data-quality gates

Block research on:

- duplicate timestamps;
- unsorted timestamps;
- `high < low`;
- open or close outside `[low, high]`;
- negative volume;
- timezone ambiguity;
- silent symbol substitution;
- large unexplained missing intervals;
- funding timestamps that cannot be mapped consistently;
- stale or conflicting metadata.

Gaps must be classified:

```text
EXPECTED_EXCHANGE_GAP
MISSING_SOURCE_FILE
DOWNLOAD_FAILURE
UNEXPLAINED_GAP
```

Do not forward-fill OHLCV.

## 4. 1m maker fill model

### Conservative main result

For a long buy limit:

```text
minute_low < rounded_limit_price - cross_ticks × tick_size
```

For a short sell limit:

```text
minute_high > rounded_limit_price + cross_ticks × tick_size
```

Baseline `cross_ticks = 1`.

### Sensitivities

- touch fill;
- strict one-tick cross;
- strict two-tick cross;
- random fill removal;
- entry delay;
- TTL variation;
- one permitted reprice for selected profiles.

Only the conservative model is eligible for the main decision.

## 5. Position event ordering

The replay engine must document and test event priority. Baseline conservative priority:

```text
1. Exchange or liquidation safety condition, if modeled
2. Existing hard stop
3. Emergency exit already armed before this minute
4. Existing trailing stop
5. Existing break-even stop
6. Existing take-profit order
7. Time exit already scheduled
8. End-of-minute signal or state update
```

Rules:

- Entry-minute TP is not allowed.
- Entry-minute hard stop is allowed.
- A break-even or trail condition first observed on a completed minute becomes active no earlier than the next minute.
- An OHLCV reversal detector first observed at close schedules a taker exit at the next executable event.
- If both TP and SL are ambiguous within the same minute, use stop-first in the main result.
- A stop cannot widen after entry.

## 6. Fees and funding

Every fill records:

- liquidity role;
- price;
- quantity;
- notional;
- fee rate;
- fee;
- slippage assumption;
- funding attribution when applicable.

Main PnL:

```text
net_pnl =
gross_price_pnl
- entry_fee
- exit_fee
- slippage_cost
- funding_cost_or_credit
```

## 7. Determinism and parity

Required tests:

- Same data/config/seed produces byte-identical ledgers or an explicitly normalized identical result.
- PnL recalculates from fills.
- Equity change equals summed trade and funding PnL.
- No negative quantity or impossible state transition.
- Every fill has an order.
- Every closed trade has an opening fill and closing fill(s).
- Every decision uses features whose timestamps are no later than the decision.
- Freqtrade signal baseline and pure Python signals have a parity report.
- Holdout commands are blocked until a signed/frozen manifest exists.

## 8. 1m limitations

1m OHLCV cannot prove:

- tick order inside the minute;
- queue position;
- order-book imbalance;
- sub-minute sudden reversal;
- actual partial-fill sequence.

Therefore reports must call the current system `minute-resolution replay`, not tick-accurate execution. Any future second-level or trade-level work is a separate project.


---


# 03 — Lane Library

## L0_NO_TRADE

A formal outcome, not a failure.

Trigger examples:

- unknown or conflicting regime;
- all lane confidence below threshold;
- expected after-cost PnL not positive;
- excessive uncertainty;
- daily loss stop reached;
- drawdown state forbids new risk;
- data-quality warning;
- all lanes shadow/disabled/retired;
- opposing signals with insufficient score gap.

## L1_TREND_PULLBACK

### Hypothesis

A higher-timeframe trend persists after a controlled 15m pullback and renewed momentum.

### Core evidence

- 1h trend direction and slope;
- 15m EMA structure;
- controlled distance from EMA or VWAP;
- RSI recovery;
- acceptable ATR and volume.

### Candidate entry profiles

- E0 baseline maker;
- E2 conservative maker;
- E4 close confirmation.

### Candidate exits

- ATR or hybrid stop;
- partial profit;
- chandelier or MFE trail;
- adverse-velocity emergency exit.

### Expected regimes

`TREND_UP`, `TREND_DOWN`.

## L2_BREAKOUT_RETEST

### Hypothesis

A completed range breakout followed by a valid retest has positive continuation expectancy.

### Guardrails

- breakout requires close confirmation;
- no entry on an unfinished breakout candle;
- retest must hold within a defined invalidation band;
- avoid chasing beyond maximum ATR extension.

### Candidate entries

- E0 baseline maker;
- E1 aggressive maker;
- E4 close confirmation.

### Candidate exits

- structure/hybrid stop;
- partial + trail;
- opposite-impulse and regime-flip emergency exit.

### Expected regimes

`COMPRESSION`, `EXPANSION_UP`, `EXPANSION_DOWN`, early trend.

## L3_RANGE_MEAN_REVERSION

### Hypothesis

When trend efficiency and ADX are low, statistically significant deviation from a stable range or VWAP reverts inward.

### Guardrails

- block in confirmed expansion;
- block against strong higher-timeframe trend;
- require a completed re-entry or rejection signal;
- target range interior, not a large trend move.

### Candidate entries

- E2 conservative maker;
- E3 second touch.

### Candidate exits

- structure stop;
- fixed target;
- usually no trail;
- regime-flip emergency exit.

### Expected regime

`RANGE`.

## L4_VOLATILITY_EXPANSION

### Hypothesis

Low-volatility compression followed by confirmed directional expansion produces a short-lived momentum opportunity.

### Guardrails

- compression percentile is known before breakout;
- require price, body, volume, and volatility expansion;
- avoid post-event extreme extension;
- conservative fill and latency stress are mandatory.

### Candidate entries

- E1 aggressive maker;
- E4 close confirmation.

### Candidate exits

- hybrid stop;
- partial profit;
- MFE giveback or chandelier trail;
- opposite impulse.

### Expected regimes

`COMPRESSION`, `EXPANSION_UP`, `EXPANSION_DOWN`.

## L5_EXHAUSTION_REVERSAL

### Hypothesis

After an overextended move, a second failed attempt to continue may offer a reversal with defined invalidation.

### Guardrails

- no centered pivots;
- first reversal attempt is observation only;
- second attempt must be identified with backward-looking data;
- block against continuing high-confidence expansion.

### Candidate entries

- E3 second touch;
- E4 close confirmation.

### Candidate exits

- structure/hybrid stop;
- fixed or partial target;
- time-decaying trail;
- opposite-lane confirmation and MFE failure.

### Expected regimes

Late trend, exhausted expansion, selected range edges.

## L6_LIQUIDITY_SWEEP

### Hypothesis

A known historical range high/low is swept, but the completed candle returns inside and continuation fails.

### Status

Experimental until it passes lane admission.

### Candidate entries

- E3 second touch;
- E4 close confirmation.

### Candidate exits

- structure stop;
- fixed target;
- regime flip;
- no-bounce exit.

## L7_MICRO_MOMENTUM

### Hypothesis

1m/5m momentum can supplement higher-timeframe expansion when after-cost edge survives conservative fills.

### Status

Experimental. It must not be promoted solely on 1m OHLCV because queue and microstructure uncertainty are high.

### Mandatory stress

- taker fee increase;
- entry delay;
- fill removal;
- strict two-tick cross;
- shorter edge half-life;
- trade-level or tick-data follow-up flag.

## Lane admission requirements

A lane may enter the adaptive candidate pool only when all apply:

- pooled OOS trades at or above configured minimum;
- pooled OOS net PnL > 0;
- expectancy > 0;
- PF at or above threshold;
- sufficient positive-fold ratio;
- no lookahead;
- no unresolved data blocker;
- no severe profit concentration;
- moderate cost stress is not materially negative;
- no parameter cliff.

Possible states:

```text
ACTIVE
REDUCED
SHADOW
DISABLED
RETIRED
```

A rejected lane remains visible in reports.


---


# 04 — Entry, Exit, Trail, and Sudden-Reversal Management

## 1. Principle

Adaptive trade management selects from a finite prequalified policy library. It does not optimize parameters while a test or holdout trade is open.

At entry, freeze:

```text
lane_id
regime_snapshot
entry_profile
stop_profile
profit_profile
break_even_profile
trail_profile
emergency_profile
time_exit_profile
risk_budget
notional
effective_leverage
policy_version
```

After entry, policies may reduce risk but may never increase the original maximum loss.

## 2. Entry profiles

### E0_BASELINE_MAKER

- Offset: 1 bp from signal close.
- TTL: 5 minutes.
- No reprice.
- No market chase.

### E1_AGGRESSIVE_MAKER

- Offset: 0 bp.
- TTL: 3 minutes.
- Intended for high-confidence continuation.
- Must survive adverse-selection tests.

### E2_CONSERVATIVE_MAKER

- Offset candidates: 2 or 3 bps.
- TTL candidates: 5 or 10 minutes.
- Intended for pullback and mean reversion.

### E3_SECOND_TOUCH

- Observe the first test.
- Require price to move away.
- Enter only on a second point-in-time-valid test with confirmation.
- No post-hoc pivot recognition.

### E4_CLOSE_CONFIRMATION

- Wait one additional completed confirmation bar.
- Re-evaluate invalidation, regime, and extension.
- Accept lower coverage if expectancy improves.

### E5_ONE_REPRICE

- Original order expires.
- Signal remains valid.
- Price remains inside maximum chase distance.
- Permit exactly one recalculated maker order.
- Never loop repricing.

## 3. Initial stop profiles

### S0_FIXED_PERCENT

Candidates:

```text
0.25%, 0.30%, 0.35%, 0.40%, 0.50%
```

### S1_ATR

Candidates:

```text
0.6, 0.8, 1.0, 1.2 ATR
```

Use minimum and maximum percentage clamps.

### S2_STRUCTURE

Use only backward-looking confirmed structure.

### S3_HYBRID

Combine structure invalidation with an ATR maximum-risk clamp.

## 4. Profit profiles

### P0_FIXED_R

Candidates:

```text
0.50R, 0.65R, 0.80R, 1.00R, 1.25R, 1.50R
```

### P1_PARTIAL_PLUS_RUNNER

Candidate families:

```text
50% at 0.60R + runner
40% at 0.80R + runner
```

Include added exit fees.

### P2_REGIME_TARGET

- Range: shorter target.
- Trend: longer target or trail.
- Expansion: protect cost and retain runner.

The selected profile is frozen at entry. Risk may tighten later; target must not be expanded without a preregistered rule.

## 5. Break-even profiles

Candidate triggers:

```text
0.35R, 0.50R, 0.65R, 0.80R
```

Break-even price must cover:

- entry fee;
- expected exit fee;
- slippage buffer.

Candidate activation modes:

- next-minute activation;
- completed-close confirmation;
- no break-even baseline.

Required analysis:

- complete stops avoided;
- later winners cut;
- break-even exit ratio;
- after-cost expectancy change.

## 6. Trailing profiles

### T0_NONE

Fixed stop/target baseline.

### T1_ATR_TRAIL

Trail from the most favorable price by a configured ATR multiple.

### T2_CHANDELIER

Use highest favorable high or lowest favorable low after entry and ATR.

### T3_MFE_GIVEBACK

Pre-register allowed giveback by MFE band.

Example research candidates:

```text
0.5R–1.0R: allow 60% giveback
1.0R–1.5R: allow 40%
>1.5R: allow 25%
```

### T4_SWING_TRAIL

Use only backward-looking confirmed higher lows/lower highs after entry.

### T5_TIME_DECAYING

Tighten as the trade exceeds expected time-to-edge.

### T6_PARTIAL_AND_TRAIL

Take partial profit, move protection toward after-cost break-even, trail the runner.

Candidate trail activation:

```text
0.4R, 0.6R, 0.8R, 1.0R
```

## 7. Sudden-reversal emergency profiles

### R0_OPPOSITE_IMPULSE

Detect a completed adverse impulse using:

- ATR-normalized body;
- body/range;
- volume percentile;
- close location;
- direction.

Schedule exit at the next executable event.

### R1_ADVERSE_VELOCITY

Measure adverse movement over 1 and 3 completed minutes normalized by ATR.

### R2_NO_BOUNCE

After minimum observation time, repeated failed attempts to reclaim entry/VWAP/short EMA may trigger exit.

### R3_REGIME_FLIP

A high-confidence transition into an opposing expansion or chaotic state may:

- tighten stop;
- partially exit;
- fully exit.

Only preregistered actions are allowed.

### R4_OPPOSITE_LANE_CONFIRMATION

A strong opposite signal may close the current position when its score exceeds continuation score by a frozen margin.

Do not reverse immediately. Require:

```text
close current position
→ wait at least one full decision interval
→ recompute
→ optionally enter opposite direction
```

### R5_MFE_FAILURE

After meaningful MFE, rapid giveback plus confirmed momentum reversal may exit before the original stop.

## 8. Time exits

Candidates are lane-specific and expressed in completed 15m bars or minutes. They must compare:

- fixed duration;
- regime-specific duration;
- time-decaying protection.

## 9. Policy qualification

Do not brute-force the full Cartesian product.

### Stage A — module screening

Evaluate each module against a simple baseline.

### Stage B — bounded retained set

Per lane, retain at most:

- 2 entry profiles;
- 2 stop profiles;
- 2 profit profiles;
- 2 trail profiles;
- 1–2 emergency profiles.

### Stage C — lane × regime mapping

Freeze a small policy map before nested walk-forward and holdout.

## 10. Required exit attribution

Each exit must carry one reason:

```text
HARD_STOP
TAKE_PROFIT
PARTIAL_TAKE_PROFIT
BREAK_EVEN_STOP
TRAILING_STOP
OPPOSITE_IMPULSE
ADVERSE_VELOCITY
NO_BOUNCE
REGIME_FLIP
OPPOSITE_LANE
MFE_FAILURE
TIME_EXIT
DAILY_RISK_EXIT
PORTFOLIO_RISK_EXIT
DATA_SAFETY_EXIT
```

Reports must show both loss saved and profit sacrificed by each adaptive exit.


---


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


---


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


---


# 07 — Phase Execution Plan

## Universal phase gate

Every Phase must produce:

1. Code or governance artifacts.
2. Tests and validation output.
3. A phase report.
4. Updated manifests.
5. Updated `STATUS.md`.
6. A clear Git commit.
7. A machine-readable gate result.

No phase may be marked complete based only on prose.

---

## Phase 0 — Governance, Scaffold, and Holdout Guard

### Objective

Establish project boundaries, schemas, CLI, tests, experiment registry, and a technically enforced sealed holdout.

### Deliverables

- repository structure;
- `AGENTS.md`;
- Python project files;
- config schemas;
- experiment registry;
- holdout guard;
- `STATUS.md`;
- Phase 0 report.

### Gate

- config validates;
- holdout access is denied by default;
- lint/typecheck/test commands run;
- deterministic seed and version recording exist.

---

## Phase 1 — Data Acquisition and QA

### Objective

Build an idempotent, resumable ETHUSDC and BTCUSDC public-data pipeline.

### Deliverables

- raw and normalized 1m data;
- funding data;
- metadata;
- checksums;
- gap and OHLC QA;
- 5m/15m/1h resampling;
- data-quality report.

### Gate

No unresolved critical data blocker.

---

## Phase 2 — Point-in-Time Features and Replay Engine

### Objective

Build lag-safe features, ledgers, maker fill model, fees, funding, and the position state machine.

### Deliverables

- feature registry;
- replay engine;
- state-transition tests;
- fill and PnL parity;
- same-minute priority tests;
- execution report.

### Gate

Deterministic replay, complete ledger traceability, zero unresolved critical invariants.

---

## Phase 3 — L1 Baseline and Cross-Engine Parity

### Objective

Implement `L1_TREND_PULLBACK` as the engineering baseline.

### Deliverables

- pure Python signal engine;
- optional Freqtrade baseline;
- signal parity report;
- lookahead and recursive tests;
- untuned conservative replay.

### Gate

Engineering correctness; profitability is not required yet.

---

## Phase 4 — Multi-Lane Library

### Objective

Implement L2 through L7 independently.

### Deliverables

For each lane:

- formal specification;
- signal tags;
- unit tests;
- leakage tests;
- untuned baseline;
- data/sample warnings.

### Gate

Each lane is distinguishable and reproducible. No copied lane with cosmetic renaming.

---

## Phase 5 — Entry Policy Lab

### Objective

Evaluate E0–E5 without exit-policy overfitting.

### Deliverables

- fill-rate tables;
- adverse-selection analysis;
- missed-winner analysis;
- entry profile OOS scorecards;
- retained profile registry.

### Gate

At most two qualified entry profiles per lane.

---

## Phase 6 — Exit and Trade-Management Lab

### Objective

Evaluate S0–S3, P0–P2, break-even, T0–T6, R0–R5, and time exits.

### Deliverables

- module-level OOS tests;
- trail benefit/harm by lane and regime;
- emergency-exit saved-loss versus sacrificed-profit analysis;
- bounded retained policy set.

### Gate

No full Cartesian optimization. Retained policies are limited and preregistered.

---

## Phase 7 — Individual Lane Walk-Forward Qualification

### Objective

Determine which lanes and lane-policy packages have positive OOS value.

### Default split

```text
Train 12 months
Validation 3 months
Test 3 months
Step 3 months
Embargo 7 days
Final holdout 180 days
```

### Deliverables

- fold reports;
- lane admission states;
- rejected-lane reasons;
- parameter plateau evidence.

### Gate

Only qualified lanes enter the router.

---

## Phase 8 — Regime System and Static Router

### Objective

Build the rule-based regime baseline, optional probabilistic challenger, and static eligibility map.

### Deliverables

- regime timeline;
- transition matrix;
- lane × regime matrix;
- static router comparisons;
- unknown and chaotic behavior.

### Gate

Router must improve or justify itself against simpler baselines.

---

## Phase 9 — Meta Model and Adaptive Lane Health

### Objective

Build calibrated signal filtering and delayed daily lane-health updates.

### Deliverables

- point-in-time training table;
- logistic baseline;
- optional boosted challenger;
- calibration reports;
- lane health ledger;
- state-transition tests.

### Gate

Expectancy improves without meaningless coverage collapse; health is leakage-safe.

---

## Phase 10 — Conflict Arbitration, Risk Budget, and Leverage

### Objective

Combine eligible signals, position constraints, daily risk, drawdown degradation, and exposure research.

### Deliverables

- arbitration report;
- fixed notional vs fixed leverage vs fixed risk vs adaptive sizing;
- 0.25x–5x exposure tables;
- daily target analysis.

### Gate

Adaptive sizing must not pass solely by increasing risk.

---

## Phase 11 — Full Nested Walk-Forward Adaptive Simulation

### Objective

Simulate model and policy updates exactly as they would have occurred through time.

### Deliverables

Per fold:

- frozen train/validation artifacts;
- test decisions;
- lane contributions;
- policy contributions;
- health transitions;
- no-trade rate;
- daily target metrics;
- calibration.

### Gate

All test periods are untouched until their turn.

---

## Phase 12 — Stress, Ablation, and Generalization

### Objective

Challenge costs, fills, latency, trail timing, reversal timing, leverage, and architecture complexity.

### Deliverables

- cost stress;
- fill removal;
- delay;
- two-tick cross;
- stop slippage;
- parameter perturbation;
- block bootstrap;
- model ablation;
- BTCUSDC generalization;
- best/worst month removal.

### Gate

Remove components that do not justify their complexity.

---

## Phase 13 — Frozen 180-Day Sealed Holdout

### Objective

Open the final holdout exactly once after a frozen manifest is approved.

### Deliverables

- signed/frozen policy manifest;
- holdout access log;
- holdout decision ledger;
- final metrics;
- final truth label.

### Gate

No post-holdout parameter changes can be called validation of the same system.

---

## Phase 14 — Shadow Research Package and Final Handoff

### Objective

Package the frozen research policy for delayed or newly downloaded historical shadow runs, without Testnet or live trading.

### Deliverables

- frozen policy YAML;
- lane registry;
- model manifest;
- decision schema;
- risk policy;
- daily report command;
- final HTML and Markdown reports;
- reproducibility instructions.

### Gate

A new environment can reproduce the final results from manifests and commands.


---


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


---


# 09 — Reporting and Final Handoff

## 1. Required reports

```text
reports/phase_01/DATA_QUALITY_REPORT.html
reports/phase_02/EXECUTION_ENGINE_REPORT.html
reports/phase_03/L1_BASELINE_REPORT.html
reports/phase_04/LANE_LIBRARY_REPORT.html
reports/phase_05/ENTRY_PROFILE_REPORT.html
reports/phase_06/EXIT_POLICY_REPORT.html
reports/phase_07/LANE_QUALIFICATION_REPORT.html
reports/phase_08/REGIME_ROUTER_REPORT.html
reports/phase_09/META_HEALTH_REPORT.html
reports/phase_10/RISK_LEVERAGE_REPORT.html
reports/phase_11/NESTED_WALK_FORWARD_REPORT.html
reports/phase_12/STRESS_ABLATION_REPORT.html
reports/phase_13/HOLDOUT_REPORT.html
reports/final/ADAPTIVE_SYSTEM_REPORT.html
reports/final/ADAPTIVE_SYSTEM_REPORT.md
reports/final/FINAL_RECOMMENDATION.md
```

## 2. Final report first page

Must show:

- final label;
- data range;
- sealed holdout range;
- initial equity;
- total OOS trades;
- OOS WR;
- OOS net PnL;
- expectancy;
- PF;
- max drawdown;
- average calendar-day PnL;
- Target A/B/Stretch status;
- effective leverage distribution;
- no-trade rate;
- moderate stress result;
- fill-drop result;
- BTC generalization result.

## 3. Required decompositions

- lane;
- direction;
- regime;
- entry profile;
- stop profile;
- profit profile;
- trail profile;
- emergency profile;
- exit reason;
- notional;
- effective leverage;
- month;
- fold;
- time of day;
- cost component;
- fill model.

## 4. Adaptive explainability

Every official decision must be explainable with:

```text
decision_time
regime probabilities
eligible lanes
raw signals
meta outputs
lane health snapshots
state
suppressed alternatives
selected lane or NO_TRADE
policy package
risk budget
notional
effective leverage
reason codes
```

## 5. Final recommendation categories

- Continue to later Testnet design.
- Continue research only.
- Keep selected lanes shadow-only.
- Retire failed lanes.
- Do not proceed because no system passed.
- Blocked by data or execution validity.

## 6. Reproducibility

Final handoff must include:

- exact commands;
- environment lock;
- Git SHA;
- data hashes;
- config hashes;
- model hashes;
- policy hashes;
- random seed;
- holdout manifest;
- output manifest.

A clean environment must be able to reproduce the final result.


---


# 10 — Decision and Ledger Contracts

## 1. Decision ledger minimum fields

```text
decision_id
decision_time_utc
data_cutoff_utc
symbol
regime_id
regime_probabilities_json
unknown_probability
candidate_lane_ids
eligible_lane_ids
raw_signal_ids
meta_scores_json
lane_health_snapshot_ids
selected_lane_id
selected_direction
selected_entry_profile
selected_stop_profile
selected_profit_profile
selected_break_even_profile
selected_trail_profile
selected_emergency_profile
selected_time_exit_profile
risk_budget_usdc
notional_usdc
effective_leverage
decision
reason_codes
policy_version
model_version
config_hash
data_hash
```

`decision` is one of:

```text
ENTER
NO_TRADE
SUPPRESS
RISK_BLOCK
DATA_BLOCK
```

## 2. Signal ledger

```text
signal_id
lane_id
symbol
direction
signal_time_utc
feature_cutoff_utc
regime_snapshot_id
signal_strength
entry_reference_price
invalidation_price
tags
feature_version
```

## 3. Order ledger

```text
order_intent_id
signal_id
decision_id
side
order_type
limit_price
quantity
notional
activation_time
expiry_time
reprice_count
status
```

## 4. Fill ledger

```text
fill_id
order_intent_id
fill_time
price
quantity
liquidity_role
fee_rate
fee_usdc
slippage_bps
fill_model
```

## 5. Position-event ledger

```text
position_id
event_id
event_time
previous_state
new_state
event_type
trigger
price
quantity
stop_price
target_price
mfe_r
mae_r
regime_id
policy_version
```

## 6. Trade ledger

```text
trade_id
position_id
lane_id
direction
entry_time
exit_time
entry_vwap
exit_vwap
quantity
gross_pnl
entry_fee
exit_fee
slippage_cost
funding_pnl
net_pnl
mfe
mae
holding_minutes
exit_reason
entry_profile
stop_profile
profit_profile
trail_profile
emergency_profile
notional
effective_leverage
fold_id
```

## 7. Lane health ledger

```text
snapshot_id
effective_time
data_cutoff
lane_id
state_before
state_after
health_score
weight
sample_count
shrunk_expectancy
profit_factor
win_rate
drawdown
fill_quality
stress_penalty
concentration_penalty
reason_codes
```

## 8. Machine-readable final decision

The final `decision.json` must include:

```text
project_version
label
failure_codes
data_range
holdout_range
primary_metrics
daily_target_metrics
stress_metrics
generalization_metrics
selected_components
retired_components
limitations
artifact_hashes
```
