"""Build the agent's per-request context (ShopDeps) on the server.

- CustomerContext comes from the signed session cookie + the users table. The browser
  can't claim to be someone else, and password_hash is never selected.
- PageContext starts from what the browser reports (path, product_id, category, search),
  but every product reference is checked against the database and the product name /
  price are filled in from the DB. Free text from the browser never reaches the prompt
  except the short search string, which is labeled as shopper input.
"""

import re

import catalog
from db import connect
from models import CustomerContext, PageContext, PageContextIn

CATEGORIES = set(catalog.CATEGORY_NAMES)


def build_customer(user: dict | None) -> CustomerContext | None:
    """user is auth.current_user() output (id, first_name, last_name, email) or None for guests."""
    if not user:
        return None
    with connect() as conn:
        row = conn.execute("SELECT created_at FROM users WHERE id = ?", (user["id"],)).fetchone()
        chats = conn.execute("SELECT COUNT(*) FROM chat_messages WHERE user_id = ?", (user["id"],)).fetchone()[0]
    return CustomerContext(
        user_id=user["id"],
        first_name=user["first_name"],
        last_name=user["last_name"],
        email=user["email"],
        member_since=(row["created_at"] or "")[:10] if row else None,
        returning_customer=chats > 0,
    )


def _page_type(path: str) -> str:
    if path == "/":
        return "home"
    if re.fullmatch(r"/products/[^/]+", path):
        return "product"
    return {
        "/products": "products",
        "/about": "about",
        "/account": "account",
        "/login": "login",
        "/create-account": "signup",
        "/chat-results": "chat_results",
        "/custom": "custom",
        "/bag": "bag",
    }.get(path, "other")


def build_page(page: PageContextIn | None) -> PageContext | None:
    if page is None:
        return None
    path = page.path.split("?")[0] or "/"
    ctx = PageContext(path=path, page_type=_page_type(path))

    # Product page: trust only an id that exists in the catalog (and matches the URL).
    pid = page.product_id
    if ctx.page_type == "product":
        pid = pid or path.rsplit("/", 1)[-1]
    if pid and (p := catalog.get_product(pid)):
        ctx.product_id = p["product_id"]
        ctx.product_name = catalog.display_name(p["name"])
        ctx.product_price = p["price"]
    elif ctx.page_type == "product":
        ctx.page_type = "other"  # unknown product id: don't pretend we know what "this" is

    if page.category in CATEGORIES:
        ctx.category = page.category
    if page.search:
        ctx.search = re.sub(r"[^\w\s/&'-]", "", page.search)[:100].strip() or None
    return ctx
