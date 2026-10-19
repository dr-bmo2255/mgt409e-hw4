"""Public-demo guards for the features that cost money (chat and design drafting).

- A time window (config.PAID_FEATURES_UNTIL): after the date, these features politely close.
- A per-visitor hourly limit and a site-wide daily cap (config.CHAT_PER_VISITOR_HOURLY / CHAT_DAILY_CAP).
Counts are kept in memory: enough for a small class demo (a restart resets them, which only ever errs low).
Image creation has its own stricter limits in custom.py, and runs in free mock mode on the public site.
"""

import threading
import time
from collections import defaultdict, deque
from datetime import date

from fastapi import Request

import config

_lock = threading.Lock()
_visitor_hits: dict[str, deque[float]] = defaultdict(deque)
_daily = {"day": None, "count": 0}


def visitor_key(request: Request, user: dict | None) -> str:
    if user:
        return f"user:{user['id']}"
    forwarded = request.headers.get("x-forwarded-for", "")  # Render's proxy puts the visitor's IP first
    ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "?")
    return f"ip:{ip}"


def check(request: Request, user: dict | None) -> str | None:
    """None if this request may use a paid feature; otherwise the reason ('closed', 'visitor', 'daily')."""
    if not config.paid_features_open():
        return "closed"
    now = time.time()
    with _lock:
        if config.CHAT_PER_VISITOR_HOURLY:
            hits = _visitor_hits[visitor_key(request, user)]
            while hits and hits[0] < now - 3600:
                hits.popleft()
            if len(hits) >= config.CHAT_PER_VISITOR_HOURLY:
                return "visitor"
        today = date.today().isoformat()
        if _daily["day"] != today:
            _daily.update(day=today, count=0)
        if config.CHAT_DAILY_CAP and _daily["count"] >= config.CHAT_DAILY_CAP:
            return "daily"
        if config.CHAT_PER_VISITOR_HOURLY:
            _visitor_hits[visitor_key(request, user)].append(now)
        _daily["count"] += 1
    return None


MESSAGES = {
    "closed": {
        "brand": "The live chat demo ran through {until} and is now closed. You can still browse every product, and the full project (with instructions to run the chat yourself) is on GitHub.",
        "dan": "*curls up for a long nap* The live chat demo ran through {until}, chum, so I'm off duty now. You can still browse all the gear, and you can run me yourself from the GitHub project!",
    },
    "visitor": {
        "brand": "You've reached this demo's limit of {n} chat messages per hour. Please try again a little later.",
        "dan": "*pants happily* Whew, that's {n} questions this hour, chum! Even a champion bulldog needs a breather. Try me again in a little while.",
    },
    "daily": {
        "brand": "The demo chat has reached its daily limit. Please try again tomorrow.",
        "dan": "*flops down after a big day* I've answered all the questions I'm allowed today, chum. Come back tomorrow and I'll fetch you more gear!",
    },
}


def message(reason: str, voice: str) -> str:
    until = config.paid_features_end_label() if config.PAID_FEATURES_UNTIL else ""
    return MESSAGES[reason][voice if voice in ("brand", "dan") else "brand"].format(until=until, n=config.CHAT_PER_VISITOR_HOURLY)
