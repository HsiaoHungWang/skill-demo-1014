"""取得台北目前時間與時段，給 hello-skills 查問候語用。"""
from datetime import datetime, timezone, timedelta

# claude.ai 的執行環境是 UTC 時區，所以固定加 8 小時換成台北時間
TAIPEI = timezone(timedelta(hours=8))

now = datetime.now(TAIPEI)
h = now.hour
if 5 <= h < 12:
    period = "morning"
elif 12 <= h < 18:
    period = "afternoon"
else:
    period = "evening"

print(f"datetime={now:%Y-%m-%d %H:%M}")
print(f"period={period}")
