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
