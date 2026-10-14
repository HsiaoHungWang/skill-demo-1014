# Hello Skills 操作手冊：從零做出你的第一個 Agent Skill

> 環境：**claude.ai 免費版**（瀏覽器） ＋ 任一文字編輯器（建議 VS Code，記事本也可以）
> 目標：三個 Demo，一步一步把 Skill 從「只有一個檔案」長成「有資料、有範本、有程式」的完整技能包

| Demo | 新增內容 | 學到什麼 |
|---|---|---|
| Demo 1 | `SKILL.md` | 最小可用的 Skill：一個檔案就能用 |
| Demo 2 | `references/`、`assets/` | 資料和範本分開放，用到才讀 |
| Demo 3 | `scripts/` | 精確的事（時間、天數）交給程式 |

---

## 準備工作

1. 用瀏覽器登入 https://claude.ai/
2. 確認設定：左下角帳號 → **設定（Settings）** → **Capabilities**，確認「**程式碼執行（Code execution）**」為開啟（免費版預設已開啟；Demo 3 一定要開）
3. 在電腦上建立一個練習資料夾，例如 `C:\SkillDemo\`

### 寫檔案前的三個規定

- 資料夾名稱必須和 `name` **一模一樣**：`hello-skills`
- 檔名必須寫成 **`SKILL.md`**（SKILL 全大寫）
- 開頭兩條 `---` 之間的 `description` 要寫成**一行**，中間不要按 Enter；冒號用**半形** `:`，後面空一格

### 怎麼壓縮成 ZIP（每個 Demo 都會用到）

1. 在檔案總管中，對 **`hello-skills` 資料夾本身**按右鍵（不是選取裡面的檔案）
2. 選「**壓縮至…**」→「**壓縮檔案**」（不要選 7z）
3. 得到 `hello-skills.zip`，打開確認第一層是 `hello-skills/` 資料夾

### 怎麼上傳到 claude.ai（每個 Demo 都會用到）

1. 設定 → **Skills** → 右上角 **＋ Add** → **Upload skill**
2. 選擇 `hello-skills.zip`
3. 確認清單中出現 `hello-skills`，且開關為開啟
4. **一定要開新對話**再測試（舊對話看不到新上傳的 Skill）

> 💡 更新版本時：建議先在 Skills 清單中，從 `hello-skills` 右側的 **⋮** 選單把舊版刪除，再上傳新版，避免新舊版本混淆。

---

## Demo 1：最小可用的 Skill——只要一個 SKILL.md

### 1-1 建立資料夾與檔案

```
hello-skills/
└── SKILL.md
```

### 1-2 SKILL.md 內容

````markdown
---
name: hello-skills
description: 用活潑的方式跟使用者打招呼並自我介紹。當使用者說「哈囉」「打招呼」「hello skills」或要求測試 Skill 時使用。
---

# Hello Skills

收到招呼時，請依照下面的格式回覆：

1. 開頭固定寫：「👋 Hello Skills 已啟動！」
2. 用一句話說明你是由 Agent Skill 驅動的
3. 加上今天的日期與時間
4. 結尾寫：「這是我的第一個 Skill 🎉」
````

### 1-3 壓縮、上傳

依「準備工作」的步驟，把 `hello-skills` 資料夾壓縮成 ZIP 並上傳。

### 1-4 測試

開新對話，依序輸入：

| 輸入 | 預期結果 |
|---|---|
| `你有哪些 skills？` | 清單中出現 `hello-skills` |
| `哈囉，幫我打個招呼` | 開頭是「👋 Hello Skills 已啟動！」，結尾是「這是我的第一個 Skill 🎉」 |

### ✅ Demo 1 重點

- 一個資料夾＋一個 `SKILL.md`，就是一個可以用的 Skill
- Claude 是看 **description** 決定要不要啟用，所以 description 要寫出「做什麼＋什麼時候用」

---

## Demo 2：資料和範本，分開放——加上 references 與 assets

### 2-1 資料夾結構

```
hello-skills/
├── SKILL.md                 ← 修改
├── references/              ← 新增資料夾
│   └── greetings.md         ← 新增：各語言問候語（給 AI「讀」）
└── assets/                  ← 新增資料夾
    └── card-template.md     ← 新增：問候卡範本（給 AI「用」）
