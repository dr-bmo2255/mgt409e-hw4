#!/usr/bin/env python3
"""Problem 11 (app check): drive the running site in Chrome and save the screenshots used by output/app_check.html.

Needs the backend (port 8000) and frontend (port 5173) running, and `pip install playwright` (it drives the
installed Google Chrome, so no browser download). Each run also writes output/app_check_images/results.json with
what the chat actually said, so the captions can be checked against the database.

  python scripts/app_check_screenshots.py
"""
import json, sqlite3
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "app_check_images"
SITE = "http://localhost:5173"
VIEW = {"width": 1360, "height": 860}

# A plain visitor: no welcome-question popup, today's design, brand voice (Part E themes stay off).
INIT = """
try { localStorage.removeItem('cc_visitor'); localStorage.setItem('cc_chat_voice', 'brand');
      sessionStorage.setItem('cc_onboarding_skipped', '1'); } catch (e) {}
"""


def ask(page, text, timeout=120_000):
    """Send a chat message and wait for the assistant's reply bubble."""
    reply = ".chat-list .bubble-assistant:not(.typing)"  # the paw "typing" indicator is a bubble too
    n = page.locator(reply).count()
    page.fill(".chat-form input", text)
    page.click(".chat-form button[type=submit]")
    page.wait_for_function(f"document.querySelectorAll('{reply}').length > {n} && !document.querySelector('.chat-list .typing')",
                           timeout=timeout)
    page.wait_for_timeout(1800)  # let the Dan reveal / card animations finish
    return page.locator(reply).last.inner_text()


def open_chat(page):
    page.click(".chat-fab")
    page.wait_for_selector(".chat-panel")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(ROOT / "data" / "campus_customs.db")
    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        ctx = browser.new_context(viewport=VIEW, device_scale_factor=1.5)
        ctx.add_init_script(INIT)

        # 1. Inventory: on the Yale Bowl T-Shirt page, ask about XL and M stock and the price.
        page = ctx.new_page()
        page.goto(f"{SITE}/products/yale-bowl-t-shirt")
        page.wait_for_selector(".stock-meters")
        open_chat(page)
        reply = ask(page, "Is this shirt in stock in XL and in M? How much is it?")
        page.screenshot(path=OUT / "inventory.png")
        # The same product's stock straight from the page (chat closed): what the chat should agree with.
        page.click(".chat-close")
        page.locator(".detail-info").scroll_into_view_if_needed()
        page.wait_for_timeout(400)
        page.locator(".detail-info").screenshot(path=OUT / "inventory_page.png")
        results["inventory"] = {
            "reply": reply,
            "db": {"price": db.execute("SELECT price FROM catalogue WHERE product_id='yale-bowl-t-shirt'").fetchone()[0],
                   "stock": dict(db.execute("SELECT size, quantity FROM inventory WHERE product_id='yale-bowl-t-shirt'").fetchall())},
        }
        page.close()

        # 2. Category question -> Dan reveal + product cards on the page.
        page = ctx.new_page()
        page.goto(SITE)
        page.wait_for_selector(".hero2")
        open_chat(page)
        reply = ask(page, "What hoodies do you have?")
        page.screenshot(path=OUT / "hoodies_chat.png")
        section = page.locator("[data-testid=chat-results]")
        section.scroll_into_view_if_needed()
        page.wait_for_timeout(1500)
        page.click(".chat-close")  # close the chat so the cards are fully visible
        page.wait_for_timeout(400)
        page.locator("[data-testid=chat-results] .card").first.evaluate("el => el.scrollIntoView({block: 'start'})")
        page.mouse.wheel(0, -90)  # keep the sticky header from covering the first row
        page.wait_for_timeout(600)
        page.screenshot(path=OUT / "hoodies_grid.png")
        results["hoodies"] = {
            "reply": reply,
            "cards_on_page": section.locator(".card").count(),
            "db_hoodies": db.execute("SELECT COUNT(*) FROM catalogue WHERE garment_type LIKE '%hood%'").fetchone()[0],
        }
        page.close()

        # 3. Usability (Problem 9): the chat starts mini, grows when the conversation overflows,
        #    and shrinks back when the shopper clicks on the page.
        page = ctx.new_page()
        page.goto(SITE)
        page.wait_for_selector(".hero2")
        open_chat(page)
        page.wait_for_timeout(500)
        page.screenshot(path=OUT / "chat_mini.png")
        ask(page, "Do you have any navy crewnecks under $60?")
        page.wait_for_selector(".chat-panel.expanded", timeout=10_000)
        page.wait_for_timeout(600)
        page.screenshot(path=OUT / "chat_expanded.png")
        page.mouse.click(250, 520)  # click on the page, outside the chat
        page.wait_for_timeout(700)
        page.screenshot(path=OUT / "chat_shrunk.png")
        results["usability"] = {
            "expanded_after_reply": True,
            "still_open_after_outside_click": page.locator(".chat-panel").count() == 1,
            "expanded_after_outside_click": page.locator(".chat-panel.expanded").count() == 1,
        }
        browser.close()
    (OUT / "results.json").write_text(json.dumps(results, indent=1))
    print(json.dumps(results, indent=1))


if __name__ == "__main__":
    main()
