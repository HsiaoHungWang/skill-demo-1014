# 開發實作手冊：把 hello-skills-mcp 變成自己的網頁服務

> 從 SKILL_ID 到 FastAPI，再到網頁｜搭配簡報「開發實作」延伸單元（第 61–72 頁）
> 資展國際 iSpan ｜ 掌握 Agent Skills 打造專屬 AI 技能包

做完這份手冊，你會有一個自己的網頁：
選語言、選日期 → Claude 套用 **hello-skills-mcp** Skill → 透過 **hello-mcp** 查政府辦公日曆 → 產出問候卡 → 你按確認後，貼到團隊留言板。

---

## 0. 先看懂架構

```
 ┌────────┐   ┌──────────────┐   ┌───────────────────────────────┐
 │ 網頁    │ → │ FastAPI 後端   │ → │ Claude Messages API             │
 │index.html│   │ app.py        │   │ skill_id ＋ code_execution ＋ 工具 │
 └────────┘   │ ・保管 API Key  │   │ （容器裡跑 now.py、讀 references） │
              │ ・當 MCP Host   │   └───────────────┬───────────────┘
              │               │ ←── tool_use ─────┘
              │               │ ──► hello-mcp（本機 stdio）
              └──────────────┘      get_next_day_off ／ post_card
```

| 角色 | 負責 | 這次的檔案 |
|---|---|---|
| Skill | 流程與規則：時段、問候語、卡片格式、「貼出前要先問」 | `skills/hello-skills-mcp/` |
| MCP Server | 外部資料與寫入：政府辦公日曆、留言板 | `hello-mcp/server.py` |
| FastAPI | 保管 Key、呼叫 Claude、**代 Claude 呼叫 MCP 工具** | `hello-web/app.py` |
| 網頁 | 輸入、顯示卡片、確認鈕、執行軌跡 | `hello-web/static/index.html` |

**三個關鍵觀念**

1. Claude Desktop／claude.ai 上傳的 Skill，API 看不到；要另外用 `ant apply` 上傳，拿到 **SKILL_ID**。
2. API Key 只放在後端；網頁只呼叫自己的 FastAPI。
3. MCP Server 跑在你的電腦上，Claude 的雲端連不到 `localhost`；所以由 **FastAPI 當 MCP Host**：把工具清單交給 Claude，Claude 要用時（`stop_reason = tool_use`）由後端代為呼叫。

---

## 1. 事前準備

| 項目 | 需求 | 確認方式 |
|---|---|---|
| Python | 3.10 以上 | `python --version` |
| Go | 1.22 以上（安裝 ant 用） | `go version` |
| Claude Console 帳號 | 有 API 額度 | https://console.anthropic.com |
| 範例資料夾 | `skill-demo-1014`（會後提供） | 見下方結構 |

完成後的資料夾結構：

```
C:\workspace\1_claude\AgentSkills\skill-demo-1014\
├─ skills\
│  ├─ claude-lock.json          ← STEP 3 執行 ant apply 後產生
│  └─ hello-skills-mcp\         ← Skill 本體
│     ├─ SKILL.md
│     ├─ assets\card-template.md
│     ├─ references\greetings.md、weekend-messages.md
│     └─ scripts\now.py、weekend.py
├─ hello-mcp\                   ← MCP Server
│  ├─ server.py
│  ├─ cache\2026.json           ← 辦公日曆快取
│  └─ outbox.md                 ← 留言板（post_card 寫入）
└─ hello-web\                   ← 本手冊要做的
   ├─ app.py
   ├─ test.py
   ├─ requirements.txt
   └─ static\
      ├─ index.html
      └─ vendor\marked.min.js、purify.min.js
```

> 以下指令都在 **PowerShell** 執行。路徑請換成你自己的位置。

---

## STEP 1　準備 API Key

1. 打開 Claude Console → **API keys** → **Create key**
   - 若跳出 identity federation 建議，本機開發選 **Continue with an API key**

   | 欄位 | 建議設定 | 說明 |
   |---|---|---|
   | Name | `skill-demo` | 一個專案一把，方便停用 |
   | Expires | 30 天 | demo 用，到期自動失效 |
   | Scope | Default workspace | Skill 也會上傳到這裡 |