```

> **怎麼分？** 問自己：這份檔案是成品的「依據」還是「外殼」？
> - 要先**看懂**才能做事（對照表、規則）→ `references/`，像員工手冊
> - 會**原樣出現**在成品裡（範本、Logo）→ `assets/`，像公司信紙

### 2-2 references/greetings.md

````markdown
# 各語言問候語

## 使用方式
- 依使用者指定的語言選一列；沒有指定時用「繁體中文」
- 依目前時段選欄位：
  - morning：05:00–11:59
  - afternoon：12:00–17:59
  - evening：18:00–04:59
- 結尾祝福語固定用最後一欄

## 問候語對照表

| 語言 | morning | afternoon | evening | 結尾祝福語 |
|---|---|---|---|---|
| 繁體中文 | 早安 | 午安 | 晚安 | 祝你有美好的一天！ |
| English | Good morning | Good afternoon | Good evening | Have a great day! |
| 日本語 | おはようございます | こんにちは | こんばんは | 良い一日を！ |
| 한국어 | 좋은 아침이에요 | 안녕하세요 | 좋은 저녁이에요 | 좋은 하루 보내세요! |
| Español | Buenos días | Buenas tardes | Buenas noches | ¡Que tengas un buen día! |
| Français | Bonjour | Bonjour | Bonsoir | Bonne journée ! |
| Tiếng Việt | Chào buổi sáng | Chào buổi chiều | Chào buổi tối | Chúc bạn một ngày tốt lành! |

## 規則
- 只能使用表格裡的問候語，不要自己翻譯或另外編寫
- 使用者要的語言不在表格中時，改用 English，並告知使用者目前支援的語言
````

### 2-3 assets/card-template.md

````markdown
<!--
問候卡範本：輸出時把 {{ }} 換成實際內容，其餘文字與符號照原樣保留。
- {{greeting}}：references/greetings.md 查到的問候語
- {{name}}：使用者的名字；沒有提供時，中文填「朋友」，其他語言填「friend」
- {{datetime}}：目前日期與時間，格式 YYYY-MM-DD HH:MM
- {{closing}}：references/greetings.md 的結尾祝福語
- 非中文時，「，」改成「, 」，「！」改成「!」
-->
━━━━━━━━━━━━━━━━━━━━
👋 {{greeting}}，{{name}}！
🕐 {{datetime}}（台北時間）
💬 {{closing}}
✨ 這張卡片由 Hello Skills 產生
━━━━━━━━━━━━━━━━━━━━
````

### 2-4 修改 SKILL.md（整份覆蓋）

````markdown
---
name: hello-skills
description: 依目前時段，用使用者指定的語言打招呼並產出一張問候卡。當使用者說「哈囉」「打招呼」「早安」「做一張問候卡」「hello skills」或要求測試 Skill 時使用，即使沒有明說要問候卡也一樣。若使用者只是要翻譯一句問候語，不適用。
---

# Hello Skills

## 流程
1. 判斷目前時段（morning／afternoon／evening）
2. 判斷使用者要的語言（沒有指定就用繁體中文）
3. 依時段，到 `references/greetings.md` 查問候語與結尾祝福語
4. 讀取 `assets/card-template.md`，依檔案開頭的說明填入所有 {{ }} 後輸出

## 規則
- 問候語只能用 references 裡有的，不要自己編
- 卡片照範本格式輸出，不要另外加東西
````

> 重點：**沒在 SKILL.md 裡寫到的檔案，Claude 不會主動打開**。路徑用相對路徑，例如 `references/greetings.md`。

### 2-5 壓縮、上傳

先刪除舊版 `hello-skills`，再壓縮上傳新版。

### 2-6 測試

開新對話，依序輸入：

| 輸入 | 預期結果 |
|---|---|
| `哈囉，我是〇〇〇` | 產出問候卡，問候語來自 greetings.md |
| `用日文幫我做一張問候卡` | 問候語換成日文（おはようございます／こんにちは／こんばんは） |
| `你剛剛讀了哪些檔案？` | 回答中提到 `greetings.md` 與 `card-template.md` |

### 👀 觀察點（帶出 Demo 3）

看看卡片上的**時間**和**問候語**對不對。claude.ai 的執行環境用 UTC 時區，比台北慢 8 小時，Claude 自己判斷時段時，可能把晚上當成白天，說出「早安」。這種「答案只有一個、錯了就出事」的工作，就該交給程式。

---

## Demo 3：精確的事，交給程式——加上 scripts

### 3-1 資料夾結構

```
hello-skills/
├── SKILL.md                    ← 修改
├── references/
│   ├── greetings.md
│   └── weekend-messages.md     ← 新增：週末倒數鼓勵訊息
├── assets/
│   └── card-template.md        ← 修改：多兩行
└── scripts/                    ← 新增資料夾
    ├── now.py                  ← 新增：台北時間與時段
    └── weekend.py              ← 新增：距離週末天數
