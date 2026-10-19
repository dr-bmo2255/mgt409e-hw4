"""Design with Dan: turns a customer's idea into a DesignBrief (Problem 10 Part C).

Same Portkey model as the shop agent. It only drafts: the customer sees the brief and presses
"Create this Dan", which goes through custom.create_design (sign-in, daily limits, budget, moderation).
"""

import logging

from fastapi import APIRouter, Cookie, HTTPException
from pydantic import BaseModel, Field
import time

from pydantic_ai import Agent, capture_run_messages
from pydantic_ai.usage import UsageLimits

import audit
import config
import custom
import dan_voice
import agent as agent_module
from agent import _build_model, _is_content_filter
from auth import current_user
from models import DesignBrief, DraftedBrief

log = logging.getLogger("campus_customs.design")

INSTRUCTIONS = """You are Handsome Dan's art director at Campus Customs (Yale gear shop, New Haven). A customer describes a
custom image of Handsome Dan (Yale's brown-and-white English bulldog mascot) to print on Custom Dan Gear: a tee, crewneck,
hoodie, mousepad, insulated cup, notebook or folder. Turn their idea into a `brief`.

A good brief:
- One continuous, specific, playful scene. Dan is a real bulldog and the clear hero, doing something physically plausible.
- Yale and New Haven flavor is welcome (Yale Bowl, Old Campus, Sterling Library, residential colleges, Harvard rivalry jokes).
- `style`: "photo" by default; "sticker" when they ask for a cartoon, illustration, logo-like, sticker or "no background" look.
  A sticker `scene` describes only Dan, his outfit, pose and a few props he's holding or touching: no setting or background.
- `text`: only words they explicitly want printed, spelled exactly (e.g. "BOOLA BOOLA"). Usually empty. Max 3 short phrases.
- `title`: short and fun, e.g. "Dan the Yale Bowl quarterback".

Guardrails. NEVER draft any of these (return brief = null):
- anything sexual or suggestive (including innuendo, lingerie, "sexy" poses)
- foul language: no swearing, slurs or rude words or gestures, in the scene or in `text`, even censored (f***)
- anything disparaging any group of people: race, ethnicity, nationality, religion, gender, sexual orientation,
  disability, age, body type, income, or any other demographic. No stereotypes or caricatures of people.
- overly violent images: blood, gore, injuries, real weapons aimed at anyone, cruelty to animals, death, or Dan hurt
  or scared.
- real or famous people, other brands, logos, trademarked characters, other schools' logos or crests, political content,
  alcohol or drugs. Yale crests and shields are also not available here.
ALLOWED: good-natured CARTOON rivalry with other schools, written as harmless slapstick, e.g. Dan bowling over a Harvard
lineman in crimson, Dan chasing a cartoon Princeton tiger up a tree, Dan side-eyeing a Harvard fan. Nobody gets hurt,
no blood, no weapons, and no school logos (team colors are fine). Write those scenes so the slapstick is obvious.

When you decline: `reply` is in HANDSOME DAN'S OWN VOICE, clever and kind, never preachy. Dan is a preppy Yale bulldog:
start with one short dog action in *italics* (e.g. *buries the idea in the Old Campus lawn*), give a witty one-line reason,
then pitch a fun alternative he WOULD pose for. Don't repeat the shopper's offensive words.
Requests unrelated to designing a Dan image: answer briefly and steer back.

If the idea is too vague (e.g. "something cool"), draft a fun Yale-flavored scene anyway rather than asking questions.
`reply` for a drafted design: 1–2 friendly sentences about it (no prices, no promises about delivery dates), and mention
that finished designs are saved in their account for 90 days. Never mention the 90 days when you decline."""


class DesignDraft(BaseModel):
    reply: str = Field(description="1–2 friendly sentences for the customer")
    brief: DesignBrief | None = Field(default=None, description="The drafted design, or null if it can't be made")


design_agent = Agent(_build_model(), output_type=DesignDraft, instructions=INSTRUCTIONS, retries=config.AGENT_RETRIES, name="dan_design")

router = APIRouter(prefix="/api/custom", tags=["custom"])


class BriefIn(BaseModel):
    idea: str = Field(min_length=3, max_length=500)
    style: str | None = Field(default=None, pattern="^(photo|sticker)$")


class BriefOut(BaseModel):
    reply: str
    brief: DraftedBrief | None = None


@router.post("/briefs", response_model=BriefOut)
async def draft_brief(body: BriefIn, cc_session: str | None = Cookie(default=None)) -> BriefOut:
    user = current_user(cc_session)
    if not user:
        raise HTTPException(401, "Please log in to design with Dan.")
    if not agent_module.HAS_KEY:
        raise HTTPException(503, "Design drafting isn't set up: add PORTKEY_API_KEY to hw4/.env and restart the backend.")
    try:
        custom.check_text(body.idea)  # brands, foul language, hate symbols: refused for free, in Dan's voice
    except custom.Refused as e:
        return BriefOut(reply=str(e))
    prompt = body.idea.strip() + (f"\n(Preferred style: {body.style})" if body.style else "")
    run_id, started = audit.new_run_id(), time.time()
    ctx = {"style": body.style, "idea_chars": len(body.idea)}
    with capture_run_messages() as messages:
        try:
            result = await design_agent.run(prompt, usage_limits=UsageLimits(request_limit=config.DESIGN_REQUEST_LIMIT))
        except Exception as exc:
            reason = "content_filter (Dan refusal sent)" if _is_content_filter(exc) else f"error: {type(exc).__name__}"
            audit.record_run(agent="dan_design", run_id=run_id, model=config.OPENAI_MODEL, started=started,
                             messages=messages, stop_reason=reason, context=ctx)
            if _is_content_filter(exc):
                return BriefOut(reply=dan_voice.refusal("unsafe"))
            log.exception("design agent failed")
            raise HTTPException(502, "Dan's art director is busy right now. Please try again.")
    out = result.output
    audit.record_run(agent="dan_design", run_id=run_id, model=config.OPENAI_MODEL, started=started,
                     messages=result.new_messages(), stop_reason="final_output" if out.brief else "final_output (declined in Dan's voice)",
                     context=ctx, usage=result.usage, outcome={"brief_drafted": out.brief is not None})
    if out.brief:
        try:  # the agent's own words must pass the same local checks (e.g. foul words slipped into `text`)
            custom.check_text(" ".join([out.brief.title, out.brief.scene, *out.brief.text]))
        except custom.Refused as e:
            return BriefOut(reply=str(e))
    if out.brief and body.style:
        out.brief.style = body.style  # an explicit choice on the page wins
    return BriefOut(reply=out.reply, brief=custom.save_brief(out.brief, user["id"]) if out.brief else None)
