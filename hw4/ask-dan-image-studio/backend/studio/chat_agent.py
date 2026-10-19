"""Studio chat agent (PydanticAI): turns a plain-language request into a structured image brief
for a ONE-OFF Dan image (it does not need to be in the catalogue), or into revision feedback
for an image already in the studio.

The agent only drafts. It cannot generate, approve or spend money: the user's button press does
that, through the same guards as everything else (authorization, caps, attempt limits).
"""

from __future__ import annotations

import json
import os
import time

from pydantic import BaseModel, Field

from . import config, state
from .prompts import IDENTITY, NEGATIVES

CHAT_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")  # same setting as the shop (Problem 12 rule)


class ImageBrief(BaseModel):
    display_name: str = Field(description="Short title, e.g. 'Dan as Yale cheerleader'. No institution names prefixed with 'Dan'.")
    setting: str = Field(description="Specific, vivid location (Yale-flavored when it fits; avoid the generic autumn Gothic steps + books + mug template)")
    outfit: str = Field(description="What Dan wears / carries")
    pose: str = Field(description="Pose or action; physically plausible for an English bulldog")
    humor: str = Field(description="The joke or charming detail")
    permitted_text: list[str] = Field(default_factory=list, max_length=8,
                                      description="The ONLY words allowed in the image, exactly spelled (e.g. ['YALE']). Empty = no text.")
    shield_slug: str | None = Field(default=None, description="One of the supplied shield slugs if an official Yale shield belongs on the image, else null")


class StudioReply(BaseModel):
    reply: str = Field(description="Short, friendly message to the user (what you drafted / what you need)")
    brief: ImageBrief | None = Field(default=None, description="A NEW image brief to show as a draft card, when the user asks for a new image")
    revise_asset_id: str | None = Field(default=None, description="asset_id of an existing studio image the user wants changed")
    revise_feedback: str | None = Field(default=None, description="Precise revision instruction for that image (what to change, what to keep)")


def _instructions(shields: list[dict], assets: list[dict], focus_asset: str | None) -> str:
    shield_list = ", ".join(f"{s['slug']} ({s['label']})" for s in shields)
    recent = ", ".join(f"{a['asset_id']} [{a['status']}]" for a in assets[-25:])
    return f"""You are the art director inside "Ask Dan Image Studio", helping the user create photorealistic images of
Handsome Dan (Yale's English bulldog mascot). You turn requests into precise image briefs. You never generate,
approve or spend money yourself: the user clicks Generate, which shows the cost first.

Rules for every brief:
- {IDENTITY}
- {NEGATIVES}
- Exact text matters: list every readable word in permitted_text, spelled exactly. Never write "Dan <Institution>".
  Use correct full Yale names (e.g. "Trumbull College", "School of Management").
- Shields: only these supplied official shields exist: {shield_list}. Set shield_slug only if one of them truly belongs
  in the image; otherwise null. Never describe or invent any other crest.
- Make scenes distinct, specific and playful; Dan stays the clear hero, a real dog (no human substitute).
- One-off images do NOT need to be in the catalogue.

How to respond:
- New image idea → return `brief` (and a 1–2 sentence reply summarizing it). Ask a short clarifying question only if the
  request is truly ambiguous.
- Change to an existing image → set revise_asset_id and revise_feedback (say what to change AND what to keep). Existing
  studio assets: {recent or "none"}.{f' The user is currently looking at {focus_asset}; "this"/"it" means that one.' if focus_asset else ''}
- Questions about the studio → answer briefly in `reply`.
"""


def _agent():
    from openai import AsyncOpenAI
    from pydantic_ai import Agent
    from pydantic_ai.models.openai import OpenAIResponsesModel
    from pydantic_ai.providers.openai import OpenAIProvider

    os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
    if key := os.getenv("PORTKEY_API_KEY"):  # chat uses the class Portkey key (works for text models)
        client = AsyncOpenAI(base_url=os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1"), api_key=key,
                             default_headers={"x-portkey-api-key": key})
    elif key := os.getenv("OPENAI_API_KEY"):
        client = AsyncOpenAI(api_key=key)
    else:
        raise RuntimeError("No PORTKEY_API_KEY or OPENAI_API_KEY for the chat agent")
    return Agent(OpenAIResponsesModel(CHAT_MODEL, provider=OpenAIProvider(openai_client=client)), output_type=StudioReply)


# Tests replace this with a fake.
RUNNER = None


def history(limit: int = 60) -> list[dict]:
    with state.db() as c:
        rows = [dict(r) for r in c.execute("SELECT * FROM chat_messages ORDER BY id DESC LIMIT ?", (limit,))]
    for r in rows:
        r["brief"] = json.loads(r["brief"]) if r["brief"] else None
    return list(reversed(rows))


def save(role: str, content: str, brief: dict | None = None, revise_feedback: str | None = None, asset_id: str | None = None) -> int:
    with state.db() as c:
        cur = c.execute("INSERT INTO chat_messages (role, content, brief, revise_feedback, asset_id, created_at) VALUES (?,?,?,?,?,?)",
                        (role, content, json.dumps(brief) if brief else None, revise_feedback, asset_id, time.time()))
        return cur.lastrowid


async def respond(message: str, focus_asset: str | None, manifest: dict, asset_states: dict) -> dict:
    from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, UserPromptPart

    past = history(30)
    save("user", message, asset_id=focus_asset)
    assets = [{"asset_id": a["asset_id"], "status": asset_states.get(a["asset_id"], {}).get("status", a["status"])}
              for a in manifest["assets"] if a.get("custom") or asset_states.get(a["asset_id"], {}).get("version_count")]
    instructions = _instructions(manifest["references"]["shields"], assets, focus_asset)
    msgs = []
    for h in past:
        content = h["content"] + (f"\n[brief drafted: {json.dumps(h['brief'])}]" if h["brief"] else "")
        msgs.append(ModelRequest(parts=[UserPromptPart(content=content)]) if h["role"] == "user" else ModelResponse(parts=[TextPart(content=content)]))
    if RUNNER is not None:
        out: StudioReply = await RUNNER(message, instructions, msgs)
    else:
        result = await _agent().run(message, instructions=instructions, message_history=msgs)
        out = result.output
    brief = out.brief.model_dump() if out.brief else None
    if brief and brief.get("shield_slug") and brief["shield_slug"] not in {s["slug"] for s in manifest["references"]["shields"]}:
        brief["shield_slug"] = None  # never pass through an invented shield
    target = out.revise_asset_id if out.revise_asset_id in {a["asset_id"] for a in manifest["assets"]} else None
    mid = save("assistant", out.reply, brief, out.revise_feedback if target else None, target)
    return {"id": mid, "reply": out.reply, "brief": brief, "revise_asset_id": target,
            "revise_feedback": out.revise_feedback if target else None}


__all__ = ["respond", "history", "save", "ImageBrief", "StudioReply", "config"]
