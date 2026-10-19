"""Accounts: signup, login, logout, current user.

Passwords are stored as  pbkdf2_sha256$<salt>$<hex digest>  (PBKDF2-HMAC-SHA256,
120,000 iterations) — the same format as the seeded users. We never decrypt or
"unhash" anything: login re-hashes what the user typed with the salt read from
the stored string and compares digests in constant time.
"""

import base64
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import time
from collections import defaultdict, deque

from fastapi import APIRouter, Cookie, HTTPException, Request, Response
from pydantic import BaseModel

from db import connect

# --- Password hashing (signup and login share these settings) ----------------

HASH_SCHEME = "pbkdf2_sha256"
HASH_ITERATIONS = 120_000
SALT_BYTES = 8  # rendered as 16 hex characters, matching the seeded rows


def _pbkdf2(password: str, salt: str) -> str:
    # The salt is used exactly as stored (its text), so seeded salts like
    # "hw4testsalt0001" and our generated hex salts both work.
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), HASH_ITERATIONS)
    return digest.hex()


def hash_password(password: str) -> str:
    """New accounts only: fresh random salt per user."""
    salt = secrets.token_hex(SALT_BYTES)
    return f"{HASH_SCHEME}${salt}${_pbkdf2(password, salt)}"


def verify_password(password: str, stored: str) -> bool:
    """Login: read the salt from the stored string, re-hash, constant-time compare."""
    try:
        scheme, salt, expected = stored.split("$", 2)
    except ValueError:
        return False
    if scheme != HASH_SCHEME:
        return False
    return hmac.compare_digest(_pbkdf2(password, salt), expected)


# Used when the email doesn't exist, so a wrong email takes as long as a wrong password
# (prevents discovering which emails have accounts by timing the response).
_DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


# --- Sessions: HMAC-signed, HttpOnly cookie ----------------------------------

SESSION_COOKIE = "cc_session"
SESSION_TTL = 60 * 60 * 24 * 7  # 7 days
_SECRET = os.getenv("SESSION_SECRET") or secrets.token_urlsafe(32)
if not os.getenv("SESSION_SECRET"):
    print("[auth] SESSION_SECRET not set; using a random one (sessions reset on restart).")


def _sign(payload: str) -> str:
    return hmac.new(_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()


def make_session(user_id: int) -> str:
    payload = f"{user_id}:{int(time.time()) + SESSION_TTL}"
    token = base64.urlsafe_b64encode(payload.encode()).decode()
    return f"{token}.{_sign(payload)}"


def read_session(token: str | None) -> int | None:
    if not token or "." not in token:
        return None
    token_part, sig = token.rsplit(".", 1)
    try:
        payload = base64.urlsafe_b64decode(token_part.encode()).decode()
        user_id, expires = (int(x) for x in payload.split(":"))
    except (ValueError, UnicodeDecodeError):
        return None
    if not hmac.compare_digest(_sign(payload), sig) or expires < time.time():
        return None
    return user_id


def _set_cookie(response: Response, user_id: int) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        make_session(user_id),
        max_age=SESSION_TTL,
        httponly=True,  # page JavaScript (and injected scripts) can't read it
        samesite="lax",
        secure=os.getenv("COOKIE_SECURE") == "1",  # set to 1 when served over HTTPS
        path="/",
    )


# --- Brute-force throttle -----------------------------------------------------

MAX_FAILURES = 5
WINDOW_SECONDS = 15 * 60
_failures: dict[str, deque[float]] = defaultdict(deque)


def _throttle_key(request: Request, email: str) -> str:
    return f"{request.client.host if request.client else '?'}|{email}"


def _recent_failures(key: str) -> deque[float]:
    q = _failures[key]
    while q and q[0] < time.time() - WINDOW_SECONDS:
        q.popleft()
    return q


# --- Helpers -----------------------------------------------------------------

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Signup password policy (login accepts any existing password, e.g. the seeded test user).
# Mirrored in frontend/src/pages/CreateAccount.tsx for live feedback; the server is the authority.
PASSWORD_MIN, PASSWORD_MAX = 8, 256


def password_problems(password: str) -> list[str]:
    problems = []
    if len(password) < PASSWORD_MIN:
        problems.append(f"be at least {PASSWORD_MIN} characters")
    if len(password) > PASSWORD_MAX:
        problems.append(f"be at most {PASSWORD_MAX} characters")
    if not re.search(r"\d", password):
        problems.append("include at least 1 number")
    if not re.search(r"[^A-Za-z0-9\s]", password):
        problems.append("include at least 1 symbol (like ! @ # $ %)")
    return problems


def public_user(row: sqlite3.Row) -> dict:
    """What the frontend (and later the agent) may see. Never includes password_hash."""
    first = row["first_name"] or (row["name"] or "").split(" ")[0]
    last = row["last_name"] or " ".join((row["name"] or "").split(" ")[1:])
    return {"id": row["id"], "first_name": first, "last_name": last, "name": row["name"], "email": row["email"]}


def get_user(user_id: int) -> dict | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT id, name, first_name, last_name, email FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    return public_user(row) if row else None


def current_user(token: str | None) -> dict | None:
    user_id = read_session(token)
    return get_user(user_id) if user_id else None


# --- Routes ------------------------------------------------------------------

router = APIRouter(prefix="/api/auth", tags=["auth"])


class SignupIn(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    confirm_password: str


class LoginIn(BaseModel):
    email: str
    password: str


@router.post("/signup", status_code=201)
def signup(body: SignupIn, response: Response) -> dict:
    first, last = body.first_name.strip(), body.last_name.strip()
    email = body.email.strip().lower()
    if not first or not last:
        raise HTTPException(422, "First and last name are required.")
    if not EMAIL_RE.match(email):
        raise HTTPException(422, "Please enter a valid email address.")
    problems = password_problems(body.password)
    if problems:
        raise HTTPException(422, "Password must " + ", ".join(problems) + ".")
    if body.password != body.confirm_password:
        raise HTTPException(422, "Passwords do not match.")

    with connect(readonly=False) as conn:
        try:
            cur = conn.execute(
                "INSERT INTO users (name, first_name, last_name, email, password_hash) VALUES (?, ?, ?, ?, ?)",
                (f"{first} {last}", first, last, email, hash_password(body.password)),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(409, "An account with that email already exists. Try logging in.")
        user_id = cur.lastrowid

    _set_cookie(response, user_id)
    return {"user": get_user(user_id)}


@router.post("/login")
def login(body: LoginIn, request: Request, response: Response) -> dict:
    email = body.email.strip().lower()
    key = _throttle_key(request, email)
    if len(_recent_failures(key)) >= MAX_FAILURES:
        raise HTTPException(429, "Too many failed attempts. Please wait 15 minutes and try again.")

    with connect() as conn:
        row = conn.execute(
            "SELECT id, name, first_name, last_name, email, password_hash FROM users WHERE lower(email) = ?",
            (email,),
        ).fetchone()

    ok = verify_password(body.password, row["password_hash"] if row else _DUMMY_HASH) and row is not None
    if not ok:
        _failures[key].append(time.time())
        # Same message whether the email or the password was wrong.
        raise HTTPException(401, "Incorrect email or password.")

    _failures.pop(key, None)
    _set_cookie(response, row["id"])
    return {"user": public_user(row)}


@router.post("/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"ok": True}


@router.get("/me")
def me(cc_session: str | None = Cookie(default=None)) -> dict:
    return {"user": current_user(cc_session)}
