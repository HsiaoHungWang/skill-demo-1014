# Hello Skills 操作手冊 Demo 5：自己做一個 MCP Server，接上 Claude Desktop

> 環境：**Windows ＋ Claude Desktop**（已登入）＋ **Python 3.10 以上** ＋ 任一文字編輯器（建議 VS Code）
> 前提：已完成《Hello Skills 操作手冊》Demo 3，手上有 `hello-skills` 資料夾
> 目標：自己做一個 MCP Server `hello-mcp`，讓 Skill 能查到**真正的放假日**（國定假日、補假、連假）

| 步驟 | 做什麼 | 學到什麼 |
|---|---|---|
| 5-1～5-3 | 寫 `hello-mcp`，在本機測試 | MCP Server 就是一支提供「工具」的程式 |
| 5-4 | 接上 Claude Desktop | 本機 MCP 怎麼設定、怎麼確認有接上 |
| 5-5 | 做 `hello-skills-mcp` | Skill 怎麼指揮 MCP 工具，並保留退路 |
| 5-6～5-7 | 三種情境測試 | 有 MCP、沒 MCP、寫入動作要先確認 |

---

## 為什麼需要 MCP？

Demo 3 的 `weekend.py` 只看「星期幾」，不知道國定假日、補假、補班。

例如 **2026/10/10 國慶日是星期六，10/9（五）補假**。如果今天是 10/9，`weekend.py` 會說「明天才放假」，但其實今天就放假了。

這種**會變動的外部資料**，不適合寫死在 Skill 裡，要交給 MCP Server 去查。

> 一句話記住：**Skill 是 SOP 手冊，MCP 是外線電話。**
> Claude 照 SOP 做事，SOP 寫著「這一步打電話問」，Claude 就撥那支電話。

| 角色 | 比喻 | 在這個 Demo 裡 |
|---|---|---|
| Claude | 新來的行政助理 | 聽懂需求、照流程做事 |
| Skill | 主管給的 SOP 手冊 | `hello-skills-mcp`：步驟、問候語、卡片範本 |
| scripts | 桌上的計算機 | `now.py`：現在幾點、什麼時段 |
| MCP Server | 打去人事室的電話 | `hello-mcp`：查政府辦公日曆 |
| 退路 | 電話不通，先看桌曆 | `weekend.py`，並在卡片上標示「⚠️ 未含國定假日」 |

---

## 準備工作

### 1. 確認 Python

開啟 **PowerShell**，輸入：

```powershell
python --version
```

看到 `Python 3.10` 以上即可。如果出現找不到指令，到 https://www.python.org/downloads/ 安裝，安裝畫面記得勾選 **Add python.exe to PATH**。

### 2. 確認 Claude Desktop

- 從 https://claude.ai/download 下載安裝並登入
- 設定 → **Capabilities** → 確認「**程式碼執行（Code execution）**」為開啟（Skill 要執行 scripts）

### 3. 練習資料夾

沿用 Demo 3 的 `C:\SkillDemo\`，完成後會長這樣：

```
C:\SkillDemo\
├── hello-skills\          ← Demo 3 做好的（不用動）
├── hello-skills-mcp\      ← 5-5 新增：MCP 版 Skill
└── hello-mcp\             ← 5-1 新增：MCP Server
    ├── server.py
    ├── requirements.txt
    ├── .venv\             ← 5-3 自動產生
    └── cache\             ← 5-3 自動產生（日曆快取）
```

> ⚠️ 本手冊的路徑都以 `C:\SkillDemo\` 為例。如果你放在別的地方，後面所有路徑都要換成你的實際路徑。

---

## 5-1 建立 hello-mcp 資料夾

```
hello-mcp/
├── server.py
└── requirements.txt
```

`requirements.txt` 只有一行：

```
mcp
```

## 5-2 server.py

> 不用看懂每一行，先注意三個地方：
> - `@mcp.tool(...)`：底下的函式就是一個「工具」，Claude 會看到它的名稱和說明（`"""` 裡的文字）
> - `get_next_day_off`：**唯讀**工具，查辦公日曆
> - `post_card`：**寫入**工具，把卡片寫進 `outbox.md`（示範用，模擬貼到團隊留言板）

````python
"""hello-mcp：給 hello-skills 用的示範 MCP Server。

