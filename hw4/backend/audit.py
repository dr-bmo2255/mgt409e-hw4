"""Append-only audit trail of agent-loop activity (Problem 12): output/audit_trail.json.

Every agent run (shop chat and Design with Dan) adds entries: run_start, each tool_call and tool_result, and run_end
with the stop reason. The file is one JSON array. New entries are added by rewriting only the closing "]" at the end
of the file, so earlier entries are never changed or removed, and nothing ever wipes it between runs.

Privacy: no secrets, passwords or full customer messages are written. Arguments and results are short summaries
(max ~200 characters) with email addresses and long digit runs masked.
"""

import fcntl
import json
import re
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from pydantic_ai.messages import ModelRequest, ModelResponse, RetryPromptPart, ToolCallPart, ToolReturnPart

from db import PROJECT_DIR

from db import PERSIST_DIR  # noqa: E402

# On the hosted demo the trail lives on the persistent disk, so it's never wiped by a redeploy.
AUDIT_PATH = (PERSIST_DIR / "audit_trail.json") if PERSIST_DIR else PROJECT_DIR / "output" / "audit_trail.json"
_lock = threading.Lock()
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
DIGITS = re.compile(r"\d{7,}")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def short(value, limit: int = 200) -> str:
    """A compact, privacy-safe one-line summary of tool arguments or results."""
    if hasattr(value, "model_dump"):
        value = value.model_dump(exclude_none=True)
    text = value if isinstance(value, str) else json.dumps(value, default=str, ensure_ascii=False)
    text = DIGITS.sub("[number]", EMAIL.sub("[email]", text))
    text = re.sub(r"\s+", " ", text)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def append(entries: list[dict]) -> None:
    """Append entries to the JSON array without touching what's already there."""
    if not entries:
        return
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    body = ",\n".join(json.dumps(e, ensure_ascii=False) for e in entries).encode()
    with _lock, open(AUDIT_PATH, "a+b") as f:
        fcntl.flock(f, fcntl.LOCK_EX)  # also safe across processes (e.g. two uvicorn workers)
        try:
            f.seek(0, 2)
            size = f.tell()
            if size == 0:
                f.write(b"[\n" + body + b"\n]\n")
                return
            # Find the closing bracket near the end and replace only it.
            tail_len = min(size, 64)
            f.seek(size - tail_len)
            tail = f.read(tail_len)
            close = tail.rfind(b"]")
            if close == -1:  # unexpected: never rewrite old content, just keep appending
                f.write(b",\n" + body + b"\n]\n")
                return
            f.truncate(size - tail_len + close)
            f.seek(0, 2)
            sep = b"\n" if f.tell() <= 2 else b",\n"  # "[\n]" (empty array) needs no comma
            f.write(sep + body + b"\n]\n")
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def new_run_id() -> str:
    return uuid.uuid4().hex[:12]


def record_run(*, agent: str, run_id: str, model: str, started: float, messages: list, stop_reason: str,
               context: dict | None = None, outcome: dict | None = None, usage=None) -> None:
    """Turn one agent run's messages into audit entries: start, each tool call/result, end."""
    entries = [{"time": datetime.fromtimestamp(started, timezone.utc).isoformat(timespec="milliseconds"),
                "event": "run_start", "agent": agent, "run_id": run_id, "model": model, **(context or {})}]
    tool_names: dict[str, str] = {}
    requests = tool_calls = 0
    for m in messages:
        if isinstance(m, ModelResponse):
            requests += 1
            for part in m.parts:
                if isinstance(part, ToolCallPart):
                    tool_calls += 1
                    tool_names[part.tool_call_id] = part.tool_name
                    entries.append({"time": m.timestamp.isoformat(timespec="milliseconds"), "event": "tool_call",
                                    "agent": agent, "run_id": run_id, "tool": part.tool_name, "args": short(part.args)})
        elif isinstance(m, ModelRequest):
            for part in m.parts:
                if isinstance(part, ToolReturnPart):
                    entries.append({"time": part.timestamp.isoformat(timespec="milliseconds"), "event": "tool_result",
                                    "agent": agent, "run_id": run_id, "tool": part.tool_name, "result": short(part.content)})
                elif isinstance(part, RetryPromptPart) and part.tool_name:
                    entries.append({"time": part.timestamp.isoformat(timespec="milliseconds"), "event": "tool_retry",
                                    "agent": agent, "run_id": run_id, "tool": part.tool_name, "result": short(part.content)})
    end = {"time": _now(), "event": "run_end", "agent": agent, "run_id": run_id, "stop_reason": stop_reason,
           "model_requests": requests, "tool_calls": tool_calls, "duration_ms": round((time.time() - started) * 1000)}
    if usage is not None:
        end["tokens"] = {"input": getattr(usage, "input_tokens", None), "output": getattr(usage, "output_tokens", None)}
    if outcome:
        end.update(outcome)
    entries.append(end)
    try:
        append(entries)
    except OSError:  # the audit trail must never break a customer's chat
        pass
