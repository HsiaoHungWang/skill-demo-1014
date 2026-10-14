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