2. 存成環境變數：

   ```powershell
   setx ANTHROPIC_API_KEY "sk-ant-..."
   ```

3. **關掉 PowerShell 重開**，確認有值：

   ```powershell
   echo $env:ANTHROPIC_API_KEY
   ```

> ⚠️ Key 只顯示一次。上傳 Skill 和呼叫 Skill 要用**同一個 workspace** 的 Key。不要寫進程式、不要放前端、不要上傳到 GitHub。

---

## STEP 2　安裝 ant CLI

```powershell
winget install GoLang.Go          # 1. 安裝 Go，裝完重開視窗
go install github.com/anthropics/anthropic-cli/cmd/ant@latest   # 2. 安裝 ant
ant --version                     # 3. 確認安裝成功
```

出現「找不到 ant」：把 `%USERPROFILE%\go\bin` 加進 PATH，重開視窗再試。
Mac：`brew install anthropics/tap/ant`。

---

## STEP 3　上傳 Skill，拿到 SKILL_ID

```powershell
cd C:\workspace\1_claude\AgentSkills\skill-demo-1014\skills
ant apply hello-skills-mcp
```

```
Apply these changes? y
+ ./hello-skills-mcp  created
  skill_01EXn2ZVk58rFsDtkFMGVY7H      ← 你的 ID 會不一樣
```

同一層會多出 `claude-lock.json`，裡面記著 skill_id 與版本：

```json
"resources": {
  "./hello-skills-mcp": {
    "kind": "skill",
    "id": "skill_01EXn2ZVk58rFsDtkFMGVY7H",
    "version": "skver_01K7w4Nf4yWDrSk5G7yReSqe"
  }
}
```

**三個檢查點**

- ① 指向**資料夾**，不是 zip
- ② `SKILL.md` 要在 `hello-skills-mcp\` 的**第一層**（從 Desktop 下載的 zip 解壓後常多一層同名資料夾）
- ③ 在 Skill 的**上一層**（`skills\`）執行

> `claude-lock.json` 要留著。之後改了 Skill 再執行一次 `ant apply`，會更新同一個 Skill，skill_id 不變。`app.py` 和 `test.py` 都會自動讀這個檔，不用手動貼 SKILL_ID。

---

## STEP 4　準備 hello-mcp（MCP Server）

hello-mcp 要有自己的虛擬環境，FastAPI 會用它的 python 來啟動 Server。

```powershell
cd C:\workspace\1_claude\AgentSkills\skill-demo-1014\hello-mcp
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe server.py --prefetch 2026   # 下載並快取 2026 辦公日曆
.venv\Scripts\python.exe tests\test_server.py        # 應顯示「全部通過」
```

> 研討會現場網路不穩時，`--prefetch` 先做好，Server 就不必連網。

hello-mcp 提供兩個工具：

| 工具 | 性質 | 用途 |
|---|---|---|
| `get_next_day_off(date_str)` | 唯讀 | 查下一個放假日、距今天數、假日名稱、連假天數 |
| `post_card(card, to)` | **寫入** | 把卡片附加到 `outbox.md`（示範用留言板） |

---

## STEP 5　用 test.py 確認 API 叫得到 Skill

```powershell
cd C:\workspace\1_claude\AgentSkills\skill-demo-1014\hello-web
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python test.py
```

`requirements.txt`：

```
anthropic>=1.11
fastapi>=0.115
uvicorn[standard]>=0.30
mcp
```

`test.py`：

```python
"""STEP 4：確認 API 叫得到 hello-skills-mcp（先不接 MCP，Skill 會走 weekend.py 退路）。"""
import json
from pathlib import Path

from anthropic import Anthropic

lock = json.loads((Path(__file__).parent.parent / "skills" / "claude-lock.json").read_text(encoding="utf-8"))
skill_id = lock["resources"]["./hello-skills-mcp"]["id"]
print("SKILL_ID =", skill_id)

client = Anthropic()  # 自動讀取 ANTHROPIC_API_KEY
resp = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=4096,
    container={"skills": [{"type": "custom", "skill_id": skill_id, "version": "latest"}]},
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}],
    messages=[{"role": "user", "content": "哈囉！假設今天是 2026-10-14，幫我做一張問候卡。"}],
)
for block in resp.content:
    if block.type == "text":
        print(block.text)
