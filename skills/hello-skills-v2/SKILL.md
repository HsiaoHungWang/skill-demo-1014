---
name: hello-skills
description: 依目前時段，用使用者指定的語言打招呼並產出一張問候卡。當使用者說「哈囉」「打招呼」「做一張問候卡」「hello skills」或要求測試 Skill 時使用，即使沒有明說要問候卡也一樣。
---

# Hello Skills

## 流程
1. 判斷使用者要的語言（沒有指定就用繁體中文）
2. 判斷目前時段，到 `references/greetings.md` 查對應的問候語與結尾祝福語
3. 讀取 `assets/card-template.md`，把 {{ }} 換成實際內容後輸出

## 規則
- 問候語只能用 references 裡有的，不要自己編
- 卡片照範本格式輸出，不要另外加東西