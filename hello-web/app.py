"""
Hello Skills（MCP 版）網頁 Demo — FastAPI 後端

和 call_skills（meeting-notes-todo）同一套架構，多了一件事：
  後端自己當「MCP Host」—— 啟動本機 hello-mcp Server，把它的工具交給 Claude，
  Claude 要用工具時（stop_reason = tool_use），由後端代為呼叫 MCP，再把結果送回去。

  網頁 ─► FastAPI ─► Messages API（skill_id + code_execution + MCP 工具清單）
                 └─► hello-mcp（stdio）：get_next_day_off / post_card

API：
  GET  /                 前端頁面
  GET  /api/status       Skill ID、MCP 連線狀態與工具清單
  POST /api/greet        做問候卡（開新對話）
  POST /api/confirm      使用者在網頁按「確認貼出」後，同一段對話繼續 → 允許 post_card
  GET  /api/outbox       看留言板（hello-mcp/outbox.md）最新內容

API Key 從環境變數 ANTHROPIC_API_KEY 讀取，絕不寫在前端。
"""
import json
import os
import sys
import uuid
from contextlib import AsyncExitStack
from datetime import date
from pathlib import Path
from typing import Any, Literal

from anthropic import AsyncAnthropic
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent

# ── 設定（都可用環境變數覆蓋）────────────────────────────────
MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")
MAX_ROUNDS = 10  # pause_turn 續跑 + tool_use 來回，合計上限
HELLO_MCP_DIR = Path(os.getenv("HELLO_MCP_DIR", BASE_DIR.parent / "hello-mcp"))
_venv_py = HELLO_MCP_DIR / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
HELLO_MCP_PYTHON = os.getenv("HELLO_MCP_PYTHON", str(_venv_py if _venv_py.exists() else sys.executable))
LOCK_FILE = Path(os.getenv("SKILL_LOCK_FILE", BASE_DIR.parent / "skills" / "claude-lock.json"))


def resolve_skill_id() -> str:
    """SKILL_ID 優先用環境變數；沒有就讀 ant apply 產生的 claude-lock.json。"""
    if os.getenv("SKILL_ID"):
        return os.environ["SKILL_ID"]
    if LOCK_FILE.exists():
        lock = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
        for path, res in lock.get("resources", {}).items():
            if res.get("kind") == "skill" and path.rstrip("/").endswith("hello-skills-mcp"):
                return res["id"]
    return ""


SKILL_ID = resolve_skill_id()
SKILLS = [{"type": "custom", "skill_id": SKILL_ID, "version": "latest"}]
CODE_EXEC = {"type": "code_execution_20250825", "name": "code_execution"}

client = AsyncAnthropic()  # 自動讀取 ANTHROPIC_API_KEY
app = FastAPI(title="Hello Skills（MCP 版）Demo")

# 對話暫存（demo 用記憶體即可；正式環境改 Redis／資料庫）
SESSIONS: dict[str, dict] = {}


# ── MCP：後端當 Host，連到本機 hello-mcp ─────────────────────
def mcp_params() -> StdioServerParameters:
    return StdioServerParameters(
        command=HELLO_MCP_PYTHON,
        args=[str(HELLO_MCP_DIR / "server.py")],
        cwd=str(HELLO_MCP_DIR),
    )


async def open_mcp(stack: AsyncExitStack) -> ClientSession:
    read, write = await stack.enter_async_context(stdio_client(mcp_params()))
    session = await stack.enter_async_context(ClientSession(read, write))
    await session.initialize()
    return session


def to_claude_tool(t: Any) -> dict:
    """MCP 工具定義 → Messages API 的 tools 格式（相容 mcp v1 / v2 欄位名稱）。"""
    schema = getattr(t, "input_schema", None) or getattr(t, "inputSchema", None) or {"type": "object"}
    return {"name": t.name, "description": f"[hello-mcp] {t.description or ''}".strip(), "input_schema": schema}


