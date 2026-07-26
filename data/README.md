# Data Governance

This directory is the boundary for research datasets. Phase 1 provides the
public-data pipeline; downloaded data remains local and ignored by Git.

## Phase 1 commands and layout

```bash
uv run pto data acquire \
  --start 2024-01-01T00:00:00Z \
  --end 2024-01-31T23:59:59.999Z
uv run pto data validate
```

The default acquisition covers configured `ETHUSDC` and `BTCUSDC`. It requires
no credentials. Re-running resumes after the newest normalized 1m row, merges
by timestamp, and does not duplicate rows.

```text
data/raw/binance_futures/<SYMBOL>/        immutable JSON responses
data/normalized/<SYMBOL>/1m.csv           normalized UTC source series
data/normalized/<SYMBOL>/{5m,15m,1h}.csv  completed-window resamples
data/normalized/<SYMBOL>/funding.csv
data/normalized/<SYMBOL>/metadata.json
data/normalized/<SYMBOL>/qa.json
data/manifests/<SYMBOL>/*.manifest.json
```

Validation exits non-zero for empty data, gaps, duplicates, wrong symbols or
intervals, non-UTC boundaries, bad close times, invalid OHLC, and negative
volume or trade counts.

## Raw data is immutable

Once acquired and checksum-verified, files under `data/raw/` are append-only
research inputs. Never edit, overwrite, repair, or silently impute a raw file in
place. Corrections must create a new version with a new manifest and checksum;
the rejected or superseded input remains traceable.

Every acquired dataset must record its source, symbol, market, interval,
inclusive time range, acquisition time, row count, file size, checksum, and
quality status in `data/manifests/`.

## Holdout is sealed

The final 180-day holdout is inaccessible to ordinary research commands.
Holdout dates, files, derived features, labels, and metrics must not be read
during development or tuning. Access requires the separately guarded,
frozen-manifest workflow defined by the project governance. A failed or missing
authorization must deny access rather than fall back to an unguarded path.

Do not place holdout data in fixtures, notebooks, caches, CI artifacts, logs, or
ordinary report outputs.

## Git stores metadata, not large datasets

Git may contain directory placeholders, small synthetic test fixtures, schemas,
and dataset manifests. It must not contain downloaded candles, funding history,
normalized market tables, feature stores, model caches, or holdout files.
Large reproducible data artifacts belong in the configured external artifact
store and are referenced by immutable checksums.

Suggested runtime layout:

```text
data/
  raw/          # immutable downloaded inputs; ignored by Git
  normalized/   # reproducible transforms; ignored by Git
  features/     # point-in-time feature tables; ignored by Git
  holdout/      # sealed; ignored by Git and guarded in code
  manifests/    # small versioned metadata and checksums
```

No data pipeline may silently cross from the research range into the sealed
holdout range.
