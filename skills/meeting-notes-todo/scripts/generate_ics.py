#!/usr/bin/env python3
"""
generate_ics.py — 把已換算好日期的待辦事項，轉成一份 .ics 行事曆檔。

用法：
    python generate_ics.py items_with_dates.json output.ics

輸入格式（陣列，通常就是 convert_relative_dates.py 的輸出）：
[
  {"owner": "小徐", "item": "傳送AI應用課程大綱初稿給大家", "due_date": "2026-09-16"},
  {"owner": "阿廷", "item": "完成招生頁面文案", "due_date": null}
]

規則：
- due_date 為 null 的項目會被跳過（不建立事件），因為時間本來就沒有定案，
  硬是排進行事曆反而會誤導使用者以為那天是截止日。
- 每個待辦事項建立一個全天事件（all-day event），標題格式為「[負責人] 待辦事項」。
"""

import sys
import json
import uuid
from datetime import datetime, date, timezone


def escape_ics_text(text):
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def build_ics(items):
    now_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//iSpan//meeting-notes-todo Skill//ZH-TW",
        "CALSCALE:GREGORIAN",
    ]

    skipped = 0
    for item in items:
        due = item.get("due_date")
        if not due:
            skipped += 1
            continue

        owner = item.get("owner", "").strip()
        task = item.get("item", "").strip()
        summary = f"[{owner}] {task}" if owner else task

        # 全天事件：DTSTART 用當天，DTEND 用隔天（iCalendar 全天事件慣例，結束日不含當天）
        due_date = date.fromisoformat(due)
        dtstart = due_date.strftime("%Y%m%d")
        dtend = date.fromordinal(due_date.toordinal() + 1).strftime("%Y%m%d")

        lines += [
            "BEGIN:VEVENT",
            f"UID:{uuid.uuid4()}@ispan-meeting-notes-todo",
            f"DTSTAMP:{now_stamp}",
            f"DTSTART;VALUE=DATE:{dtstart}",
            f"DTEND;VALUE=DATE:{dtend}",
            f"SUMMARY:{escape_ics_text(summary)}",
            "END:VEVENT",
        ]

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n", skipped


def main():
    if len(sys.argv) != 3:
        print("用法：python generate_ics.py items_with_dates.json output.ics", file=sys.stderr)
        sys.exit(1)

    input_path, output_path = sys.argv[1], sys.argv[2]

    with open(input_path, encoding="utf-8") as f:
        items = json.load(f)

    ics_content, skipped = build_ics(items)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ics_content)

    print(f"已產生 {output_path}（跳過 {skipped} 項無明確日期的待辦事項，未排入行事曆）")


if __name__ == "__main__":
    main()