```

**預期結果**（實測）

```
━━━━━━━━━━━━━━━━━━━━
👋 午安，朋友！
🕐 2026-10-14 13:59（台北時間）
📅 距離週末還有 3 天（10/17 星期六）
　 ⚠️ 未含國定假日與補班
💪 🐫 駝峰日快樂！還有 3 天，穩穩前進就好。
💬 祝你有美好的一天！
✨ 這張卡片由 Hello Skills（MCP 版）產生
━━━━━━━━━━━━━━━━━━━━
```

怎麼確認 Skill 有作用：

- 依台北時段用「午安」（`scripts/now.py`）
- 沒接 MCP → 改跑 `scripts/weekend.py`，並標示「⚠️ 未含國定假日與補班」
- 鼓勵語是 `references/weekend-messages.md` 裡的句子（駝峰日快樂）

> 兩個關鍵參數：`container.skills` 指定 Skill；`tools` 一定要帶 `code_execution`，Skill 才能在容器裡跑 scripts。

---

## STEP 6　FastAPI 後端 app.py

完整程式見附錄 A。以下拆成五段說明。

### 6-1　設定：SKILL_ID 自動從 claude-lock.json 讀

```python
MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")
HELLO_MCP_DIR = Path(os.getenv("HELLO_MCP_DIR", BASE_DIR.parent / "hello-mcp"))
LOCK_FILE = Path(os.getenv("SKILL_LOCK_FILE", BASE_DIR.parent / "skills" / "claude-lock.json"))

def resolve_skill_id() -> str:
    if os.getenv("SKILL_ID"):                 # 有設環境變數就用
        return os.environ["SKILL_ID"]
    lock = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
    ...                                       # 否則找 ./hello-skills-mcp 的 id

SKILLS = [{"type": "custom", "skill_id": SKILL_ID, "version": "latest"}]
CODE_EXEC = {"type": "code_execution_20250825", "name": "code_execution"}
```

`"version": "latest"`：之後 `ant apply` 更新 Skill，下一次呼叫就是新版。

### 6-2　後端當 MCP Host：啟動 Server、列出工具

```python
def mcp_params() -> StdioServerParameters:
    return StdioServerParameters(
        command=HELLO_MCP_PYTHON,                 # hello-mcp\.venv\Scripts\python.exe
        args=[str(HELLO_MCP_DIR / "server.py")],
        cwd=str(HELLO_MCP_DIR),
    )

async def open_mcp(stack):
    read, write = await stack.enter_async_context(stdio_client(mcp_params()))
    session = await stack.enter_async_context(ClientSession(read, write))
    await session.initialize()
    return session

def to_claude_tool(t) -> dict:
    """MCP 工具定義 → Messages API 的 tools 格式"""
    return {"name": t.name, "description": f"[hello-mcp] {t.description}", "input_schema": t.input_schema}
```

| 步驟 | MCP Python SDK |
|---|---|
| 啟動 Server | `stdio_client(params)` |
| 初始化 | `session.initialize()` |
| 列出工具 | `session.list_tools()` |
| 轉成 tools | `{name, description, input_schema}` |
| 呼叫工具 | `session.call_tool(name, args)` |

> 工具的 description（server.py 裡的 docstring）會原封不動交給 Claude，Claude 靠它判斷何時使用。描述寫得好，工具才會被正確呼叫。

### 6-3　核心迴圈：處理 pause_turn 與 tool_use

```python
for _ in range(MAX_ROUNDS):
    resp = await client.messages.create(
        model=MODEL, max_tokens=4096,
        container=container,              # skills ＋（第二輪起）container id
        tools=tools,                      # code_execution ＋ MCP 工具
        messages=sess["messages"],
    )
    sess["messages"].append({"role": "assistant", "content": resp.content})

    tool_results = []
    for b in resp.content:
        if b.type == "tool_use":          # Claude 要用 MCP 工具
            tool_results.append(await call_mcp_tool(sess, mcp, b, trace))

    if resp.stop_reason == "pause_turn":  # 長任務：沿用同一個 container 繼續
        continue
    if resp.stop_reason == "tool_use":    # 把工具結果送回去，讓 Claude 接著做
        sess["messages"].append({"role": "user", "content": tool_results})
        continue
    break                                  # end_turn：完成
