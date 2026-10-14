"""計算距離週末（星期六）還有幾天，並給出遠近等級，給 hello-skills 用。

用法：
  python scripts/weekend.py              # 以台北今天計算
  python scripts/weekend.py 2026-10-14   # 指定日期（demo 測試用）
"""
import sys
from datetime import datetime, date, timezone, timedelta

TAIPEI = timezone(timedelta(hours=8))   # 執行環境是 UTC，換成台北時間
WEEKDAYS = ["一", "二", "三", "四", "五", "六", "日"]
LEVELS = {0: "holiday", 1: "tomorrow", 2: "close", 3: "midweek", 4: "far", 5: "monday"}

if len(sys.argv) > 1:
    try:
        today = date.fromisoformat(sys.argv[1])
    except ValueError:
        print("error=日期格式錯誤，請用 YYYY-MM-DD，例如 2026-10-14")
        sys.exit(1)
else:
    today = datetime.now(TAIPEI).date()

wd = today.weekday()                      # 星期一 = 0 … 星期日 = 6
if wd >= 5:                               # 星期六、日：已經放假
    days_left = 0
    saturday = today - timedelta(days=wd - 5)
else:
    days_left = 5 - wd
    saturday = today + timedelta(days=days_left)

print(f"today={today:%Y-%m-%d}（星期{WEEKDAYS[wd]}）")
print(f"saturday={saturday:%Y-%m-%d}（星期六）")
print(f"days_left={days_left}")
print(f"level={LEVELS[days_left]}")
