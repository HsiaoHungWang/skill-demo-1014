# hello-mcp：給 hello-skills 用的示範 MCP Server

用來示範 **Skill 管流程、MCP 管外部資料與寫入動作** 的分工。

| 工具 | 性質 | 用途 |
|---|---|---|
| `get_next_day_off(date_str)` | 唯讀 | 查政府行政機關辦公日曆，回傳下一個放假日、距今天數、假日名稱、連假天數 |
| `post_card(card, to)` | 寫入 | 把問候卡貼到「團隊留言板」（示範：附加到 `outbox.md`） |

日曆資料：行政院人事行政總處「政府行政機關辦公日曆表」（data.gov.tw 資料集 14718），
透過社群整理的 JSON 版 [ruyut/TaiwanCalendar](https://github.com/ruyut/TaiwanCalendar) 取得。
第一次查某年份時下載到 `cache/{year}.json`，之後都讀快取。

> ⚠️ 研討會前先執行 `.venv\Scripts\python.exe server.py --prefetch 2026` 建好快取，現場就不用連網。
> 也可以手動把 `https://cdn.jsdelivr.net/gh/ruyut/TaiwanCalendar/data/2026.json` 存成 `cache/2026.json`。

---

## 1. 安裝

在 `hello-mcp` 資料夾裡建立獨立的虛擬環境 `.venv`，不汙染系統的 Python：

```powershell
cd C:\workspace\1_claude\AgentSkills\skill-demo-1014\hello-mcp
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe server.py --prefetch 2026   # 下載並快取今年辦公日曆
.venv\Scripts\python.exe tests\test_server.py       # 不連網，用 tests\fixture-2026.json 測，應顯示「全部通過」
```

> 一律寫 `.venv\Scripts\python.exe` 的完整路徑，不用 `activate`。
> Claude Desktop 啟動 Server 時不會幫你 activate，config 裡也要寫 venv 的 python.exe，
> 否則會用到系統的 Python，出現 `No module named 'mcp'`。
>
> PowerShell 想要 activate 的話是 `.venv\Scripts\Activate.ps1`；
> 若出現「已停用指令碼執行」，先執行 `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`。

程式同時相容 MCP Python SDK v2（`MCPServer`）與 v1（`FastMCP`）。

## 2. 接到 Claude

### Claude Desktop（本機 stdio，示範最簡單）

編輯 `%APPDATA%\Claude\claude_desktop_config.json`，加入：

```json
{
  "mcpServers": {
    "hello-mcp": {
      "command": "C:\\workspace\\1_claude\\AgentSkills\\skill-demo-1014\\hello-mcp\\.venv\\Scripts\\python.exe",
      "args": ["C:\\workspace\\1_claude\\AgentSkills\\skill-demo-1014\\hello-mcp\\server.py"]
    }
  }
}
```

JSON 字串裡的反斜線要寫成兩個（`\\`）。存檔後**完全結束** Claude Desktop（系統匣也要結束）再打開。

### Claude Code

```powershell
claude mcp add hello-mcp -- C:\workspace\1_claude\AgentSkills\skill-demo-1014\hello-mcp\.venv\Scripts\python.exe C:\workspace\1_claude\AgentSkills\skill-demo-1014\hello-mcp\server.py
```

### claude.ai 網頁版（自訂連接器）

網頁版是從雲端呼叫 Server，`localhost` 連不到，必須有公開的 HTTPS 網址：

```powershell
.venv\Scripts\python.exe server.py --http   # http://127.0.0.1:8000/mcp
cloudflared tunnel --url http://localhost:8000  # 或 ngrok http 8000
```

把取得的 `https://xxxx.trycloudflare.com/mcp` 加成自訂連接器。
這個示範 Server **沒有做驗證**，網址公開期間任何人都能呼叫，demo 完請關掉 tunnel。

### 單獨測 Server（不經過 Claude）

```powershell
npx @modelcontextprotocol/inspector .venv\Scripts\python.exe server.py
```

## 3. 搭配的 Skill

`skills/hello-skills-mcp/`：從 hello-skills 複製出來改的版本。
- 步驟 2 改成「有 `get_next_day_off` 就用，沒有或出錯就退回 `scripts/weekend.py`」
- 卡片多一行資料來源（退路時顯示「⚠️ 未含國定假日與補班」）
- 新增 `long-weekend` 鼓勵訊息
- 新增「貼到留言板」：必須先給使用者確認，才呼叫 `post_card`

上傳時 **hello-skills 與 hello-skills-mcp 只開一個**，兩個描述很像，同時開著 Claude 不一定挑到你要示範的那個。

## 4. 研討會示範腳本（以 2026/10/9 為例）

| 步驟 | 設定 | 輸入 | 預期 |
|---|---|---|---|
| ① | 原版 hello-skills | 假設今天是 10/9，還有幾天放假？ | 「明天就放假了！再撐一天」→ **錯**，10/9 是國慶日補假 |
| ② | hello-skills-mcp ＋ hello-mcp | 同上 | 「今天放假！（補假、國慶日）連假 10/09（五）–10/11（日）」＋連假鼓勵語 |
| ③ | hello-skills-mcp，**關掉** hello-mcp | 同上 | 退回 weekend.py，卡片標示「⚠️ 未含國定假日與補班」 |
| ④ | hello-skills-mcp ＋ hello-mcp | 做一張卡貼到留言板給教育訓練部 | Claude 先秀卡片問確認 → 同意後才寫入 `outbox.md` |

其他好用的測試日：
- `10/21`（三）→ 3 天後 10/24 起光復節連假 3 天
- `10/14`（三）→ 一般週末，結果與原版相同（證明沒有亂改）

## 5. 這個範例想講的重點

1. **計算放 Skill、外部資料放 MCP**：`now.py`、`weekend.py` 不需要權限，留在 Skill；辦公日曆每年會變，交給 Server。
2. **回傳欄位對齊**：MCP 也回傳 `days_left`、`level`，Skill 後續步驟幾乎不用改。
3. **一定要有退路**：連接器斷了，Skill 仍能產出結果，並誠實標示資料較不完整。
4. **安全規則寫在 Skill**：Server 收到合法呼叫就會執行，不知道 Skill 存在；「先確認再貼出」只能靠 Skill 約束。
5. **工具描述就是說明書**：docstring 寫清楚何時用、參數格式、回傳欄位；錯誤訊息要能讓 AI 自己修正（例如日期格式錯誤時告訴它正確格式）。
