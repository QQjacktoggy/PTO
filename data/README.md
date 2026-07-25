# Data Governance

This directory is the boundary for research datasets. Phase 0 does not download
market data.

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
