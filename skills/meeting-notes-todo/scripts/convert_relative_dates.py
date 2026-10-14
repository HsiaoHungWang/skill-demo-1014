#!/usr/bin/env python3
"""
convert_relative_dates.py — 把會議紀錄中常見的相對時間敘述，換算成具體日期。

用法：
    python convert_relative_dates.py input.json meeting_date

input.json 格式（陣列，每個待辦事項一筆）：
[
  {"owner": "小徐", "item": "傳送AI應用課程大綱初稿給大家", "relative": "這兩天"},
  {"owner": "阿廷", "item": "完成招生頁面文案", "relative": "本週內"},
  {"owner": "小徐", "item": "確認開班時間", "relative": "待定"}
]

meeting_date 格式：YYYY-MM-DD（會議發生的日期，作為換算基準）

輸出：同樣結構的JSON，每筆多一個 "due_date" 欄位（YYYY-MM-DD 或 null）。
無法判斷的敘述（例如「盡快」「待定」「時間待定」）回傳 null，
代表這項需要人工確認，不強行猜一個日期。
"""

import sys
import json
import re
from datetime import date, timedelta
import calendar

# 中文數字轉阿拉伯數字（只涵蓋常見的1-2位數，日期換算夠用）
CN_NUM = {
    "一": 1, "二": 2, "兩": 2, "三": 3, "四": 4, "五": 5,
    "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
}


def cn_to_int(s):
    if s.isdigit():
        return int(s)
    if s in CN_NUM:
        return CN_NUM[s]
    return None


def last_day_of_month(year, month):
    return calendar.monthrange(year, month)[1]


WEEKDAY_MAP = {"一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 6, "天": 6}


def resolve(relative_text, meeting_date):
    """回傳 date 物件，或 None（代表無法判斷，需人工確認）"""
    if not relative_text:
        return None
    text = relative_text.strip()

    # 無法判斷的模糊字眼
    vague_markers = ["待定", "盡快", "不會太久", "還沒有明確", "沒辦法給明確", "尚未"]
    if any(m in text for m in vague_markers):
        return None

    # 「這N天」「這兩天內」
    m = re.search(r"這([一二兩三四五六七八九十\d]+)天", text)
    if m:
        n = cn_to_int(m.group(1))
        if n:
            return meeting_date + timedelta(days=n)

    # 「N天內」
    m = re.search(r"([一二兩三四五六七八九十\d]+)天內", text)
    if m:
        n = cn_to_int(m.group(1))
        if n:
            return meeting_date + timedelta(days=n)

    # 「N週內」「兩週內」
    m = re.search(r"([一二兩三四五六七八九十\d]+)週內", text)
    if m:
        n = cn_to_int(m.group(1))
        if n:
            return meeting_date + timedelta(weeks=n)

    # 「本週內」「這週五前」→ 當週週五
    if "本週" in text or "這週" in text:
        days_to_friday = (4 - meeting_date.weekday()) % 7
        return meeting_date + timedelta(days=days_to_friday)

    # 「下週X前」「下週三前」
    m = re.search(r"下週([一二三四五六日天])", text)
    if m:
        wd = WEEKDAY_MAP.get(m.group(1))
        if wd is not None:
            days_ahead = (7 - meeting_date.weekday()) + wd
            return meeting_date + timedelta(days=days_ahead)

    # 「N月底」
    m = re.search(r"(\d{1,2})月底", text)
    if m:
        month = int(m.group(1))
        year = meeting_date.year if month >= meeting_date.month else meeting_date.year + 1
        return date(year, month, last_day_of_month(year, month))

    # 「N月中」
    m = re.search(r"(\d{1,2})月中", text)
    if m:
        month = int(m.group(1))
        year = meeting_date.year if month >= meeting_date.month else meeting_date.year + 1
        return date(year, month, 15)

    # 「本週五」之類，找不到規則就放棄，交給人工確認
    return None


def main():
    if len(sys.argv) != 3:
        print("用法：python convert_relative_dates.py input.json YYYY-MM-DD", file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    meeting_date = date.fromisoformat(sys.argv[2])

    with open(input_path, encoding="utf-8") as f:
        items = json.load(f)

    for item in items:
        resolved = resolve(item.get("relative", ""), meeting_date)
        item["due_date"] = resolved.isoformat() if resolved else None

    print(json.dumps(items, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
