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
