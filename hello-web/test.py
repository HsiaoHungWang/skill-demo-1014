"""STEP 4：確認 API 叫得到 hello-skills-mcp（先不接 MCP，Skill 會走 weekend.py 退路）。"""
import json
from pathlib import Path

from anthropic import Anthropic

lock = json.loads((Path(__file__).parent.parent / "skills" / "claude-lock.json").read_text(encoding="utf-8"))
skill_id = lock["resources"]["./hello-skills-mcp"]["id"]
print("SKILL_ID =", skill_id)

client = Anthropic()  # 自動讀取 ANTHROPIC_API_KEY
resp = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=4096,
    container={"skills": [{"type": "custom", "skill_id": skill_id, "version": "latest"}]},
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}],
    messages=[{"role": "user", "content": "哈囉！假設今天是 2026-10-14，幫我做一張問候卡。"}],
)
for block in resp.content:
    if block.type == "text":
        print(block.text)