```

| stop_reason | 意思 | 後端要做的事 |
|---|---|---|
| `end_turn` | 完成 | 回傳結果給網頁 |
| `tool_use` | Claude 要用你提供的工具 | 呼叫 MCP，回傳 `tool_result` 再續跑 |
| `pause_turn` | 長任務暫停 | 原樣再呼叫一次，沿用同一個 container |

> Messages API 沒有記憶：每一輪都要把前面的 `messages` 全部帶上。

### 6-4　寫入動作的第二道防線

```python
if block.name == "post_card" and not sess.get("confirmed"):
    # Skill 規定要先問使用者；後端再擋一次
    return {"type": "tool_result", "tool_use_id": block.id,
            "content": "尚未取得使用者確認，不能貼出…", "is_error": True}
r = await mcp.call_tool(block.name, args)
```

- **第一道**：SKILL.md 規定「先顯示卡片，使用者同意才呼叫 post_card」
- **第二道**：使用者沒在網頁按「確認貼出」，後端就回錯誤不執行（執行軌跡顯示 ⛔）

> MCP Server 收到合法呼叫就會執行，它不知道 Skill 存在。寫入類的工具，最好在你能控制的後端再加一道關卡。

### 6-5　五支 API

| 方法 | 路徑 | 做什麼 |
|---|---|---|
| POST | `/api/greet` | 收名字、語言、日期 → 啟動 hello-mcp → 帶 skill_id＋工具呼叫 Claude；開一個 session |
| POST | `/api/confirm` | 使用者按「確認貼出」→ 同一個 session、同一個 container 繼續，放行 post_card |
| GET | `/api/status` | SKILL_ID、hello-mcp 是否連上、工具清單（網頁頂端狀態列） |
| GET | `/api/outbox` | 讀 `hello-mcp\outbox.md`（留言板） |
| GET | `/` | 回傳 `static/index.html` |

`/api/greet` 會把網頁選項組成一句話送給 Claude，例如：

```
哈囉！我是小明，請用繁體中文幫我做一張問候卡。
假設今天是 2026-10-10。
做好之後幫我貼到留言板給全體同仁。
```

---

## STEP 7　網頁 static/index.html

網頁只做一件事：呼叫自己的 FastAPI。（完整檔案在 `hello-web\static\index.html`）

```javascript
const res = await fetch('/api/greet', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({ name, language, as_of, use_mcp, post_to })
});
const data = await res.json();
// data.text             → 問候卡框＋說明文字
// data.awaiting_confirm → 顯示「確認貼出」按鈕 → POST /api/confirm
// data.trace            → 執行軌跡（Skill／MCP）
```

| 區塊 | 內容 |
|---|---|
| ① 問候卡設定 | 名字、語言、假設日期（快捷鈕 10/9、10/14、10/21）、連接 hello-mcp 開關、貼到留言板 |
| ② Claude 的回覆 | 送出的指令、問候卡、確認列、tokens 用量 |
| ③ 團隊留言板 | `outbox.md` 最新內容 |
| 執行軌跡 | 🟨 Skill：容器裡跑的 scripts、讀的檔案　🟦 MCP：後端代呼叫的工具與回傳 |

> Markdown 轉換用 `marked`，再用 `DOMPurify` 清理，不把 AI 輸出直接塞進頁面。兩個函式庫放在 `static/vendor`，公司網路擋外部 CDN 也能用。

---

## STEP 8　啟動與示範

```powershell
cd C:\workspace\1_claude\AgentSkills\skill-demo-1014\hello-web
.venv\Scripts\python.exe -m uvicorn app:app --port 8000
```

瀏覽器開 http://localhost:8000，先看頂端狀態列：

```
SKILL_ID skill_01EXn2ZVk…   模型 claude-opus-5-5   hello-mcp 已連線：get_next_day_off、post_card
```

> Windows 上**不要加 `--reload`**：重載模式的事件迴圈對子行程支援較差，啟動 MCP Server 可能出現 `NotImplementedError`。

### 示範腳本

| # | 設定 | 預期結果 | 想講的重點 |
|---|---|---|---|
| ① | 日期 **10/9**、勾選 hello-mcp | 「今天放假！（補假、國慶日）連假 10/09（五）–10/11（日）」＋連假鼓勵語；軌跡出現 MCP `get_next_day_off` | MCP 補上 Skill 自己算不出來的外部資料 |
| ② | 同上，**取消勾選** hello-mcp | 軌跡改成 Skill `weekend.py`；卡片標「⚠️ 未含國定假日與補班」 | Skill 要有退路，並誠實標示 |
| ③ | 勾選「貼到留言板」，對象：教育訓練部 | Claude 先秀卡片問確認 → 按「確認貼出」→ 軌跡出現 `post_card`，留言板更新 | 寫入動作：Skill 規定先問＋後端再擋一次 |
| ④ | 日期 **10/21** | 「距離放假還有 3 天（10/24（六））・光復節…，連假 3 天」 | 同一套流程，不同日期自動正確 |
| ⑤ | 日期 **10/14** | 與 test.py 結果相同（一般週末） | MCP 沒有亂改正常情況 |

實測參考：做卡片＋確認貼出合計約 3.6 萬 input tokens；正式使用前要評估費用。

---

## STEP 9　更新 Skill：前後端都不用改

1. **修改 Skill**：改 `SKILL.md`、`references` 或 `scripts`
2. **ant apply**：

   ```powershell
   cd C:\workspace\1_claude\AgentSkills\skill-demo-1014\skills
   ant apply hello-skills-mcp      # 顯示 update；skill_id 不變、版本 ID 更新
   ```

3. **直接生效**：呼叫時用 `"version": "latest"`，下一次就是新版

**練習**：在 `references/weekend-messages.md` 的 `long-weekend` 區塊加一句新的鼓勵語 → `ant apply` → 網頁選 10/9 重跑，看看新句子會不會出現。

> ⚠️ 常見的坑：改完忘了 `ant apply`，本機是新版、API 上還是舊版。確認方式：看 `claude-lock.json` 的 `version` 有沒有變。
> MCP Server 的程式改了則不用任何上傳：後端每次請求都重新啟動 hello-mcp，下一次呼叫就生效。

---

## 常見卡關

| 症狀 | 原因與解法 |
|---|---|
| 網頁顯示「尚未設定 SKILL_ID」 | 還沒 `ant apply` → 在 `skills` 資料夾執行，產生 `claude-lock.json` |
| hello-mcp 未連線 | `hello-mcp\.venv` 沒建好 → 照 STEP 4 建 venv、安裝 mcp |
| 有接 MCP 卻標 ⚠️ | 辦公日曆下載失敗 → 先跑 `server.py --prefetch 2026` |
| Skill 沒作用 | 沒帶 code_execution → `tools` 加上 `code_execution_20250825` |
| `NotImplementedError` | Windows 加了 `--reload` → 拿掉再啟動 |
| API 回 skill 不存在 | Key 跟 Skill 不在同一個 workspace → 用同一個 workspace 的 Key |
| 改了規則沒生效 | 忘了 `ant apply` → 重新上傳，確認 `claude-lock.json` 版本有變 |
| 找不到 ant 指令 | Go 的 bin 不在 PATH → 加入 `%USERPROFILE%\go\bin` 後重開視窗 |
| `Activate.ps1` 已停用指令碼執行 | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`，或直接用 `.venv\Scripts\python.exe` |