```

### 3-2 scripts/now.py

````python
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
````

輸出範例：

```
datetime=2026-10-14 20:05
period=evening
```

### 3-3 scripts/weekend.py

````python
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
````

輸出範例（星期三）：

```
today=2026-10-14（星期三）
saturday=2026-10-17（星期六）
days_left=3
level=midweek
```

| level | 意思 |
|---|---|
| monday | 星期一，剩 5 天 |
| far | 星期二，剩 4 天 |
| midweek | 星期三，剩 3 天 |
| close | 星期四，剩 2 天 |
| tomorrow | 星期五，明天放假 |
| holiday | 星期六、日，今天放假 |

### 3-4 references/weekend-messages.md

> 程式只負責算天數和等級；鼓勵的文字放在 Markdown，不會寫程式的人也能自己改文案。

````markdown
# 週末倒數鼓勵訊息

## 使用方式
- 依 `scripts/weekend.py` 輸出的 `level` 找到對應區塊
- 從該區塊挑**一句**使用，可以依使用者的語言翻譯，但意思不要改
- 句子裡的 {N} 換成 `days_left` 的數字

## holiday（今天就是週末）
- 🎉 放假了！今天就好好休息，把電充飽吧～
- 🌴 週末快樂！工作的事先放一邊，享受屬於自己的時間。

## tomorrow（剩 1 天，星期五）
- 🔥 明天就放假了！再撐一天，週末在向你招手～
- 🏁 最後衝刺！今天把事情收尾，明天就能安心放假。

## close（剩 2 天，星期四）
- 💪 只剩 {N} 天！週末已經看得到了，加油～
- ☕ 再兩天就自由了，來杯咖啡繼續拚！

## midweek（剩 3 天，星期三）
- ⛰️ 一週過一半了！翻過小週末這座山，後面就是下坡。
- 🐫 駝峰日快樂！還有 {N} 天，穩穩前進就好。

## far（剩 4 天，星期二）
- 🌱 還有 {N} 天，慢慢來，一步一步把事情完成。
- 📋 星期二是最有效率的一天，趁現在把重要的事做掉！

## monday（剩 5 天，星期一）
- ☀️ 新的一週開始了！還有 {N} 天，先從一件小事做起。
- 🚀 星期一也可以很有精神，這週一起加油！
````

### 3-5 修改 assets/card-template.md（整份覆蓋）

````markdown
<!--
問候卡範本：輸出時把 {{ }} 換成實際內容，其餘文字與符號照原樣保留。
- {{greeting}}：references/greetings.md 查到的問候語
- {{name}}：使用者的名字；沒有提供時，中文填「朋友」，其他語言填「friend」
- {{datetime}}：目前日期與時間，格式 YYYY-MM-DD HH:MM
- {{closing}}：references/greetings.md 的結尾祝福語
- {{weekend}}：週末倒數，格式「距離週末還有 N 天（MM/DD 星期六）」；放假時寫「今天放假！」
- {{cheer}}：references/weekend-messages.md 挑出的鼓勵訊息
- 非中文時，「，」改成「, 」，「！」改成「!」
-->
━━━━━━━━━━━━━━━━━━━━
👋 {{greeting}}，{{name}}！
🕐 {{datetime}}（台北時間）
📅 {{weekend}}
💪 {{cheer}}
💬 {{closing}}
✨ 這張卡片由 Hello Skills 產生
━━━━━━━━━━━━━━━━━━━━
````

### 3-6 修改 SKILL.md（整份覆蓋）

````markdown
---
name: hello-skills
description: 依台北目前時段，用使用者指定的語言打招呼，並產出一張含週末倒數與鼓勵訊息的問候卡。當使用者說「哈囉」「打招呼」「早安」「做一張問候卡」「還有幾天放假」「離週末還有多久」「hello skills」或要求測試 Skill 時使用，即使沒有明說要問候卡也一樣。若使用者只是要翻譯一句問候語，不適用。
---

# Hello Skills

## 流程
1. 執行 `python scripts/now.py`，取得：
   - `datetime`：台北目前日期時間
   - `period`：目前時段（morning／afternoon／evening）
2. 執行 `python scripts/weekend.py`，取得：
   - `saturday`：本週六的日期
   - `days_left`：距離週末還有幾天（0 代表今天就是週末）
   - `level`：遠近等級
3. 判斷使用者要的語言（沒有指定就用繁體中文）
4. 依 `period`，到 `references/greetings.md` 查問候語與結尾祝福語
5. 依 `level`，到 `references/weekend-messages.md` 挑一句鼓勵訊息，把 {N} 換成 `days_left`
6. 讀取 `assets/card-template.md`，依檔案開頭的說明填入所有 {{ }} 後輸出：
   - {{weekend}}：`days_left` 大於 0 時寫「距離週末還有 N 天（MM/DD 星期六）」，等於 0 時寫「今天放假！」

## 規則
- 時間、時段、天數一律以 scripts 的輸出為準，不要自己推算
- 問候語與鼓勵訊息只能用 references 裡有的，不要自己編
- 卡片照範本格式輸出，不要另外加東西
- 使用者只問「還有幾天放假」時，仍然輸出完整的問候卡

## 測試用
- 使用者指定日期（例如「假設今天是 10/14」）時，改執行 `python scripts/weekend.py 2026-10-14`
````

> 叫用程式要寫清楚三件事：**什麼時候執行**、**執行哪個指令**、**輸出結果怎麼用**。

### 3-7 壓縮、上傳

先刪除舊版 `hello-skills`，再壓縮上傳新版。

### 3-8 測試

開新對話，依序輸入：

| 輸入 | 預期結果 |
|---|---|
| `哈囉，我是〇〇〇` | 問候卡的時間是台北時間，問候語符合目前時段，並出現週末倒數與鼓勵訊息 |
| `還有幾天放假？` | 仍然輸出完整問候卡，週末倒數天數正確 |
| `假設今天是 2026-10-12，幫我做問候卡` | 顯示「距離週末還有 5 天」，鼓勵訊息來自 monday 區塊 |
| `假設今天是 2026-10-17，幫我做問候卡` | 顯示「今天放假！」 |
| `你剛剛執行了哪些程式？` | 回答中提到 `now.py`、`weekend.py` |

卡片範例：

```
━━━━━━━━━━━━━━━━━━━━
👋 晚安，〇〇〇！
🕐 2026-10-14 20:05（台北時間）
📅 距離週末還有 3 天（10/17 星期六）
💪 ⛰️ 一週過一半了！翻過小週末這座山，後面就是下坡。
💬 祝你有美好的一天！
✨ 這張卡片由 Hello Skills 產生
━━━━━━━━━━━━━━━━━━━━
```

### ✅ Demo 3 重點

- AI 擅長理解、判斷、撰寫；程式擅長**每次都要一樣**的事：時間、計算、格式轉換
- 只有程式的**執行結果**會進到對話，程式碼本身不佔 Claude 的閱讀空間
- 規則裡寫明「以 scripts 的輸出為準，不要自己推算」，避免 Claude 蓋掉程式的結果

---

## 常見問題排除

| 狀況 | 可能原因 | 解法 |
|---|---|---|
| 上傳失敗 | 壓縮成 7z，或只壓縮了資料夾裡的檔案 | 對 `hello-skills` 資料夾本身按右鍵 →「壓縮檔案」 |
| 上傳失敗或讀取錯誤 | `name` 和資料夾名稱不同、有大寫或底線；`---` 少一條；冒號是全形「：」 | 對照「寫檔案前的三個規定」檢查 |
| 清單有 Skill，但對話沒反應 | 用的是舊對話 | 開新對話再試 |
| 有觸發，但沒照 references／assets 做 | SKILL.md 沒寫到那個檔案，或路徑打錯 | 確認 SKILL.md 裡的路徑和實際檔名一致 |
| scripts 沒有執行 | 程式碼執行未開啟 | 設定 → Capabilities → 開啟程式碼執行 |
| 兩個 Skill 搶著觸發 | description 用詞重疊 | 切乾淨職責，加一句「若是〇〇，改用 X」；或直接點名 Skill |
| 時段不對（晚上說早安） | 沒有用 now.py，Claude 用 UTC 自己推算 | 確認是 Demo 3 版本，並問 Claude「你剛剛執行了哪些程式？」 |

---

## 附錄：完成版資料夾

```
hello-skills/
├── SKILL.md                  ← 主說明：做什麼、何時用、流程與規則
├── references/               ← 給 AI「讀」：要看懂才能做事
│   ├── greetings.md
│   └── weekend-messages.md
├── assets/                   ← 給 AI「用」：原樣出現在成品
│   └── card-template.md
└── scripts/                  ← 交給程式：每次都要一樣的事
    ├── now.py
    └── weekend.py
```

參考資料：
- Agent Skills 規格：https://agentskills.io/specification
- Skill 撰寫最佳實踐：https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
