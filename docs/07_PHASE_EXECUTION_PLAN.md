# 07 — Phase Execution Plan

## Universal phase gate

Every Phase must produce:

1. Code or governance artifacts.
2. Tests and validation output.
3. A phase report.
4. Updated manifests.
5. Updated `STATUS.md`.
6. A clear Git commit.
7. A machine-readable gate result.

No phase may be marked complete based only on prose.

---

## Phase 0 — Governance, Scaffold, and Holdout Guard

### Objective

Establish project boundaries, schemas, CLI, tests, experiment registry, and a technically enforced sealed holdout.

### Deliverables

- repository structure;
- `AGENTS.md`;
- Python project files;
- config schemas;
- experiment registry;
- holdout guard;
- `STATUS.md`;
- Phase 0 report.

### Gate

- config validates;
- holdout access is denied by default;
- lint/typecheck/test commands run;
- deterministic seed and version recording exist.

---

## Phase 1 — Data Acquisition and QA

### Objective

Build an idempotent, resumable ETHUSDC and BTCUSDC public-data pipeline.

### Deliverables

- raw and normalized 1m data;
- funding data;
- metadata;
- checksums;
- gap and OHLC QA;
- 5m/15m/1h resampling;
- data-quality report.

### Gate

No unresolved critical data blocker.

---

## Phase 2 — Point-in-Time Features and Replay Engine

### Objective

Build lag-safe features, ledgers, maker fill model, fees, funding, and the position state machine.

### Deliverables

- feature registry;
- replay engine;
- state-transition tests;
- fill and PnL parity;
- same-minute priority tests;
- execution report.

### Gate

Deterministic replay, complete ledger traceability, zero unresolved critical invariants.

---

## Phase 3 — L1 Baseline and Cross-Engine Parity

### Objective

Implement `L1_TREND_PULLBACK` as the engineering baseline.

### Deliverables

- pure Python signal engine;
- optional Freqtrade baseline;
- signal parity report;
- lookahead and recursive tests;
- untuned conservative replay.

### Gate

Engineering correctness; profitability is not required yet.

---

## Phase 4 — Multi-Lane Library

### Objective

Implement L2 through L7 independently.

### Deliverables

For each lane:

- formal specification;
- signal tags;
- unit tests;
- leakage tests;
- untuned baseline;
- data/sample warnings.

### Gate

Each lane is distinguishable and reproducible. No copied lane with cosmetic renaming.

---

## Phase 5 — Entry Policy Lab

### Objective

Evaluate E0–E5 without exit-policy overfitting.

### Deliverables

- fill-rate tables;
- adverse-selection analysis;
- missed-winner analysis;
- entry profile OOS scorecards;
- retained profile registry.

### Gate

At most two qualified entry profiles per lane.

---

## Phase 6 — Exit and Trade-Management Lab

### Objective

Evaluate S0–S3, P0–P2, break-even, T0–T6, R0–R5, and time exits.

### Deliverables

- module-level OOS tests;
- trail benefit/harm by lane and regime;
- emergency-exit saved-loss versus sacrificed-profit analysis;
- bounded retained policy set.

### Gate

No full Cartesian optimization. Retained policies are limited and preregistered.

---

## Phase 7 — Individual Lane Walk-Forward Qualification

### Objective

Determine which lanes and lane-policy packages have positive OOS value.

### Default split

```text
Train 12 months
Validation 3 months
Test 3 months
Step 3 months
Embargo 7 days
Final holdout 180 days
```

### Deliverables

- fold reports;
- lane admission states;
- rejected-lane reasons;
- parameter plateau evidence.

### Gate

Only qualified lanes enter the router.

---

## Phase 8 — Regime System and Static Router

### Objective

Build the rule-based regime baseline, optional probabilistic challenger, and static eligibility map.

### Deliverables

- regime timeline;
- transition matrix;
- lane × regime matrix;
- static router comparisons;
- unknown and chaotic behavior.

### Gate

Router must improve or justify itself against simpler baselines.

---

## Phase 9 — Meta Model and Adaptive Lane Health

### Objective

Build calibrated signal filtering and delayed daily lane-health updates.

### Deliverables

- point-in-time training table;
- logistic baseline;
- optional boosted challenger;
- calibration reports;
- lane health ledger;
- state-transition tests.

### Gate

Expectancy improves without meaningless coverage collapse; health is leakage-safe.

---

## Phase 10 — Conflict Arbitration, Risk Budget, and Leverage

### Objective

Combine eligible signals, position constraints, daily risk, drawdown degradation, and exposure research.

### Deliverables

- arbitration report;
- fixed notional vs fixed leverage vs fixed risk vs adaptive sizing;
- 0.25x–5x exposure tables;
- daily target analysis.

### Gate

Adaptive sizing must not pass solely by increasing risk.

---

## Phase 11 — Full Nested Walk-Forward Adaptive Simulation

### Objective

Simulate model and policy updates exactly as they would have occurred through time.

### Deliverables

Per fold:

- frozen train/validation artifacts;
- test decisions;
- lane contributions;
- policy contributions;
- health transitions;
- no-trade rate;
- daily target metrics;
- calibration.

### Gate

All test periods are untouched until their turn.

---

## Phase 12 — Stress, Ablation, and Generalization

### Objective

Challenge costs, fills, latency, trail timing, reversal timing, leverage, and architecture complexity.

### Deliverables

- cost stress;
- fill removal;
- delay;
- two-tick cross;
- stop slippage;
- parameter perturbation;
- block bootstrap;
- model ablation;
- BTCUSDC generalization;
- best/worst month removal.

### Gate

Remove components that do not justify their complexity.

---

## Phase 13 — Frozen 180-Day Sealed Holdout

### Objective

Open the final holdout exactly once after a frozen manifest is approved.

### Deliverables

- signed/frozen policy manifest;
- holdout access log;
- holdout decision ledger;
- final metrics;
- final truth label.

### Gate

No post-holdout parameter changes can be called validation of the same system.

---

## Phase 14 — Shadow Research Package and Final Handoff

### Objective

Package the frozen research policy for delayed or newly downloaded historical shadow runs, without Testnet or live trading.

### Deliverables

- frozen policy YAML;
- lane registry;
- model manifest;
- decision schema;
- risk policy;
- daily report command;
- final HTML and Markdown reports;
- reproducibility instructions.

### Gate

A new environment can reproduce the final results from manifests and commands.
