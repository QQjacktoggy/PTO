# Phase 0 Report — Governance, Scaffold, and Holdout Guard

## Gate status

**PASS — local and remote Phase 0 gates completed**

The required governance gate passed locally and in GitHub Actions on Python
3.11.

## Objective

Establish the repository boundaries, typed Python scaffold, configuration
validation, immutable experiment manifests, sealed-holdout guard, CLI, and
repeatable quality checks required by the project plan.

## Scope boundaries

- Historical public-data research only.
- No exchange credentials, Testnet, live trading, or order submission.
- No strategy implementation or performance claims in Phase 0.
- No full market-data download in Phase 0.
- The final 180-day holdout remains sealed and must be denied by default.

## Required evidence

| Check | Required command or evidence | Status | Exact outcome |
|---|---|---|---|
| Install | `make setup` | PASS | Locked `uv` environment synchronized |
| Config validation | `make validate-config` | PASS | All seven YAML files and cross-file contracts valid |
| Lint/format | `make lint` | PASS | Ruff check passed; 24 files formatted |
| Type checking | `make typecheck` | PASS | Strict mypy: 18 source files, zero issues |
| Tests | `make test` | PASS | 32 passed in 0.52 seconds |
| Holdout denial | Automated default-denial tests | PASS | Missing flag/manifest, tampering, and redacted audit covered |
| Determinism/versioning | Config hash, lock, registry, manifest tests | PASS | Config hash `c4b9ffcd...00f37`; implementation commit `5d523a4` |
| CI | GitHub Actions Python 3.11 quality gate | PASS | Run 30141370410; all steps successful |

## Artifacts

- Governance and configuration contracts: present in the repository.
- Python scaffold and validation implementation: complete.
- Machine-readable gate: `reports/phase_00/gate.json`.
- Data governance boundary: `data/README.md`.
- Implementation commit: `5d523a4f1d218d610386c244aef7cd8fcad484a8`.

## Data and holdout state

- Market-data acquisition performed: **No**.
- Raw market data added to Git: **No**.
- Holdout opened: **No**.
- Holdout state: **SEALED**.

## Evidence details

- Project package: `pto-quant 0.1.0`.
- Locked environment: `uv.lock`.
- PyYAML: `6.0.3`.
- jsonschema: `4.26.0`.
- Ruff: `0.16.0`.
- mypy: `1.20.2`.
- pytest: `8.4.2`.
- Governed config hash:
  `c4b9ffcd0e6a0667da694ec76b75f233969f1fd4694b379f7390e80558c00f37`.
- Holdout coordinates are absent from normal CLI output and denial messages.
- No market data was downloaded and no strategy code was implemented.

## Known limitations

- Filesystem append-only behavior is enforced by the application contract; an
  operating-system administrator can still alter local files.
- Phase 0 validates governance and reproducibility only, not market-data
  availability, execution correctness, or profitability.

## Next allowed action

Phase 1 public-data acquisition and QA may begin using only
`prompts/PHASE_01_PROMPT.md`. Strategy implementation, parameter optimization,
and holdout access remain prohibited.
