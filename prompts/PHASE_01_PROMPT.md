# Phase 01 Prompt — Data Acquisition and QA

You are executing **only Phase 1** of `ETHUSDC_ADAPTIVE_MULTI_LANE_V2`.

Read `AGENTS.md`, the relevant documents in `docs/`, all configuration files, and the current `STATUS.md`.

## Required work

1. Implement idempotent public-data download for ETHUSDC and BTCUSDC.
2. Download or prepare resumable daily/monthly 1m klines, funding, and metadata.
3. Normalize to UTC and create immutable raw manifests and checksums.
4. Implement duplicate, gap, OHLC, volume, timezone, and symbol QA.
5. Resample 1m to 5m, 15m, and 1h using completed windows only.
6. Create representative small fixtures for CI.
7. Generate a data-quality HTML/Markdown report.

## Required tests and evidence

- Run lint, type checking, pytest, schema validation, and all Phase-specific checks.
- Generate a Phase report under `reports/phase_01/`.
- Update manifests and `STATUS.md`.
- Create a clear Git commit.
- Record blockers honestly.
- Do not start the next Phase.

## Gate

- No critical QA blocker.
- Download is resumable and does not duplicate rows.
- Validation exits non-zero on critical defects.
- Manifests include source, range, rows, checksum, Git SHA, and config hash.

## Final response format

1. Phase 1 gate: `PASS`, `FAIL`, or `BLOCKED`.
2. Files created or modified.
3. Tests and exact outcomes.
4. Key metrics or evidence.
5. Known limitations.
6. Commit hash.
7. Next allowed action.

If the gate does not pass, stop and explain the blocking condition. Do not bypass the gate.