**一句話**：Skill 管流程、MCP 管外部資料與寫入；Key 和 MCP 都在後端，網頁只呼叫自己的 FastAPI。

---

## 延伸：和 meeting-notes-todo 版的差異

| | meeting-notes-todo（call_skills） | hello-skills-mcp（hello-web） |
|---|---|---|
| tools | `code_execution` | `code_execution` ＋ MCP 工具（從 `list_tools()` 轉換） |
| 迴圈 | 只處理 `pause_turn` | 再加 `tool_use`：呼叫 MCP、回傳 `tool_result` |
| 對話 | 一問一答 | 有 session：卡片 → 使用者確認 → 同一個 container 繼續 |
| 產出 | Word、.ics（Files API 下載） | 卡片文字＋寫入 `outbox.md` |
| 安全 | 只開放下載本次產生的 file_id | `post_card` 要使用者按確認，後端才放行 |

**為什麼不用 Messages API 內建的 MCP connector？**
內建 connector 是 Claude 的雲端直接連你的 Server，必須有公開的 HTTPS 網址（例如用 cloudflared tunnel）。這個示範 Server 沒有做驗證，公開出去任何人都能呼叫。由後端代呼叫，`localhost` 就能用，也能在後端加確認關卡。正式環境若 Server 已部署在雲端並有驗證，再考慮改用 connector。

