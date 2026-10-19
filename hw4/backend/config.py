"""One place for the shop's AI settings (Problem 12 rules: the model is configurable, never hard-coded twice).

Secrets are NOT here: keys come from environment variables (.env files loaded by db.py) and are never logged.
"""

import os

import db  # noqa: F401  (loads the .env files before we read the environment)

# Text model for the shop agent and the design agent, routed through Portkey with PORTKEY_API_KEY.
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
# Used only if the primary model errors (PydanticAI FallbackModel). Set it to "" to disable.
OPENAI_FALLBACK_MODEL = os.getenv("OPENAI_FALLBACK_MODEL", "gpt-5.6-terra")
PORTKEY_BASE_URL = os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1")

# Agent-loop limits (PydanticAI UsageLimits): each chat message gets at most this many model round trips / tool calls.
SHOP_REQUEST_LIMIT = int(os.getenv("SHOP_REQUEST_LIMIT", "8"))
SHOP_TOOL_CALLS_LIMIT = int(os.getenv("SHOP_TOOL_CALLS_LIMIT", "12"))
DESIGN_REQUEST_LIMIT = int(os.getenv("DESIGN_REQUEST_LIMIT", "3"))
AGENT_RETRIES = 2  # re-asks when the model's structured output fails validation

# --- Public demo controls (web deployment) ------------------------------------------------------
# The features that cost money (chat, design drafting, image creation) can be limited to a time window.
# Empty = no end date (local use). The public Render deployment sets this to 30 days after launch.
PAID_FEATURES_UNTIL = os.getenv("PAID_FEATURES_UNTIL", "").strip()
# Chat rate limits (0 = off). They count chat messages and design drafts together.
CHAT_PER_VISITOR_HOURLY = int(os.getenv("CHAT_PER_VISITOR_HOURLY", "0"))
CHAT_DAILY_CAP = int(os.getenv("CHAT_DAILY_CAP", "0"))


def paid_features_open() -> bool:
    """True while the money-spending features are available (always, if no end date is set)."""
    if not PAID_FEATURES_UNTIL:
        return True
    from datetime import date
    return date.today() <= date.fromisoformat(PAID_FEATURES_UNTIL)


def paid_features_end_label() -> str:
    from datetime import date
    d = date.fromisoformat(PAID_FEATURES_UNTIL)
    return d.strftime("%B %-d, %Y")
