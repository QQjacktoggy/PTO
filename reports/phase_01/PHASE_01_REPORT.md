# Phase 1：公開歷史資料取得與品質閘門報告

**日期：** 2026-07-26
**實作版本：** `933c7ff07574700e4aad45942c547a1b225c0d05`
**Gate：** `PASS`

## 結論

Phase 1 的資料管線與第二輪 review 修正已完成。管線使用 Binance Vision
USD-M Futures 月檔取得 ETHUSDC 與 BTCUSDC，逐檔驗證官方 SHA-256，保存
不可覆寫的 raw archive evidence，產生 1m、funding 與完整連續的 5m、15m、1h
資料。

普通研究命令的可信任資料窗固定為 2024-01-05 00:00:00 UTC 至
2025-06-30 23:59:59.999 UTC，共 543 個完整 UTC 日；邊界與市場 universe
由可信任 bootstrap 固定，不可透過 `--config-dir` 改寫。2026 sealed holdout
仍未讀取。

## 真實資料證據

| 市場 | 1m | Funding | 5m | 15m | 1h | Critical QA |
|---|---:|---:|---:|---:|---:|---:|
| ETHUSDC | 781,920 | 1,629 | 156,384 | 52,128 | 13,032 | 0 |
| BTCUSDC | 781,920 | 1,629 | 156,384 | 52,128 | 13,032 | 0 |

兩個 1m dataset 均從 `1704412800000` 到 `1751327940000`。validator 由
治理窗口提供 expected range，並檢查首尾分鐘、543 日最低歷史、連續性、排序、
重複、symbol、interval、UTC boundary、close time、OHLCV 有限值、正價格、
非負成交量、funding 時間／symbol／數值及 derived parity。

主要 artifact SHA-256：

| Artifact | SHA-256 |
|---|---|
| ETHUSDC 1m | `94d75c471ba66a75c3db5d128c2c96e22e61e4e68e85689fe712259e7a8ee78a` |
| ETHUSDC funding | `27fba41eccbcd28ced67f54c440a9038698194212f4333beac6f2558d7793d46` |
| BTCUSDC 1m | `1223cb858df6ad59114adaa6fe6b7549bd1b2eba020f4a8a1fce7ba3326c78a5` |
| BTCUSDC funding | `54b7bd9d72f58ff74448db5ec001d419df0af8829442abfbaff6d0554bfcf7c4` |

大型 raw／normalized 行情不提交 Git。`data/manifests/evidence-index.json`
索引 72 個逐月 raw archive manifest 與 14 個 dataset manifest，共 86 個項目；
每個外層 checksum 都由目前檔案重新計算，dataset manifest 的 `source_artifacts`
會進一步驗證對應 raw ZIP 的存在、bytes 與 payload SHA-256。

## 第二輪 Code Review 修正

本輪已處理全部 10 條未解決 findings（4 個 P1、6 個 P2）：

- 使用可信任 `HoldoutGuard` 固定 Phase 1 日期窗口與 `ETHUSDC`／`BTCUSDC`
  universe，拒絕可編輯 config 繞過 sealed holdout。
- Gate 不再相信 manifest 自行宣告的短區間；兩個市場都必須通過完整 543 日
  治理窗口與 540 日最低歷史要求。
- funding 輸出嚴格裁切至本次請求，並驗證時間、symbol、排序、非空與數值邊界。
- Gate 會以目前可解析的 implementation Git SHA 重建 evidence index、gate 與
  phase manifest 的 checksum chain。
- validator 會沿 `source_artifacts` 驗證 raw manifest 與 Binance Vision ZIP；
  缺 ZIP、bytes 不符或 checksum 不符都會使 Gate FAIL。
- Vision ZIP sidecar manifest 使用暫存檔、fsync 與 atomic rename；空白／損壞
  sidecar 可安全重試。
- NaN／Infinity 會產生受控 critical QA，不會進入 Decimal 排序或比較而拋出例外。
- REST resume 會補足缺少的前綴、尾端與中間缺口。
- 只保留在請求截止時間前已完成的最後一根 Kline，排除 cutoff 後資料。

## 驗證結果

| 檢查 | 結果 | 證據 |
|---|---:|---|
| Config validation | PASS | Governed YAML 與 schema 有效 |
| Ruff lint／format | PASS | 32 files |
| Strict mypy | PASS | 25 source files |
| Pytest | PASS | 53/53 |
| Binance Vision | PASS | 72/72 checksum manifests |
| 真實 1m QA | PASS | 1,563,840 rows；critical 0 |
| Funding QA | PASS | 3,258 rows；時間與 symbol 均符合窗口 |
| Derived parity | PASS | 5m／15m／1h 全部重算一致 |
| Evidence chain | PASS | 86 個外層 manifest checksum；gate／index／phase manifest 一致 |
| Holdout | SEALED | 未嘗試存取 |

正式 Gate 指令：

```text
make phase1
```

`phase1` 的 Gate 會直接執行同一套完整資料 validation；缺檔、短歷史、config
hash 不一致、raw ZIP 缺失／checksum mismatch、funding 越界、derived mismatch
或任一 critical issue 都會產生 `FAIL` 並回傳非零，不會由較早的單元測試結果
掩蓋資料失敗。

## Gate 決策

目前 Phase 1 Gate 為 `PASS`。PR #2 仍維持 Draft，待第三輪 Code Review 確認
本輪 10 項修正後才決定是否合併；本報告不構成策略獲利或實盤準備聲明，Phase 2
尚未開始。
