# Adaptive Crypto Quant Work Handoff Pack

**版本：** 2.0.0  
**日期：** 2026-07-25  
**主要標的：** Binance USD-M Futures `ETHUSDC`  
**泛化標的：** `BTCUSDC`  
**研究資金基準：** 200 USDC  
**研究範圍：** 公開歷史資料、回測、1m replay、walk-forward、adaptive simulation  
**明確排除：** Testnet、實盤、API Key、真實下單、永久常駐服務

本交接包取代舊版單一 `ETHUSDC_MTF_PULLBACK_MAKER_V1` 計畫。舊策略只保留為：

```text
L1_TREND_PULLBACK
```

新版最終目標是建立一套可稽核的：

```text
Multi-Lane
+ Regime Detection
+ Entry Modulation
+ Adaptive Exit / Trail / Reversal Stop
+ Meta Signal Scoring
+ Lane Health
+ Conflict Arbitration
+ Risk-Based Position Sizing
+ Effective Leverage Research
+ NO_TRADE
```

## 最快開始方式

1. 將本資料夾全部放到新的 GitHub repository 根目錄。
2. 讓 Work／Codex 先閱讀：
   - `AGENTS.md`
   - `ADAPTIVE_QUANT_MASTER_PLAN.md`
   - `docs/07_PHASE_EXECUTION_PLAN.md`
   - `config/*.yaml`
3. 將 `WORK_MASTER_PROMPT.md` 全文貼給 Work。
4. Work 第一輪只執行 Phase 0；不得直接跳到回測或最佳化。
5. 每個 Phase 都依序完成：
   - 實作
   - 測試
   - 報告
   - manifest
   - `STATUS.md`
   - commit
   - gate
6. Gate 未通過時，先修復或明確結案，不得假裝進入下一 Phase。

## 檔案導覽

### 核心入口

- `ADAPTIVE_QUANT_MASTER_PLAN.md`：完整總計畫，適合人類與 Work 通讀。
- `WORK_MASTER_PROMPT.md`：可直接貼給 Work 的起始指令。
- `AGENTS.md`：專案永久治理規則。
- `STATUS_TEMPLATE.md`：Work 建立 `STATUS.md` 時使用。

### 技術文件

- `docs/00_PROJECT_CHARTER.md`
- `docs/01_ARCHITECTURE.md`
- `docs/02_DATA_EXECUTION_VALIDATION.md`
- `docs/03_LANE_LIBRARY.md`
- `docs/04_ENTRY_EXIT_TRADE_MANAGEMENT.md`
- `docs/05_REGIME_META_ADAPTIVE.md`
- `docs/06_RISK_LEVERAGE_TARGETS.md`
- `docs/07_PHASE_EXECUTION_PLAN.md`
- `docs/08_ACCEPTANCE_STRESS_HOLDOUT.md`
- `docs/09_REPORTING_AND_HANDOFF.md`
- `docs/10_DECISION_AND_LEDGER_CONTRACTS.md`

### 設定檔

- `config/research.yaml`
- `config/lanes.yaml`
- `config/regimes.yaml`
- `config/entry_exit_profiles.yaml`
- `config/adaptive_policy.yaml`
- `config/risk_targets.yaml`
- `config/acceptance.yaml`

### Phase 提示

`prompts/PHASE_00_PROMPT.md` 到 `prompts/PHASE_14_PROMPT.md`。

這些提示設計成每個 Phase 可分別貼給 Work，避免單一任務過長，也避免 Work 尚未完成底層正確性就直接最佳化。

## 最終正式輸出標籤

Work 最終只能輸出以下之一：

```text
PASS_TARGET_B
PASS_TARGET_A
PASS_STRETCH
PASS_SURVIVAL
PASS_ADAPTIVE_EV_ONLY
NO_ADAPTIVE_SYSTEM_PASSED
INSUFFICIENT_HISTORY
BLOCKED_BY_DATA_OR_ENGINE
```

其中 `PASS_TARGET_A/B/STRETCH` 必須同時符合 after-cost、OOS、holdout、drawdown、成本與 fill 壓力條件。每日獲利目標是評估結果，不是強迫每天交易的 quota。