def mcp_result_text(r: Any) -> tuple[str, bool]:
    texts = [c.text for c in r.content if getattr(c, "type", "") == "text"]
    is_error = bool(getattr(r, "is_error", None) or getattr(r, "isError", False))
    return "\n".join(texts) or "{}", is_error


# ── 組指令 ─────────────────────────────────────────────────
class GreetRequest(BaseModel):
    name: str = Field("", max_length=30, description="使用者名字，留空則卡片寫「朋友」")
    language: str = Field("繁體中文", max_length=20)
    as_of: date | None = Field(None, description="測試用：假設今天是哪一天")
    use_mcp: bool = Field(True, description="關掉可示範退路（weekend.py）")
    post_to: str | None = Field(None, max_length=30, description="要貼到留言板給誰；None = 不貼")


class ConfirmRequest(BaseModel):
    session_id: str
    action: Literal["confirm", "cancel"] = "confirm"


def build_prompt(req: GreetRequest) -> str:
    who = f"我是{req.name.strip()}，" if req.name.strip() else ""
    parts = [f"哈囉！{who}請用{req.language}幫我做一張問候卡。"]
    if req.as_of:
        parts.append(f"假設今天是 {req.as_of:%Y-%m-%d}。")
    if req.post_to:
        parts.append(f"做好之後幫我貼到留言板給{req.post_to.strip() or '全體同仁'}。")
    return "\n".join(parts)


# ── 核心：呼叫 Claude，遇到 MCP 工具就代為執行 ─────────────────
def describe_server_tool(block: dict) -> str:
    """把 Skill 在容器裡做的事轉成一句話，給網頁的「執行軌跡」用。"""
    inp = block.get("input") or {}
    cmd = inp.get("command", "")
    if block.get("name") == "text_editor_code_execution":
        return f"讀取 {inp.get('path', '')}" if cmd == "view" else f"{cmd} {inp.get('path', '')}"
    return cmd if isinstance(cmd, str) else json.dumps(inp, ensure_ascii=False)


async def run_claude(sess: dict, mcp: ClientSession | None, tools: list[dict]) -> dict:
    trace: list[dict] = []
    texts: list[str] = []
    usage = {"input_tokens": 0, "output_tokens": 0}
    mcp_tool_names = {t["name"] for t in tools if t.get("input_schema")}

    for _ in range(MAX_ROUNDS):
        container = {"skills": SKILLS}
        if sess.get("container_id"):
            container["id"] = sess["container_id"]
        resp = await client.messages.create(
            model=MODEL,
            max_tokens=4096,
            container=container,
            tools=tools,
            messages=sess["messages"],
        )
        sess["container_id"] = resp.container.id if resp.container else sess.get("container_id")
        usage["input_tokens"] += resp.usage.input_tokens
        usage["output_tokens"] += resp.usage.output_tokens
        sess["messages"].append({"role": "assistant", "content": resp.content})

        tool_results = []
        for b in resp.content:
            if b.type == "text":
                texts.append(b.text)
            elif b.type == "server_tool_use":
                trace.append({"kind": "skill", "label": describe_server_tool(b.model_dump())})
            elif b.type == "tool_use" and b.name in mcp_tool_names:
                tool_results.append(await call_mcp_tool(sess, mcp, b, trace))

        if resp.stop_reason == "pause_turn":  # 長任務：同一個 container 接著跑
            continue
        if resp.stop_reason == "tool_use" and tool_results:
            sess["messages"].append({"role": "user", "content": tool_results})
            continue
        break

    return {"text": "\n\n".join(texts).strip(), "trace": trace, "usage": usage}


