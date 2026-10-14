"""用真正的 MCP 用戶端（stdio）連 server.py，測試工具清單與回傳值。

執行：python tests/test_server.py
使用 tests/fixture-2026.json 當日曆資料（只有 2026 年 10 月的國定假日是真實的），
不會連網，也不會碰到正式的 cache/ 與 outbox.md。
"""
import asyncio
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

HERE = Path(__file__).resolve().parent
SERVER = HERE.parent / "server.py"

CASES = [
    # (假設今天, 預期 days_left, 預期 level, 預期 holiday_name 包含, 預期 streak_days)
    ("2026-10-08", 1, "tomorrow", "國慶日", 3),   # 週四：明天（週五）就補假
    ("2026-10-09", 0, "holiday", "國慶日", 3),    # 週五：今天就是補假
    ("2026-10-14", 3, "midweek", "", 2),          # 一般週三
    ("2026-10-21", 3, "midweek", "補假", 3),      # 週三：週六起光復節連假
]


def payload(result):
    if getattr(result, "structuredContent", None):
        sc = result.structuredContent
        return sc.get("result", sc)
    return json.loads(result.content[0].text)


async def main():
    tmp = Path(tempfile.mkdtemp())
    (tmp / "cache").mkdir()
    shutil.copy(HERE / "fixture-2026.json", tmp / "cache" / "2026.json")
    env = {**os.environ, "HELLO_MCP_CACHE_DIR": str(tmp / "cache"),
           "HELLO_MCP_OUTBOX": str(tmp / "outbox.md")}
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)], env=env)

    failed = 0
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            tools = (await s.list_tools()).tools
            print("工具：", [(t.name, t.annotations.model_dump(by_alias=True, exclude_none=True) if t.annotations else None) for t in tools])

            for day, left, level, name, streak in CASES:
                p = payload(await s.call_tool("get_next_day_off", {"date_str": day}))
                ok = (p["days_left"] == left and p["level"] == level
                      and name in p["holiday_name"] and p["streak_days"] == streak)
                failed += not ok
                print("✅" if ok else "❌", day, "→", p["next_day_off_label"], p["days_left"], "天",
                      p["level"], p["holiday_name"] or "(一般週末)", p["streak_range"])

            p = payload(await s.call_tool("get_next_day_off", {"date_str": "10/14"}))
            ok = "error" in p; failed += not ok
            print("✅" if ok else "❌", "錯誤格式 →", p.get("error"))

            p = payload(await s.call_tool("post_card", {"card": "測試卡片", "to": "教育訓練部"}))
            ok = p.get("ok") and "測試卡片" in (tmp / "outbox.md").read_text(encoding="utf-8")
            failed += not ok
            print("✅" if ok else "❌", "post_card →", p)

    shutil.rmtree(tmp)
    print("全部通過" if not failed else f"{failed} 項失敗")
    sys.exit(1 if failed else 0)


asyncio.run(main())
