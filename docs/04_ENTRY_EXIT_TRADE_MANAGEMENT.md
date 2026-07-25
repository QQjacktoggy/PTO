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
