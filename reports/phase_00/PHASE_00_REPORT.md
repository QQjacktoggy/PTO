# Phase 0 Report — Governance, Scaffold, and Holdout Guard

## Gate status

**IN_PROGRESS — final result PENDING**

Phase 0 has not yet passed. This report is a working evidence record and must
not be interpreted as proof that the repository is ready for Phase 1.

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
| Install | `python -m pip install -e ".[dev]"` | PENDING | Not yet recorded |
| Config validation | `make validate-config` | PENDING | Not yet recorded |
| Lint/format | `make lint` | PENDING | Not yet recorded |
| Type checking | `make typecheck` | PENDING | Not yet recorded |
| Tests | `make test` | PENDING | Not yet recorded |
| Holdout denial | Automated test proving default denial | PENDING | Not yet recorded |
| Determinism/versioning | Seed and run-version evidence | PENDING | Not yet recorded |
| CI | GitHub Actions Python 3.11 quality gate | PENDING | Not yet run |

## Artifacts

- Governance and configuration contracts: present in the repository.
- Python scaffold and validation implementation: in progress.
- Machine-readable gate: `reports/phase_00/gate.json`.
- Data governance boundary: `data/README.md`.
- Phase commit: pending.

## Data and holdout state

- Market-data acquisition performed: **No**.
- Raw market data added to Git: **No**.
- Holdout opened: **No**.
- Holdout state: **SEALED**.

## Blockers

The full validation suite has not yet completed and no Phase 0 commit has been
recorded. Therefore the gate must remain pending.

## Next allowed action

Complete the Phase 0 implementation, execute every required check, record exact
outcomes and hashes, and update this report plus `gate.json` and `STATUS.md`.
Phase 1 may begin only after all required checks pass and the Phase 0 work is
committed.
