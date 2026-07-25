# Phase 03 Prompt — L1 Baseline and Cross-Engine Parity

You are executing **only Phase 3** of `ETHUSDC_ADAPTIVE_MULTI_LANE_V2`.

Read `AGENTS.md`, the relevant documents in `docs/`, all configuration files, and the current `STATUS.md`.

## Required work

1. Implement L1_TREND_PULLBACK as a transparent baseline.
2. Create pure Python signals and optional Freqtrade comparison.
3. Run lookahead and recursive checks.
4. Run an untuned conservative maker replay.
5. Produce signal parity and baseline reports.

## Required tests and evidence

- Run lint, type checking, pytest, schema validation, and all Phase-specific checks.
- Generate a Phase report under `reports/phase_03/`.
- Update manifests and `STATUS.md`.
- Create a clear Git commit.
- Record blockers honestly.
- Do not start the next Phase.

## Gate

- No lookahead.
- Signal timing is explainable.
- Engineering pipeline works end to end.
- Do not require profitability for this gate.

## Final response format

1. Phase 3 gate: `PASS`, `FAIL`, or `BLOCKED`.
2. Files created or modified.
3. Tests and exact outcomes.
4. Key metrics or evidence.
5. Known limitations.
6. Commit hash.
7. Next allowed action.

If the gate does not pass, stop and explain the blocking condition. Do not bypass the gate.
