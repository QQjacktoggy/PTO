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
