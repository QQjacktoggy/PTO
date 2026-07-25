# Phase 14 Prompt — Shadow Research Package and Final Handoff

You are executing **only Phase 14** of `ETHUSDC_ADAPTIVE_MULTI_LANE_V2`.

Read `AGENTS.md`, the relevant documents in `docs/`, all configuration files, and the current `STATUS.md`.

## Required work

1. Package frozen policies, lane registry, models, manifests, decision schema, and risk policy.
2. Create commands for new historical data, delayed replay, health update, and daily report.
3. Produce final HTML/Markdown reports and reproducibility guide.
4. Do not add Testnet or live trading.

## Required tests and evidence

- Run lint, type checking, pytest, schema validation, and all Phase-specific checks.
- Generate a Phase report under `reports/phase_14/`.
- Update manifests and `STATUS.md`.
- Create a clear Git commit.
- Record blockers honestly.
- Do not start the next Phase.

## Gate

- A clean environment can reproduce final results.
- All final artifacts have hashes.
- Recommendations distinguish research-only, shadow-only, and later deployment candidates.

## Final response format

1. Phase 14 gate: `PASS`, `FAIL`, or `BLOCKED`.
2. Files created or modified.
3. Tests and exact outcomes.
4. Key metrics or evidence.
5. Known limitations.
6. Commit hash.
7. Next allowed action.

If the gate does not pass, stop and explain the blocking condition. Do not bypass the gate.
