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
