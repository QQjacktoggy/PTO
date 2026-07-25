# 09 — Reporting and Final Handoff

## 1. Required reports

```text
reports/phase_01/DATA_QUALITY_REPORT.html
reports/phase_02/EXECUTION_ENGINE_REPORT.html
reports/phase_03/L1_BASELINE_REPORT.html
reports/phase_04/LANE_LIBRARY_REPORT.html
reports/phase_05/ENTRY_PROFILE_REPORT.html
reports/phase_06/EXIT_POLICY_REPORT.html
reports/phase_07/LANE_QUALIFICATION_REPORT.html
reports/phase_08/REGIME_ROUTER_REPORT.html
reports/phase_09/META_HEALTH_REPORT.html
reports/phase_10/RISK_LEVERAGE_REPORT.html
reports/phase_11/NESTED_WALK_FORWARD_REPORT.html
reports/phase_12/STRESS_ABLATION_REPORT.html
reports/phase_13/HOLDOUT_REPORT.html
reports/final/ADAPTIVE_SYSTEM_REPORT.html
reports/final/ADAPTIVE_SYSTEM_REPORT.md
reports/final/FINAL_RECOMMENDATION.md
```

## 2. Final report first page

Must show:

- final label;
- data range;
- sealed holdout range;
- initial equity;
- total OOS trades;
- OOS WR;
- OOS net PnL;
- expectancy;
- PF;
- max drawdown;
- average calendar-day PnL;
- Target A/B/Stretch status;
- effective leverage distribution;
- no-trade rate;
- moderate stress result;
- fill-drop result;
- BTC generalization result.

## 3. Required decompositions

- lane;
- direction;
- regime;
- entry profile;
- stop profile;
- profit profile;
- trail profile;
- emergency profile;
- exit reason;
- notional;
- effective leverage;
- month;
- fold;
- time of day;
- cost component;
- fill model.

## 4. Adaptive explainability

Every official decision must be explainable with:

```text
decision_time
regime probabilities
eligible lanes
raw signals
meta outputs
lane health snapshots
state
suppressed alternatives
selected lane or NO_TRADE
policy package
risk budget
notional
effective leverage
reason codes
```

## 5. Final recommendation categories

- Continue to later Testnet design.
- Continue research only.
- Keep selected lanes shadow-only.
- Retire failed lanes.
- Do not proceed because no system passed.
- Blocked by data or execution validity.

## 6. Reproducibility

Final handoff must include:

- exact commands;
- environment lock;
- Git SHA;
- data hashes;
- config hashes;
- model hashes;
- policy hashes;
- random seed;
- holdout manifest;
- output manifest.

A clean environment must be able to reproduce the final result.