提供兩個工具：
  - get_next_day_off(date)  查下一個「真正的」放假日（含國定假日、補假、補班）
  - post_card(card, to)      把問候卡貼到團隊留言板（示範用：寫入本機 outbox.md）

資料來源：
  行政院人事行政總處「政府行政機關辦公日曆表」（data.gov.tw 資料集 14718），
  透過社群整理的 JSON 版本 ruyut/TaiwanCalendar 取得：
  https://cdn.jsdelivr.net/gh/ruyut/TaiwanCalendar/data/{year}.json
  第一次查某年份時下載，之後讀 cache/{year}.json，不會每次呼叫都連網。

執行：
  python server.py           # stdio，給 Claude Desktop / Claude Code 用
  python server.py --http    # Streamable HTTP，http://127.0.0.1:8000/mcp
  python server.py --prefetch 2026   # 先下載並快取 2026 年辦公日曆
"""

import json
import os
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# 相容 MCP Python SDK v2（MCPServer）與 v1（FastMCP）
try:
    from mcp.server.mcpserver import MCPServer as Server
except ImportError:  # mcp < 2
    from mcp.server.fastmcp import FastMCP as Server
from mcp.types import ToolAnnotations

BASE_DIR = Path(__file__).resolve().parent
CACHE_DIR = Path(os.environ.get("HELLO_MCP_CACHE_DIR", BASE_DIR / "cache"))
OUTBOX = Path(os.environ.get("HELLO_MCP_OUTBOX", BASE_DIR / "outbox.md"))
SOURCE_URL = "https://cdn.jsdelivr.net/gh/ruyut/TaiwanCalendar/data/{year}.json"
TAIPEI = timezone(timedelta(hours=8))
WEEKDAYS = "一二三四五六日"

# 和 hello-skills/scripts/weekend.py 用同一套 level，Skill 的後續步驟不用改
LEVELS = {0: "holiday", 1: "tomorrow", 2: "close", 3: "midweek", 4: "far", 5: "monday"}

mcp = Server(
    "hello-mcp",
    instructions="提供台灣政府行政機關辦公日曆（含國定假日、補假、補班），以及示範用的問候卡留言板。",
)

_calendar: dict[str, dict] = {}  # "2026-10-09" -> {"holiday": bool, "desc": str}


class CalendarError(Exception):
    pass


def _load_year(year: int) -> None:
    """載入某一年的辦公日曆：先讀快取，沒有才下載。"""
    cache_file = CACHE_DIR / f"{year}.json"
    if not cache_file.exists():
        try:
            with urllib.request.urlopen(SOURCE_URL.format(year=year), timeout=15) as r:
                raw = r.read()
        except Exception as e:
            raise CalendarError(
                f"無法下載 {year} 年辦公日曆（{e}）。"
                f"請確認網路，或手動下載 {SOURCE_URL.format(year=year)} 存成 {cache_file}。"
            )
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_file.write_bytes(raw)

    rows = json.loads(cache_file.read_text(encoding="utf-8"))
    for row in rows:
        d = row["date"]  # "20261009"
        _calendar[f"{d[:4]}-{d[4:6]}-{d[6:]}"] = {
            "holiday": bool(row["isHoliday"]),
            "desc": row.get("description", "").strip(),
        }


def _day(d: date) -> dict:
    key = d.isoformat()
    if key not in _calendar:
        _load_year(d.year)
    if key not in _calendar:
        raise CalendarError(f"{d.year} 年辦公日曆沒有 {key} 這一天的資料。")
    return _calendar[key]


def _label(d: date) -> str:
    return f"{d:%m/%d}（{WEEKDAYS[d.weekday()]}）"


@mcp.tool(
    annotations=ToolAnnotations(title="查下一個放假日", readOnlyHint=True, openWorldHint=True),
)
def get_next_day_off(date_str: str = "") -> dict:
    """查台灣政府行政機關辦公日曆，回傳下一個放假日與距今天數。
    會考慮國定假日、補假與補班日，比單純用星期幾推算準確。
    做問候卡、回答「還有幾天放假」「這週有沒有連假」時使用。

    date_str：要當作「今天」的日期，格式 YYYY-MM-DD；留空則用台北今天。

    回傳欄位：
      today / today_is_day_off / today_note
      next_day_off（YYYY-MM-DD）、days_left（0 = 今天就放假）
      level：holiday / tomorrow / close / midweek / far / monday（與 weekend.py 相同；超過 5 天為 far）
      holiday_name：放假原因（例如「國慶日」「補假」；一般週末為空字串）
      streak_days / streak_range：這段連續放假共幾天、起訖日
      long_weekend：streak_days >= 3 時為 true
    """
    if date_str:
        try:
            today = date.fromisoformat(date_str)
        except ValueError:
            return {"error": f"date_str 格式應為 YYYY-MM-DD（例如 2026-10-14），收到「{date_str}」。"}
    else:
        today = datetime.now(TAIPEI).date()

    try:
        info = _day(today)
        # 找下一個放假日（最多往後找 60 天）
        d = today
        for _ in range(60):
            if _day(d)["holiday"]:
                break
            d += timedelta(days=1)
        else:
            return {"error": f"{today} 起 60 天內找不到放假日，資料可能有誤。"}
        start = d

        # 連假往前找起點（today 本身就在連假中時）、往後找終點
        while _day(start - timedelta(days=1))["holiday"]:
            start -= timedelta(days=1)
        end = d
        while _day(end + timedelta(days=1))["holiday"]:
            end += timedelta(days=1)
        names = []
        x = start
        while x <= end:
            n = _day(x)["desc"]
            if n and n not in names:
                names.append(n)
            x += timedelta(days=1)
    except CalendarError as e:
        return {"error": str(e)}

    days_left = (d - today).days
    streak = (end - start).days + 1
    weekday_note = "補班日" if (today.weekday() >= 5 and not info["holiday"]) else ""
    return {
        "today": f"{today.isoformat()}（星期{WEEKDAYS[today.weekday()]}）",
        "today_is_day_off": info["holiday"],
        "today_note": info["desc"] or weekday_note,
        "next_day_off": d.isoformat(),
        "next_day_off_label": _label(d),
        "days_left": days_left,
        "level": LEVELS.get(days_left, "far"),
        "holiday_name": "、".join(names),
        "streak_days": streak,
        "streak_range": f"{_label(start)}–{_label(end)}",
        "long_weekend": streak >= 3,
        "source": "行政院人事行政總處 政府行政機關辦公日曆表",
    }


@mcp.tool(
    annotations=ToolAnnotations(
        title="貼出問候卡", readOnlyHint=False, destructiveHint=False, idempotentHint=False
    ),
)
def post_card(card: str, to: str = "全體同仁") -> dict:
    """把做好的問候卡貼到團隊留言板（示範：附加到 hello-mcp/outbox.md）。
    這是「寫入」動作：呼叫前必須先把卡片內容與對象給使用者看，取得同意後才呼叫。

    card：完整卡片文字
    to：要貼給誰（預設「全體同仁」）
    """
    if not card.strip():
        return {"error": "card 不能是空的，請傳入完整卡片文字。"}
    stamp = datetime.now(TAIPEI).strftime("%Y-%m-%d %H:%M")
    with OUTBOX.open("a", encoding="utf-8") as f:
        f.write(f"\n## {stamp} → {to}\n\n```\n{card.strip()}\n```\n")
    return {"ok": True, "posted_at": stamp, "to": to, "outbox": str(OUTBOX)}


if __name__ == "__main__":
    if "--prefetch" in sys.argv:  # 先下載某年辦公日曆到 cache/，例如 python server.py --prefetch 2026
        year = int(sys.argv[sys.argv.index("--prefetch") + 1])
        _load_year(year)
        print(f"已快取 {CACHE_DIR / f'{year}.json'}")
    elif "--http" in sys.argv:
        if Server.__name__ == "FastMCP":  # mcp < 2：host/port 設在 settings
            mcp.settings.host, mcp.settings.port = "127.0.0.1", 8000
            mcp.run(transport="streamable-http")
        else:
            mcp.run(transport="streamable-http", host="127.0.0.1", port=8000)
    else:
        mcp.run()
````

> 💡 工具的說明文字（docstring）就是給 Claude 看的說明書：寫清楚**做什麼、什麼時候用、參數格式、回傳什麼**。錯誤訊息也要寫成 Claude 看得懂、能自己修正的樣子（例如「格式應為 YYYY-MM-DD」）。

## 5-3 建立虛擬環境、安裝、本機測試

在 PowerShell 依序執行：

```powershell
cd C:\SkillDemo\hello-mcp
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

> 為什麼要 venv？讓 hello-mcp 有自己的 Python 環境，不影響電腦上其他程式。
> 本手冊一律寫 `.venv\Scripts\python.exe` 完整路徑，**不需要 activate**。

先下載今年的辦公日曆（存到 `cache\`，之後不用連網）：

```powershell
.venv\Scripts\python.exe server.py --prefetch 2026
```

預期看到：

```
已快取 C:\SkillDemo\hello-mcp\cache\2026.json
```

直接呼叫工具測試一次：

```powershell
.venv\Scripts\python.exe -c "import server; print(server.get_next_day_off('2026-10-09'))"
```

預期結果（重點看這幾個欄位）：

```
'days_left': 0, 'level': 'holiday', 'holiday_name': '補假、國慶日',
'streak_days': 3, 'streak_range': '10/09（五）–10/11（日）', 'long_weekend': True
```

> ✅ 看到 `補假、國慶日`，代表 Server 本身沒問題了。接下來才接上 Claude。

---

## 5-4 接上 Claude Desktop

### 5-4-1 打開設定檔

最保險的方式是**從 Claude Desktop 裡開**：

設定 → **開發者（Developer）** → **編輯設定（Edit Config）**

它會開出 Desktop 實際在讀的 `claude_desktop_config.json`。

> 也可以用 PowerShell：`notepad $env:APPDATA\Claude\claude_desktop_config.json`
> 但如果 Claude Desktop 是從 **Microsoft Store** 安裝的，實際檔案位置可能不同，改這份不會生效。所以建議從 Desktop 裡開。

### 5-4-2 加入 hello-mcp

**檔案是空的、或不存在**：整份貼上：

```json
{
  "mcpServers": {
    "hello-mcp": {
      "command": "C:\\SkillDemo\\hello-mcp\\.venv\\Scripts\\python.exe",
      "args": ["C:\\SkillDemo\\hello-mcp\\server.py"]
    }
  }
}
```

**檔案已經有內容**：不要整份覆蓋，只把 `"hello-mcp": {...}` 加進現有的 `mcpServers` 裡（前一項結尾記得補逗號）：

```json
{
  "preferences": { ... },
  "mcpServers": {
    "其他server": { ... },
    "hello-mcp": {
      "command": "C:\\SkillDemo\\hello-mcp\\.venv\\Scripts\\python.exe",
      "args": ["C:\\SkillDemo\\hello-mcp\\server.py"]
    }
  }
}
```

寫設定檔的三個規定：

- `command` 要寫 **venv 裡的 python.exe**，不能只寫 `python`（Desktop 不會幫你 activate，寫 `python` 會用到系統 Python，出現 `No module named 'mcp'`）
- 路徑裡的反斜線要寫**兩個** `\\`
- 兩個路徑都要是**完整路徑**（從 `C:\` 開始）

### 5-4-3 重開 Claude Desktop

存檔後，**完全結束** Claude Desktop：

- 關掉視窗還不夠，要到右下角**系統匣**，對 Claude 圖示按右鍵 → **結束（Quit）**
- 再重新打開

### 5-4-4 確認有接上

設定 → **開發者（Developer）**，看到 `hello-mcp` 狀態為**執行中（running）**。

開新對話，輸入：

```
你有哪些 hello-mcp 的工具？
```

預期提到 `get_next_day_off` 與 `post_card`。

> 💡 第一次呼叫工具時，Desktop 可能會跳出「是否允許使用這個工具」的確認，選**允許**即可。

---

## 5-5 做 hello-skills-mcp（MCP 版 Skill）

### 5-5-1 複製資料夾

把 `hello-skills` 整個資料夾複製一份，改名為 **`hello-skills-mcp`**。

```
hello-skills-mcp/
├── SKILL.md                    ← 修改
├── references/
│   ├── greetings.md            （不用動）
│   └── weekend-messages.md     ← 修改：多一個 long-weekend 區塊
├── assets/
│   └── card-template.md        ← 修改：多一行資料來源
└── scripts/
    ├── now.py                  （不用動）
    └── weekend.py              （不用動，變成「退路」）
```

### 5-5-2 修改 SKILL.md（整份覆蓋）

> `name` 改成 `hello-skills-mcp`，要和資料夾名稱**一模一樣**。

````markdown
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
````

這份 SKILL.md 比 Demo 3 多了三件事：

| 新增 | 用意 |
|---|---|
| 步驟 2「**優先用 MCP**，沒有或出錯就用 weekend.py」 | 指名要用哪個工具，並寫好**退路** |
| 卡片標示資料來源 | 走退路時，誠實告訴使用者資料不完整 |
| 「貼到留言板」要**先確認**才呼叫 `post_card` | MCP 收到呼叫就會執行，安全規則只能寫在 Skill 裡 |

### 5-5-3 修改 references/weekend-messages.md（整份覆蓋）

````markdown
# 週末倒數鼓勵訊息

## 使用方式
- 依 `get_next_day_off`（或退路 `scripts/weekend.py`）輸出的 `level` 找到對應區塊
- 今天放假而且是連假（`long_weekend` 為 true）時，改用 `long-weekend` 區塊
- 從該區塊挑**一句**使用，可以依使用者的語言翻譯，但意思不要改
- 句子裡的 {N} 換成 `days_left` 的數字，{S} 換成 `streak_days` 的數字

## holiday（今天就是週末）
- 🎉 放假了！今天就好好休息，把電充飽吧～
- 🌴 週末快樂！工作的事先放一邊，享受屬於自己的時間。

## long-weekend（今天放假，而且是連假）
- 🏖️ 連假快樂！這次一共 {S} 天，好好安排、好好放鬆～
- 🎆 {S} 天連假快樂！把時間留給自己和重要的人。

## tomorrow（剩 1 天）
- 🔥 明天就放假了！再撐一天，週末在向你招手～
- 🏁 最後衝刺！今天把事情收尾，明天就能安心放假。

## close（剩 2 天）
- 💪 只剩 {N} 天！週末已經看得到了，加油～
- ☕ 再兩天就自由了，來杯咖啡繼續拚！

## midweek（剩 3 天）
- ⛰️ 一週過一半了！翻過小週末這座山，後面就是下坡。
- 🐫 駝峰日快樂！還有 {N} 天，穩穩前進就好。

## far（剩 4 天，或 6 天以上）
- 🌱 還有 {N} 天，慢慢來，一步一步把事情完成。
- 📋 星期二是最有效率的一天，趁現在把重要的事做掉！

## monday（剩 5 天）
- ☀️ 新的一週開始了！還有 {N} 天，先從一件小事做起。
- 🚀 星期一也可以很有精神，這週一起加油！
````

### 5-5-4 修改 assets/card-template.md（整份覆蓋）

````markdown
<!--
問候卡範本：輸出時把 {{ }} 換成實際內容，其餘文字與符號照原樣保留。
- {{greeting}}：references/greetings.md 查到的問候語
- {{name}}：使用者的名字；沒有提供時，中文填「朋友」，其他語言填「friend」
- {{datetime}}：目前日期與時間，格式 YYYY-MM-DD HH:MM
- {{closing}}：references/greetings.md 的結尾祝福語
- {{weekend}}：放假倒數，依資料來源：
  - A（MCP）：
    - days_left > 0：「距離放假還有 N 天（{next_day_off_label}）」；holiday_name 不是空的就在後面加「・{holiday_name}」；long_weekend 為 true 再加「，連假 {streak_days} 天」
    - days_left = 0：「今天放假！」；holiday_name 不是空的就加「（{holiday_name}）」；long_weekend 為 true 再加「連假 {streak_range}」
  - B（weekend.py 退路）：
    - days_left > 0：「距離週末還有 N 天（MM/DD 星期六）」；days_left = 0：「今天放假！」
- {{source}}：A 寫「依政府行政機關辦公日曆」；B 寫「⚠️ 未含國定假日與補班」
- {{cheer}}：references/weekend-messages.md 挑出的鼓勵訊息
- 非中文時，「，」改成「, 」，「！」改成「!」
-->
━━━━━━━━━━━━━━━━━━━━
👋 {{greeting}}，{{name}}！
🕐 {{datetime}}（台北時間）
📅 {{weekend}}
　 {{source}}
💪 {{cheer}}
💬 {{closing}}
✨ 這張卡片由 Hello Skills（MCP 版）產生
━━━━━━━━━━━━━━━━━━━━
````

### 5-5-5 壓縮、上傳

1. 對 **`hello-skills-mcp` 資料夾本身**按右鍵 →「壓縮至…」→「壓縮檔案」
2. Claude Desktop：設定 → **Skills** → **＋ Add** → **Upload skill** → 選 `hello-skills-mcp.zip`
3. 把舊的 **`hello-skills` 開關關掉**

> ⚠️ 兩個 Skill 的 description 很像，同時開著 Claude 不一定選到 MCP 版（就是 Demo 4 的觸發衝突）。測試時只開 `hello-skills-mcp`。

---

## 5-6 測試：有 MCP 的情況

在 **Claude Desktop 開新對話**，依序輸入：

| 輸入 | 預期結果 |
|---|---|
| `假設今天是 2026-10-09，還有幾天放假？` | 「今天放假！（補假、國慶日）連假 10/09（五）–10/11（日）」，資料來源寫「依政府行政機關辦公日曆」 |
| `假設今天是 2026-10-21，幫我做問候卡` | 「距離放假還有 3 天（10/24（六））・臺灣光復暨金門古寧頭大捷紀念日…，連假 3 天」 |
| `假設今天是 2026-10-14，幫我做問候卡` | 一般週末：「距離放假還有 3 天（10/17（六））」，天數和 Demo 3 相同 |
| `你剛剛用了哪些工具？` | 提到 `get_next_day_off` 與 `now.py` |

卡片範例（10/9）：

```
━━━━━━━━━━━━━━━━━━━━
👋 晚安，〇〇〇！
🕐 2026-10-09 20:05（台北時間）
📅 今天放假！（補假、國慶日）連假 10/09（五）–10/11（日）
　 依政府行政機關辦公日曆
💪 🏖️ 連假快樂！這次一共 3 天，好好安排、好好放鬆～
💬 祝你有美好的一天！
✨ 這張卡片由 Hello Skills（MCP 版）產生
━━━━━━━━━━━━━━━━━━━━
```

> 💡 為什麼要「假設今天是…」？因為 10/9 這種特殊日子不是每天都有。用指定日期，任何時候都能重現補假的情境。

### 寫入動作：先確認再執行

| 輸入 | 預期結果 |
|---|---|
| `做一張問候卡，貼到留言板給教育訓練部` | Claude **先**秀出完整卡片與對象「教育訓練部」，問你是否確認，**還沒**呼叫 `post_card` |
| `確認` | 這時才呼叫 `post_card`；打開 `C:\SkillDemo\hello-mcp\outbox.md` 可以看到卡片 |

---

## 5-7 測試：沒有 MCP 的情況（退路）

不用拆設定檔，最簡單的做法：**到瀏覽器版 claude.ai** 問同一句話。

> 原因：hello-mcp 跑在你的電腦上，網頁版的 Claude 在雲端，連不到你電腦裡的 MCP。

先確認網頁版也有上傳 `hello-skills-mcp`（Skill 是跟著帳號的，通常 Desktop 上傳後網頁版也看得到），然後開新對話輸入：

| 輸入 | 預期結果 |
|---|---|
| `假設今天是 2026-10-09，還有幾天放假？` | 退回 weekend.py：「距離週末還有 1 天（10/10 星期六）」，並標示「⚠️ 未含國定假日與補班」 |
| `做一張問候卡，貼到留言板` | 告知「尚未連接 hello-mcp，無法貼出」，**不會**假裝已經貼出 |

### 三種結果對照

| | 只有 Skill（Demo 3） | Skill ＋ hello-mcp | 沒有 MCP（退路） |
|---|---|---|---|
| 10/9 的結果 | 明天就放假了 ✗ | 今天放假，連假 3 天 ✓ | 還有 1 天 ⚠️ 未含國定假日 |
| 要講的話 | 資料不對，結果就不對 | 打一通電話，拿到真實資料 | 電話不通，也有 B 計畫 |

### ✅ Demo 5 重點

- **Skill 管流程，MCP 管外部資料與動作**：會變動的資料、需要權限的動作交給 MCP；不需要權限的計算（`now.py`）留在 Skill
- **一定要寫退路**：連接器可能斷線，Skill 要寫好 B 計畫，並誠實標示資料不完整
- **安全規則寫在 Skill**：MCP Server 不知道 Skill 存在，收到呼叫就執行；「先給我看過再做」只能寫在 SKILL.md
- **本機 MCP 只在 Claude Desktop、Claude Code 有效**；網頁版要用，必須部署成公開的 HTTPS 服務

---

## 常見問題排除

| 狀況 | 可能原因 | 解法 |
|---|---|---|
| `pip install` 失敗 | 沒有網路，或公司網路擋 PyPI | 換網路，或請 IT 開放 pypi.org |
| `--prefetch` 失敗（無法下載辦公日曆） | 網路擋住 cdn.jsdelivr.net | 換網路；或手動下載錯誤訊息裡的網址，存成 `cache\2026.json` |
| 開發者頁面看不到 hello-mcp | 設定檔改錯份（Microsoft Store 版），或沒有完全結束 Desktop | 從 Desktop「編輯設定」開檔；系統匣也要結束再開 |
| hello-mcp 顯示錯誤／失敗 | `command` 寫成 `python`，出現 `No module named 'mcp'` | 改成 `.venv\Scripts\python.exe` 完整路徑 |
| hello-mcp 顯示錯誤，設定檔看起來沒錯 | 反斜線只寫一個、少逗號、路徑打錯 | 反斜線寫 `\\`；用 https://jsonlint.com 檢查 JSON 格式 |
| 有 MCP 但卡片還是說「明天才放假」 | 觸發到舊的 `hello-skills` | 關掉 `hello-skills` 開關，開新對話再試 |
| 有 MCP 但沒有呼叫工具 | 用的是舊對話，或第一次的工具授權被拒絕 | 開新對話；工具授權選「允許」 |
| 網頁版也呼叫到了 hello-mcp | 不會發生；網頁版連不到本機 MCP | 若看到資料來源寫「依政府行政機關辦公日曆」，確認你是不是其實在 Desktop |

---

## 附錄 A：用 Claude Code 接 hello-mcp

一行指令加入（`-s user`：在任何資料夾執行 `claude` 都能用）：

```powershell
claude mcp add -s user hello-mcp -- C:\SkillDemo\hello-mcp\.venv\Scripts\python.exe C:\SkillDemo\hello-mcp\server.py
claude mcp list
```

看到 `hello-mcp: ... - √ Connected` 即成功。

> 不加 `-s user` 的話，只在執行指令當下的資料夾有效。
> Claude Code 讀的 Skill 在 `C:\Users\<你的帳號>\.claude\skills\`，要把 `hello-skills-mcp` 資料夾複製過去才能用。

## 附錄 B：單獨測試 Server（不經過 Claude）

```powershell
cd C:\SkillDemo\hello-mcp
npx @modelcontextprotocol/inspector .venv\Scripts\python.exe server.py
```

需要先安裝 Node.js。瀏覽器會打開 MCP Inspector，可以看到工具清單、直接呼叫工具看回傳值。

## 附錄 C：完成版資料夾

```
C:\SkillDemo\
├── hello-skills-mcp\              ← Skill：SOP 手冊
│   ├── SKILL.md                   ← 流程：優先用 MCP，沒有就走退路
│   ├── references\
│   │   ├── greetings.md
│   │   └── weekend-messages.md    ← 多了 long-weekend
│   ├── assets\
│   │   └── card-template.md       ← 多了資料來源
│   └── scripts\
│       ├── now.py                 ← 計算機：現在幾點
│       └── weekend.py             ← 退路：只看星期幾
└── hello-mcp\                     ← MCP Server：外線電話
    ├── server.py                  ← get_next_day_off、post_card
    ├── requirements.txt
    ├── .venv\
    ├── cache\2026.json            ← 辦公日曆快取
    └── outbox.md                  ← post_card 寫入的「留言板」
```

參考資料：
- MCP 官方文件：https://modelcontextprotocol.io/
- MCP Python SDK：https://github.com/modelcontextprotocol/python-sdk
- 辦公日曆資料來源：行政院人事行政總處「政府行政機關辦公日曆表」https://data.gov.tw/dataset/14718 （JSON 版：https://github.com/ruyut/TaiwanCalendar）
- 何時用桌面版／網頁版連接器：https://support.claude.com/en/articles/11725091
