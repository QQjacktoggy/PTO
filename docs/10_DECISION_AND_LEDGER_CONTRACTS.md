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
