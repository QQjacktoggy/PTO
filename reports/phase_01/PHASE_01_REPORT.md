# Phase 1 — Data Acquisition and QA Report

**Date:** 2026-07-25
**Implementation commit:** `f5ded0a234f2449ecc11fb6fef3948a083f154db`
**Gate:** `PASS`

## Outcome

Phase 1 is complete. The governed pipeline acquired checksum-verified real Binance
USD-M Futures history for ETHUSDC and BTCUSDC through Binance Vision, normalized
the data, generated funding and archive-provenance metadata, derived only complete
contiguous higher-timeframe candles, and passed the fail-closed quality gate.

The acquisition window is 2024-01-05 00:00:00 UTC through 2025-06-30 23:59:59.999
UTC: 543 complete calendar days. It exceeds the required 540 research days and is
entirely before the sealed 180-day final holdout. No 2026 market data was read.

## Real-data evidence

| Symbol | 1m rows | Funding rows | 5m rows | 15m rows | 1h rows | Critical QA |
|---|---:|---:|---:|---:|---:|---:|
| ETHUSDC | 781,920 | 1,629 | 156,384 | 52,128 | 13,032 | 0 |
| BTCUSDC | 781,920 | 1,629 | 156,384 | 52,128 | 13,032 | 0 |

Both normalized 1m datasets begin at `1704412800000` and end at
`1751327940000`, with no gaps, duplicates, ordering defects, boundary defects,
close-time defects, symbol mismatch, invalid OHLC, or negative volume/trade count.

### Normalized checksums

| Artifact | SHA-256 |
|---|---|
| ETHUSDC 1m | `94d75c471ba66a75c3db5d128c2c96e22e61e4e68e85689fe712259e7a8ee78a` |
| ETHUSDC funding | `27fba41eccbcd28ced67f54c440a9038698194212f4333beac6f2558d7793d46` |
| BTCUSDC 1m | `1223cb858df6ad59114adaa6fe6b7549bd1b2eba020f4a8a1fce7ba3326c78a5` |
| BTCUSDC funding | `54b7bd9d72f58ff74448db5ec001d419df0af8829442abfbaff6d0554bfcf7c4` |

The local raw evidence contains 72 immutable ZIP files: monthly kline and funding
archives for 18 months and two symbols. Every archive was checked against its
official Binance Vision `.CHECKSUM` before parsing. Raw and normalized market data
remain intentionally excluded from Git.

## Implemented

- Binance Vision monthly archive transport with SHA-256 verification;
- official kline and funding CSV parsing from ZIP without API credentials;
- bounded UTC acquisition for ETHUSDC and BTCUSDC;
- immutable raw ZIP retention and retry integrity checks;
- normalized 1m and funding CSV outputs;
- archive-provenance metadata;
- completed, contiguous-window-only 5m, 15m, and 1h resampling;
- gap, duplicate, ordering, boundary, close-time, symbol, interval, OHLC, volume,
  quote-volume, and trade-count QA;
- dataset manifests containing source, range, rows, SHA-256, Git SHA, config hash,
  and acquisition timestamp;
- retained REST transport for permitted environments;
- deterministic fixture coverage for Vision checksum and parsing behavior.

## Verification

| Check | Result | Evidence |
|---|---:|---|
| Config validation | PASS | Governed YAML and schema valid |
| Ruff lint | PASS | 32 files checked |
| Ruff format | PASS | 32 files |
| Strict mypy | PASS | 25 source files |
| Pytest | PASS | 42 passed |
| Binance Vision acquisition | PASS | 72 checksum-verified monthly archives |
| Real 1m QA | PASS | 1,563,840 total rows; 0 critical defects |
| Real resampling | PASS | Exact complete-window row ratios |
| CLI validation | PASS | Exit code 0 for both symbols |
| Holdout | SEALED | Access not attempted |

Acquisition command:

```text
pto data acquire --transport vision \
  --symbol ETHUSDC --symbol BTCUSDC \
  --start 2024-01-05T00:00:00Z \
  --end 2025-06-30T23:59:59.999Z
```

Validation command:

```text
pto data validate --symbol ETHUSDC --symbol BTCUSDC
```

## Gate decision

`PASS`. Phase 1 meets the 540-day minimum history requirement with verified real
market data for both required symbols, zero critical data-quality defects,
reproducible manifests, and a still-sealed holdout. Phase 2 may begin from this
frozen dataset boundary; no profitability claim is made.