async def call_mcp_tool(sess: dict, mcp: ClientSession | None, block: Any, trace: list) -> dict:
    """Claude 要呼叫 MCP 工具 → 後端代為執行。post_card 多一道關卡：使用者要先在網頁按確認。"""
    args = block.input or {}
    shown = {"to": args.get("to", "全體同仁")} if block.name == "post_card" else args  # 卡片全文太長，軌跡只顯示對象
    item = {"kind": "mcp", "label": f"{block.name}({json.dumps(shown, ensure_ascii=False)})"}

    if block.name == "post_card" and not sess.get("confirmed"):
        # 第二道防線：Skill 規定要先問，後端再擋一次，避免 Claude 沒先問就直接貼出
        text, is_error = "尚未取得使用者確認，不能貼出。請先把完整卡片與貼文對象給使用者看，等使用者在網頁上按「確認貼出」。", True
        item["label"] += "　⛔ 已攔下（使用者尚未確認）"
    elif mcp is None:
        text, is_error = "hello-mcp 未連線", True
    else:
        r = await mcp.call_tool(block.name, args)
        text, is_error = mcp_result_text(r)
        if block.name == "post_card" and not is_error:
            sess["posted"] = True
    item["result"] = text[:400]
    trace.append(item)
    return {"type": "tool_result", "tool_use_id": block.id, "content": text, "is_error": is_error}


async def run_turn(sess: dict) -> dict:
    async with AsyncExitStack() as stack:
        mcp, tools = None, [CODE_EXEC]
        if sess["use_mcp"]:
            try:
                mcp = await open_mcp(stack)
                tools += [to_claude_tool(t) for t in (await mcp.list_tools()).tools]
            except Exception as e:  # noqa: BLE001 —— 連不上就當作沒有 MCP，讓 Skill 走退路
                sess.setdefault("notes", []).append(f"hello-mcp 啟動失敗，改走退路：{e}")
                mcp = None
        try:
            out = await run_claude(sess, mcp, tools)
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=f"呼叫 Claude API 失敗：{e}") from e
    out["tools"] = [t["name"] for t in tools]
    out["notes"] = sess.pop("notes", [])
    return out


# ── API ───────────────────────────────────────────────────
@app.get("/api/status")
async def status():
    info = {"skill_id": SKILL_ID or None, "model": MODEL, "mcp": {"ok": False, "tools": []}}
    try:
        async with AsyncExitStack() as stack:
            mcp = await open_mcp(stack)
            info["mcp"] = {"ok": True, "tools": [t.name for t in (await mcp.list_tools()).tools]}
    except Exception as e:  # noqa: BLE001
        info["mcp"]["error"] = str(e)
    return info


@app.post("/api/greet")
async def greet(req: GreetRequest):
    if not SKILL_ID:
        raise HTTPException(400, "找不到 SKILL_ID：請先在 skills 資料夾執行 ant apply hello-skills-mcp，或設定環境變數 SKILL_ID。")
    sid = uuid.uuid4().hex
    sess = {
        "messages": [{"role": "user", "content": build_prompt(req)}],
        "use_mcp": req.use_mcp,
        "want_post": bool(req.post_to),
        "confirmed": False,
        "posted": False,
    }
    SESSIONS[sid] = sess
    out = await run_turn(sess)
    return {"session_id": sid, "prompt": sess["messages"][0]["content"], **out,
            "awaiting_confirm": sess["want_post"] and not sess["posted"], "posted": sess["posted"]}


@app.post("/api/confirm")
async def confirm(req: ConfirmRequest):
    sess = SESSIONS.get(req.session_id)
    if not sess:
        raise HTTPException(404, "對話已過期，請重新產生卡片。")
    if req.action == "cancel":
        sess["want_post"] = False
        return {"text": "已取消，卡片不會貼出。", "trace": [], "usage": {"input_tokens": 0, "output_tokens": 0},
                "awaiting_confirm": False, "posted": False}
    sess["confirmed"] = True
    sess["messages"].append({"role": "user", "content": "確認，貼出去。"})
    out = await run_turn(sess)
    return {**out, "awaiting_confirm": False, "posted": sess["posted"]}


@app.get("/api/outbox")
def outbox():
    f = Path(os.getenv("HELLO_MCP_OUTBOX", HELLO_MCP_DIR / "outbox.md"))
    return {"path": str(f), "content": f.read_text(encoding="utf-8")[-3000:] if f.exists() else ""}


@app.get("/")
def index():
    return FileResponse(BASE_DIR / "static" / "index.html")


app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
