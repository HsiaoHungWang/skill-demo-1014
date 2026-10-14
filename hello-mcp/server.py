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