---

## 附錄 A　app.py 完整程式

```python
"""
Hello Skills（MCP 版）網頁 Demo — FastAPI 後端

和 call_skills（meeting-notes-todo）同一套架構，多了一件事：
  後端自己當「MCP Host」—— 啟動本機 hello-mcp Server，把它的工具交給 Claude，
  Claude 要用工具時（stop_reason = tool_use），由後端代為呼叫 MCP，再把結果送回去。

  網頁 ─► FastAPI ─► Messages API（skill_id + code_execution + MCP 工具清單）
                 └─► hello-mcp（stdio）：get_next_day_off / post_card

API：
  GET  /                 前端頁面
  GET  /api/status       Skill ID、MCP 連線狀態與工具清單
  POST /api/greet        做問候卡（開新對話）
  POST /api/confirm      使用者在網頁按「確認貼出」後，同一段對話繼續 → 允許 post_card
  GET  /api/outbox       看留言板（hello-mcp/outbox.md）最新內容

API Key 從環境變數 ANTHROPIC_API_KEY 讀取，絕不寫在前端。
"""
import json
import os
import sys
import uuid
from contextlib import AsyncExitStack
from datetime import date
from pathlib import Path
from typing import Any, Literal

from anthropic import AsyncAnthropic
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent

# ── 設定（都可用環境變數覆蓋）────────────────────────────────
MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")
MAX_ROUNDS = 10  # pause_turn 續跑 + tool_use 來回，合計上限
HELLO_MCP_DIR = Path(os.getenv("HELLO_MCP_DIR", BASE_DIR.parent / "hello-mcp"))
_venv_py = HELLO_MCP_DIR / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
HELLO_MCP_PYTHON = os.getenv("HELLO_MCP_PYTHON", str(_venv_py if _venv_py.exists() else sys.executable))
LOCK_FILE = Path(os.getenv("SKILL_LOCK_FILE", BASE_DIR.parent / "skills" / "claude-lock.json"))


def resolve_skill_id() -> str:
    """SKILL_ID 優先用環境變數；沒有就讀 ant apply 產生的 claude-lock.json。"""
    if os.getenv("SKILL_ID"):
        return os.environ["SKILL_ID"]
    if LOCK_FILE.exists():
        lock = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
        for path, res in lock.get("resources", {}).items():
            if res.get("kind") == "skill" and path.rstrip("/").endswith("hello-skills-mcp"):
                return res["id"]
    return ""


SKILL_ID = resolve_skill_id()
SKILLS = [{"type": "custom", "skill_id": SKILL_ID, "version": "latest"}]
CODE_EXEC = {"type": "code_execution_20250825", "name": "code_execution"}

client = AsyncAnthropic()  # 自動讀取 ANTHROPIC_API_KEY
app = FastAPI(title="Hello Skills（MCP 版）Demo")

# 對話暫存（demo 用記憶體即可；正式環境改 Redis／資料庫）
SESSIONS: dict[str, dict] = {}


# ── MCP：後端當 Host，連到本機 hello-mcp ─────────────────────
def mcp_params() -> StdioServerParameters:
    return StdioServerParameters(
        command=HELLO_MCP_PYTHON,
        args=[str(HELLO_MCP_DIR / "server.py")],
        cwd=str(HELLO_MCP_DIR),
    )


async def open_mcp(stack: AsyncExitStack) -> ClientSession:
    read, write = await stack.enter_async_context(stdio_client(mcp_params()))
    session = await stack.enter_async_context(ClientSession(read, write))
    await session.initialize()
    return session


def to_claude_tool(t: Any) -> dict:
    """MCP 工具定義 → Messages API 的 tools 格式（相容 mcp v1 / v2 欄位名稱）。"""
    schema = getattr(t, "input_schema", None) or getattr(t, "inputSchema", None) or {"type": "object"}
    return {"name": t.name, "description": f"[hello-mcp] {t.description or ''}".strip(), "input_schema": schema}


def mcp_result_text(r: Any) -> tuple[str, bool]:
    texts = [c.text for c in r.content if getattr(c, "type", "") == "text"]
    is_error = bool(getattr(r, "is_error", None) or getattr(r, "isError", False))
    return "\n".join(texts) or "{}", is_error


# ── 組指令 ─────────────────────────────────────────────────
class GreetRequest(BaseModel):
    name: str = Field("", max_length=30, description="使用者名字，留空則卡片寫「朋友」")
    language: str = Field("繁體中文", max_length=20)
    as_of: date | None = Field(None, description="測試用：假設今天是哪一天")
    use_mcp: bool = Field(True, description="關掉可示範退路（weekend.py）")
    post_to: str | None = Field(None, max_length=30, description="要貼到留言板給誰；None = 不貼")


class ConfirmRequest(BaseModel):
    session_id: str
    action: Literal["confirm", "cancel"] = "confirm"


def build_prompt(req: GreetRequest) -> str:
    who = f"我是{req.name.strip()}，" if req.name.strip() else ""
    parts = [f"哈囉！{who}請用{req.language}幫我做一張問候卡。"]
    if req.as_of:
        parts.append(f"假設今天是 {req.as_of:%Y-%m-%d}。")
    if req.post_to:
        parts.append(f"做好之後幫我貼到留言板給{req.post_to.strip() or '全體同仁'}。")
    return "\n".join(parts)


# ── 核心：呼叫 Claude，遇到 MCP 工具就代為執行 ─────────────────
def describe_server_tool(block: dict) -> str:
    """把 Skill 在容器裡做的事轉成一句話，給網頁的「執行軌跡」用。"""
    inp = block.get("input") or {}
    cmd = inp.get("command", "")
    if block.get("name") == "text_editor_code_execution":
        return f"讀取 {inp.get('path', '')}" if cmd == "view" else f"{cmd} {inp.get('path', '')}"
    return cmd if isinstance(cmd, str) else json.dumps(inp, ensure_ascii=False)


async def run_claude(sess: dict, mcp: ClientSession | None, tools: list[dict]) -> dict:
    trace: list[dict] = []
    texts: list[str] = []
    usage = {"input_tokens": 0, "output_tokens": 0}
    mcp_tool_names = {t["name"] for t in tools if t.get("input_schema")}

    for _ in range(MAX_ROUNDS):
        container = {"skills": SKILLS}
        if sess.get("container_id"):
            container["id"] = sess["container_id"]
        resp = await client.messages.create(
            model=MODEL,
            max_tokens=4096,
            container=container,
            tools=tools,
            messages=sess["messages"],
        )
        sess["container_id"] = resp.container.id if resp.container else sess.get("container_id")
        usage["input_tokens"] += resp.usage.input_tokens
        usage["output_tokens"] += resp.usage.output_tokens
        sess["messages"].append({"role": "assistant", "content": resp.content})

        tool_results = []
        for b in resp.content:
            if b.type == "text":
                texts.append(b.text)
            elif b.type == "server_tool_use":
                trace.append({"kind": "skill", "label": describe_server_tool(b.model_dump())})
            elif b.type == "tool_use" and b.name in mcp_tool_names:
                tool_results.append(await call_mcp_tool(sess, mcp, b, trace))

        if resp.stop_reason == "pause_turn":  # 長任務：同一個 container 接著跑
            continue
        if resp.stop_reason == "tool_use" and tool_results:
            sess["messages"].append({"role": "user", "content": tool_results})
            continue
        break

    return {"text": "\n\n".join(texts).strip(), "trace": trace, "usage": usage}


async def call_mcp_tool(sess: dict, mcp: ClientSession | None, block: Any, trace: list) -> dict:
    """Claude 要呼叫 MCP 工具 → 後端代為執行。post_card 多一道關卡：使用者要先在網頁按確認。"""
    args = block.input or {}
    shown = {"to": args.get("to", "全體同仁")} if block.name == "post_card" else args  # 卡片全文太長，軌跡只顯示對象
    item = {"kind": "mcp", "label": f"{block.name}({json.dumps(shown, ensure_ascii=False)})"}

    if block.name == "post_card" and not sess.get("confirmed"):
        # 第二道防線：Skill 規定要先問，後端再擋一次，避免 Claude 沒先問就直接貼出
        text, is_error = "尚未取得使用者確認，不能貼出。請先把完整卡片與貼文對象給使用者看，等使用者在網頁上按「確認貼出」。", True
        item["label"] += "　⛔ 已攔下（使用者尚未確認）"
    elif mcp is None:
        text, is_error = "hello-mcp 未連線", True
    else:
        r = await mcp.call_tool(block.name, args)
        text, is_error = mcp_result_text(r)
        if block.name == "post_card" and not is_error:
            sess["posted"] = True
    item["result"] = text[:400]
    trace.append(item)
    return {"type": "tool_result", "tool_use_id": block.id, "content": text, "is_error": is_error}


async def run_turn(sess: dict) -> dict:
    async with AsyncExitStack() as stack:
        mcp, tools = None, [CODE_EXEC]
        if sess["use_mcp"]:
            try:
                mcp = await open_mcp(stack)
                tools += [to_claude_tool(t) for t in (await mcp.list_tools()).tools]
            except Exception as e:  # noqa: BLE001 —— 連不上就當作沒有 MCP，讓 Skill 走退路
                sess.setdefault("notes", []).append(f"hello-mcp 啟動失敗，改走退路：{e}")
                mcp = None
        try:
            out = await run_claude(sess, mcp, tools)
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=f"呼叫 Claude API 失敗：{e}") from e
    out["tools"] = [t["name"] for t in tools]
    out["notes"] = sess.pop("notes", [])
    return out


# ── API ───────────────────────────────────────────────────
@app.get("/api/status")
async def status():
    info = {"skill_id": SKILL_ID or None, "model": MODEL, "mcp": {"ok": False, "tools": []}}
    try:
        async with AsyncExitStack() as stack:
            mcp = await open_mcp(stack)
            info["mcp"] = {"ok": True, "tools": [t.name for t in (await mcp.list_tools()).tools]}
    except Exception as e:  # noqa: BLE001
        info["mcp"]["error"] = str(e)
    return info


@app.post("/api/greet")
async def greet(req: GreetRequest):
    if not SKILL_ID:
        raise HTTPException(400, "找不到 SKILL_ID：請先在 skills 資料夾執行 ant apply hello-skills-mcp，或設定環境變數 SKILL_ID。")
    sid = uuid.uuid4().hex
    sess = {
        "messages": [{"role": "user", "content": build_prompt(req)}],
        "use_mcp": req.use_mcp,
        "want_post": bool(req.post_to),
        "confirmed": False,
        "posted": False,
    }
    SESSIONS[sid] = sess
    out = await run_turn(sess)
    return {"session_id": sid, "prompt": sess["messages"][0]["content"], **out,
            "awaiting_confirm": sess["want_post"] and not sess["posted"], "posted": sess["posted"]}


@app.post("/api/confirm")
async def confirm(req: ConfirmRequest):
    sess = SESSIONS.get(req.session_id)
    if not sess:
        raise HTTPException(404, "對話已過期，請重新產生卡片。")
    if req.action == "cancel":
        sess["want_post"] = False
        return {"text": "已取消，卡片不會貼出。", "trace": [], "usage": {"input_tokens": 0, "output_tokens": 0},
                "awaiting_confirm": False, "posted": False}
    sess["confirmed"] = True
    sess["messages"].append({"role": "user", "content": "確認，貼出去。"})
    out = await run_turn(sess)
    return {**out, "awaiting_confirm": False, "posted": sess["posted"]}


@app.get("/api/outbox")
def outbox():
    f = Path(os.getenv("HELLO_MCP_OUTBOX", HELLO_MCP_DIR / "outbox.md"))
    return {"path": str(f), "content": f.read_text(encoding="utf-8")[-3000:] if f.exists() else ""}


@app.get("/")
def index():
    return FileResponse(BASE_DIR / "static" / "index.html")


app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
```
