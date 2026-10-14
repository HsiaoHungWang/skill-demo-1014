---
name: hello-skills-mcp
description: 依台北目前時段，用使用者指定的語言打招呼，並產出一張含「真正放假日」倒數（含國定假日、補假、連假）與鼓勵訊息的問候卡，可選擇貼到團隊留言板。當使用者說「哈囉」「打招呼」「早安」「做一張問候卡」「還有幾天放假」「離週末還有多久」「有沒有連假」「hello skills」或要求測試 Skill 時使用，即使沒有明說要問候卡也一樣。若使用者只是要翻譯一句問候語，不適用。
---

# Hello Skills（MCP 版）

## 流程
1. 執行 `python scripts/now.py`，取得：
   - `datetime`：台北目前日期時間
   - `period`：目前時段（morning／afternoon／evening）
2. 取得放假資訊（二選一，**優先用 MCP**）：
   - **A. 有 hello-mcp 連接器的 `get_next_day_off` 工具時**：呼叫它，取得
     `days_left`、`level`、`next_day_off_label`、`holiday_name`、`streak_days`、`streak_range`、`long_weekend`
   - **B. 沒有該工具，或工具回傳 `error` 時**：改執行 `python scripts/weekend.py`，
     取得 `saturday`、`days_left`、`level`，並記下「資料來源為退路」
3. 判斷使用者要的語言（沒有指定就用繁體中文）
4. 依 `period`，到 `references/greetings.md` 查問候語與結尾祝福語
5. 挑一句鼓勵訊息（`references/weekend-messages.md`），把 {N} 換成 `days_left`：
   - A 且 `days_left` 為 0 且 `long_weekend` 為 true → 用 `long-weekend` 區塊，{S} 換成 `streak_days`
   - 其他情況 → 依 `level` 找區塊
6. 讀取 `assets/card-template.md`，依檔案開頭的說明填入所有 {{ }} 後輸出

## 貼到留言板（選用）
7. 只有使用者明確說「貼出去」「發給大家」「貼到留言板」時才做：
   - 先顯示完整卡片與貼文對象（沒說就是「全體同仁」），問使用者是否確認
   - 使用者明確同意後，才呼叫 hello-mcp 的 `post_card` 工具（card 傳完整卡片文字）
   - 沒有 `post_card` 工具時，告知「尚未連接 hello-mcp，無法貼出」，不要假裝已貼出
   - 使用者沒提到貼出時，不要主動詢問

## 規則
- 時間、時段、天數、假日名稱一律以 scripts 或 MCP 工具的輸出為準，不要自己推算
- 問候語與鼓勵訊息只能用 references 裡有的，不要自己編
- 卡片照範本格式輸出，不要另外加東西
- 使用者只問「還有幾天放假」時，仍然輸出完整的問候卡

## 測試用
- 使用者指定日期（例如「假設今天是 10/14」）時：
  - A：呼叫 `get_next_day_off`，`date_str` 傳 `2026-10-14`
  - B：執行 `python scripts/weekend.py 2026-10-14`
