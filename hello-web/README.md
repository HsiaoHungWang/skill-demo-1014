# Hello Skills（MCP 版）— 網頁 Demo

和 `call_skills`（meeting-notes-todo）同一套架構：**SKILL_ID → FastAPI → 網頁**。
多出來的一件事：**FastAPI 自己當 MCP Host**，啟動本機 `hello-mcp`，把它的工具交給 Claude；
Claude 要查放假日或貼留言板時（`stop_reason = tool_use`），由 FastAPI 代為呼叫，再把結果送回去。

```
網頁 ──► FastAPI ──► Messages API（skill_id ＋ code_execution ＋ hello-mcp 的工具定義）
            │            └─ Skill 在 Claude 容器裡跑 now.py、讀 references
            └──► hello-mcp（stdio，本機）：get_next_day_off ／ post_card
```

> 為什麼不用 API 的 MCP connector？那要 Server 有公開 HTTPS 網址（tunnel）。
> 由後端代呼叫，`localhost` 的 Server 就能用，也不必把沒驗證的 Server 公開出去。

## 資料夾

```
skill-demo-1014\
├─ skills\
│  ├─ claude-lock.json     ← ant apply 後產生，app.py 會自動讀 SKILL_ID
│  └─ hello-skills-mcp\    ← 上傳這層
├─ hello-mcp\              ← 既有的 MCP Server（要先建好 .venv）
└─ hello-web\              ← 本範例
   ├─ app.py
   ├─ test.py
   └─ static\index.html
```

## 執行

```powershell
# 1. 上傳 Skill，拿到 SKILL_ID（只要做一次；改 SKILL.md 後再跑一次就是更新）
cd C:\workspace\1_claude\AgentSkills\skill-demo-1014\skills
ant apply hello-skills-mcp

# 2. 建虛擬環境、安裝套件
cd ..\hello-web
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt

# 3. 先確認 API 叫得到 Skill（不接 MCP）
.venv\Scripts\python.exe test.py

# 4. 啟動，開 http://localhost:8000
.venv\Scripts\python.exe -m uvicorn app:app --port 8000
```

`hello-mcp` 要先照它的 README 建好 `.venv` 並 `--prefetch 2026`；app.py 會用 `hello-mcp\.venv\Scripts\python.exe` 啟動它。
Windows 上建議不要加 `--reload`（重載模式的事件迴圈對子行程支援較差）。

## API

| 方法 | 路徑 | 用途 |
|---|---|---|
| GET | `/api/status` | SKILL_ID、hello-mcp 是否連得上、工具清單 |
| POST | `/api/greet` | 做問候卡（名字、語言、假設日期、是否接 MCP、要貼給誰） |
| POST | `/api/confirm` | 使用者按「確認貼出」→ 同一段對話繼續，允許 `post_card` |
| GET | `/api/outbox` | 讀 `hello-mcp\outbox.md`（留言板） |

## 和 meeting-notes-todo 版的差異

| | meeting-notes-todo | hello-skills-mcp |
|---|---|---|
| tools | `code_execution` | `code_execution` ＋ MCP 工具（從 `list_tools()` 轉換） |
| 迴圈 | 只處理 `pause_turn` | 再加 `tool_use`：後端呼叫 MCP，回傳 `tool_result` |
| 對話 | 一問一答 | 有 session：卡片 → 使用者確認 → 同一個 container 繼續 |
| 安全 | 只開放下載本次 file_id | `post_card` 要使用者在網頁按確認，後端才放行（Skill 規則之外的第二道防線） |
| 產出 | Word／.ics（Files API） | 卡片文字＋寫入 outbox.md |

## 示範腳本

| 步驟 | 設定 | 預期 |
|---|---|---|
| ① | 10/9 國慶補假、接 hello-mcp | 「今天放假！（補假、國慶日）連假 10/09–10/11」＋連假鼓勵語；軌跡出現 MCP `get_next_day_off` |
| ② | 同上，**取消勾選** hello-mcp | 軌跡改成 Skill `python scripts/weekend.py 2026-10-09`；卡片標示「⚠️ 未含國定假日與補班」 |
| ③ | 勾「貼到留言板」、對象：教育訓練部 | Claude 先秀卡片問確認 → 按「確認貼出」→ 軌跡出現 `post_card`，左下留言板更新 |
| ④ | 10/21 光復節連假前 | 「距離放假還有 3 天（10/24（六））・光復節…，連假 3 天」 |

## 設定（環境變數，都可不設）

| 變數 | 說明 | 預設 |
|---|---|---|
| `ANTHROPIC_API_KEY` | API Key（必填，setx 設定） | — |
| `SKILL_ID` | 指定 Skill | 讀 `..\skills\claude-lock.json` |
| `CLAUDE_MODEL` | 模型 | claude-opus-5-5 |
| `HELLO_MCP_DIR` | hello-mcp 資料夾 | `..\hello-mcp` |
| `HELLO_MCP_PYTHON` | 啟動 Server 的 python | `hello-mcp\.venv\Scripts\python.exe` |
