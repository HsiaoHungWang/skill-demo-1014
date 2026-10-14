---
name: hello-skills
description: 依台北目前時段，用使用者指定的語言打招呼，並產出一張含週末倒數與鼓勵訊息的問候卡。當使用者說「哈囉」「打招呼」「早安」「做一張問候卡」「還有幾天放假」「離週末還有多久」「hello skills」或要求測試 Skill 時使用，即使沒有明說要問候卡也一樣。若使用者只是要翻譯一句問候語，不適用。
---

# Hello Skills

## 流程
1. 執行 `python scripts/now.py`，取得：
   - `datetime`：台北目前日期時間
   - `period`：目前時段（morning／afternoon／evening）
2. 執行 `python scripts/weekend.py`，取得：
   - `saturday`：本週六的日期
   - `days_left`：距離週末還有幾天（0 代表今天就是週末）
   - `level`：遠近等級
3. 判斷使用者要的語言（沒有指定就用繁體中文）
4. 依 `period`，到 `references/greetings.md` 查問候語與結尾祝福語
5. 依 `level`，到 `references/weekend-messages.md` 挑一句鼓勵訊息，把 {N} 換成 `days_left`
6. 讀取 `assets/card-template.md`，依檔案開頭的說明填入所有 {{ }} 後輸出：
   - {{weekend}}：`days_left` 大於 0 時寫「距離週末還有 N 天（MM/DD 星期六）」，等於 0 時寫「今天放假！」

## 規則
- 時間、時段、天數一律以 scripts 的輸出為準，不要自己推算
- 問候語與鼓勵訊息只能用 references 裡有的，不要自己編
- 卡片照範本格式輸出，不要另外加東西
- 使用者只問「還有幾天放假」時，仍然輸出完整的問候卡

## 測試用
- 使用者指定日期（例如「假設今天是 10/14」）時，改執行 `python scripts/weekend.py 2026-10-14`
