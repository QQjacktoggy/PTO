# Phase 1：公開歷史資料取得與品質閘門報告

**日期：** 2026-07-25
**實作版本：** `8981abea9f60191843232fe426daeb97bf2a4e65`
**Gate：** `PASS`

## 結論

Phase 1 已完成。管線透過 Binance Vision 取得 ETHUSDC 與 BTCUSDC 的真實
USD-M Futures 歷史資料，逐檔驗證官方 SHA-256，正規化為 1m 與 funding
資料，並只由完整且連續的視窗產生 5m、15m、1h Kline。

研究資料窗固定為 2024-01-05 00:00:00 UTC 至
2025-06-30 23:59:59.999 UTC，共 543 個完整 UTC 日，超過 540 日最低要求。
一般研究 CLI 會在網路請求前拒絕超出此資料窗的日期，2026 holdout 仍為
`SEALED`，本次未讀取。

## 真實資料證據

| 市場 | 1m | Funding | 5m | 15m | 1h | Critical QA |
|---|---:|---:|---:|---:|---:|---:|
| ETHUSDC | 781,920 | 1,629 | 156,384 | 52,128 | 13,032 | 0 |
| BTCUSDC | 781,920 | 1,629 | 156,384 | 52,128 | 13,032 | 0 |

兩個 1m dataset 均從 `1704412800000` 到 `1751327940000`。新版 validator
逐一檢查首尾分鐘、連續性、排序、重複、symbol、interval、UTC boundary、
close time、OHLCV 有限值、正價格、非負成交量，以及 derived parity。

| Artifact | SHA-256 |
|---|---|
| ETHUSDC 1m | `94d75c471ba66a75c3db5d128c2c96e22e61e4e68e85689fe712259e7a8ee78a` |
| ETHUSDC funding | `27fba41eccbcd28ced67f54c440a9038698194212f4333beac6f2558d7793d46` |
| BTCUSDC 1m | `1223cb858df6ad59114adaa6fe6b7549bd1b2eba020f4a8a1fce7ba3326c78a5` |
| BTCUSDC funding | `54b7bd9d72f58ff74448db5ec001d419df0af8829442abfbaff6d0554bfcf7c4` |

大型 raw／normalized 行情不提交 Git。Git 追蹤
`data/manifests/evidence-index.json`，其中索引 72 個逐月 raw archive manifest
與 14 個 dataset manifest；每項均記錄路徑、bytes 與 checksum，供外部稽核。

## 第一輪 Code Review 修正

本輪已處理全部 18 條 findings：

- 將 acquisition 限定於治理設定的日期與 ETHUSDC／BTCUSDC universe；
- critical QA 時 fail closed、回傳非零並標記 dataset 為 `REJECTED`；
- 驗證請求區間的第一根與最後一根 1m；
- `make phase1` 綁定真實資料、manifest、checksum 與 derived parity；
- 每次輸出嚴格裁切請求區間，避免混用舊 normalized 資料；
- 在去重前拒絕 identical／conflicting duplicate；
- REST raw response 使用逐檔 manifest，不再由固定檔名覆寫 lineage；
- Gate 記錄 repository 內可解析的 implementation Git SHA；
- Vision ZIP 以暫存檔、fsync、checksum、atomic rename 發布；
- current exchangeInfo 明確標為非 point-in-time provenance；
- `data validate` 驗證所有必要 artifact、schema、rows、bytes 與 checksum；
- 每個 Vision archive 保存 URL、member、month、bytes 與官方 checksum；
- 已驗證 archives 可逐檔重用，支援 partial-failure recovery；
- 拒絕 Infinity、NaN、非正價格及無效 funding mark price；
- 驗證 ZIP member filename 與每筆資料所屬月份；
- dataset manifest 新增 market、file size、quality status、source artifacts；
- evidence index 納入版本控制；
- 新增對應回歸測試。

## 驗證結果

| 檢查 | 結果 | 證據 |
|---|---:|---|
| Config validation | PASS | Governed YAML 與 schema 有效 |
| Ruff lint／format | PASS | 32 files |
| Strict mypy | PASS | 25 source files |
| Pytest | PASS | 48/48 |
| Binance Vision | PASS | 72/72 checksum manifests |
| 真實 1m QA | PASS | 1,563,840 rows；critical 0 |
| Derived parity | PASS | 5m／15m／1h 全部重算一致 |
| Artifact validation | PASS | required files、rows、bytes、checksum |
| Holdout | SEALED | 未嘗試存取 |

正式 Gate 指令：

```text
make phase1
```

該 target 依序執行 config、Ruff、mypy、pytest、`pto data validate`，最後以
同一次 validation 結果原子產生 `reports/phase_01/gate.json`。缺檔、checksum
mismatch、derived mismatch 或任一 critical issue 都會輸出 `FAIL` 並回傳非零。

## Gate 決策

`PASS`。Phase 1 已符合真實資料、540 日歷史、完整性、可重現性與 sealed
holdout 的要求。PR #2 仍須完成第二輪 Code Review，確認沒有新的 P1／P2
後才可合併；本報告不構成策略獲利聲明。
