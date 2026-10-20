"""Comprehensive browser test of the local Campus Customs site (Chrome via Playwright).

Pages, images, console errors, disclaimer, layout (desktop + phone), carousel, bag, chat (onboarding, rival
banner, decade theme, start over, nudge, size cap, scroll alignment) and a few real chat replies.
Needs the backend (8000) and frontend (5173) running and Google Chrome installed. A few real chat replies are used
(a fraction of a cent through Portkey). Creates one throwaway local account (…@example.test).
Run from hw4/:  uv run --with playwright --with httpx python scripts/site_test.py
"""
import json, re, secrets, sys, time
from pathlib import Path
import httpx
from playwright.sync_api import sync_playwright

SITE = "http://localhost:5173"
OUT = Path(__file__).resolve().parent.parent / "output" / "site_test" 
OUT.mkdir(parents=True, exist_ok=True)
results = []


def check(group, name, ok, detail=""):
    results.append({"group": group, "name": name, "ok": bool(ok), "detail": str(detail)[:300]})
    print(("PASS " if ok else "FAIL ") + f"[{group}] {name}" + (f"  ({detail})" if detail and not ok else ""), flush=True)


FRESH = "try{localStorage.clear();sessionStorage.clear()}catch(e){}"
products = httpx.get("http://localhost:8000/api/products").json()
PID = "champion-full-zip-hood"


def page_health(page, path, group="pages"):
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(SITE + path, wait_until="networkidle")
    page.wait_for_timeout(600)
    info = page.evaluate("""() => ({
        broken: [...document.images].filter(i => i.complete && i.naturalWidth === 0 && i.getAttribute('src')).map(i => i.getAttribute('src')),
        hscroll: document.documentElement.scrollWidth > window.innerWidth + 1,
        disclaimer: /Not a real retail site/i.test(document.querySelector('.footer-disclaimer')?.textContent || ''),
        h1: document.querySelector('main h1, main h2')?.textContent?.trim() || '',
    })""")
    check(group, f"{path}: no broken images", not info["broken"], info["broken"][:3])
    check(group, f"{path}: no horizontal scroll", not info["hscroll"])
    check(group, f"{path}: disclaimer in footer", info["disclaimer"])
    check(group, f"{path}: no JS errors", not errors, errors[:2])
    return info


def open_chat(page, voice=None):
    if not page.locator(".chat-panel").count():
        page.click(".chat-fab")
        page.wait_for_timeout(400)
    if voice:
        page.locator(".voice-toggle button", has_text="Chat with Dan" if voice == "dan" else "Campus Customs").click()
        page.wait_for_timeout(500)


def ask(page, text, timeout=120_000):
    reply = ".chat-list .bubble-assistant:not(.typing)"
    n = page.locator(reply).count()
    page.fill(".chat-form input", text)
    page.click(".chat-form button[type=submit]")
    page.wait_for_function(f"document.querySelectorAll('{reply}').length > {n} && !document.querySelector('.chat-list .typing')", timeout=timeout)
    page.wait_for_timeout(1500)
    return page.locator(reply).last.inner_text()


def newest_offset(page):
    return page.evaluate("""() => { const l=document.querySelector('.chat-list'); const b=[...l.querySelectorAll('.bubble:not(.typing)')].pop();
        return Math.round(b.getBoundingClientRect().top - l.getBoundingClientRect().top) }""")


def newest_aligned(page):
    """Top of the newest bubble at the top (8 px), or the list is already scrolled to the bottom (a short reply can't
    go higher)."""
    return page.evaluate("""() => { const l=document.querySelector('.chat-list'); const b=[...l.querySelectorAll('.bubble:not(.typing)')].pop();
        const off=b.getBoundingClientRect().top - l.getBoundingClientRect().top; const atBottom = l.scrollTop >= l.scrollHeight - l.clientHeight - 2;
        return {ok: Math.abs(off-8) <= 3 || (atBottom && off > 0), off: Math.round(off), atBottom} }""")


with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    ctx = browser.new_context(viewport={"width": 1360, "height": 860})
    ctx.add_init_script("if(!sessionStorage.getItem('t_init')){" + FRESH + ";sessionStorage.setItem('t_init','1')}")
    page = ctx.new_page()

    # ---------- 1. Every page ----------
    for path in ["/", "/products", "/products?category=Hoodies", "/products?q=yale", f"/products/{PID}", "/about", "/login",
                 "/create-account", "/custom", "/bag", "/chat-results", "/this-page-does-not-exist"]:
        page_health(page, path)
    page.goto(SITE + "/account"); page.wait_for_timeout(600)
    check("pages", "/account as guest redirects to /login", page.url.endswith("/login"), page.url)
    page.goto(SITE + "/this-page-does-not-exist"); page.wait_for_timeout(400)
    check("pages", "unknown URL shows a not-found page", "find" in page.inner_text("main").lower() or "not found" in page.inner_text("main").lower(), page.inner_text("main")[:80])

    # all 102 product pages render their name + price
    bad = []
    for prod in products:
        page.goto(f"{SITE}/products/{prod['product_id']}")
        try:
            page.wait_for_selector(".detail h1", timeout=8000)
        except Exception:
            bad.append(prod["product_id"]); continue
        if "$" not in page.inner_text(".detail"):
            bad.append(prod["product_id"])
    check("pages", "all 102 product pages render (name + price)", not bad, bad[:5])

    # ---------- 2. Navigation ----------
    page.goto(SITE + "/")
    for label, path in [("Products", "/products"), ("Design with Dan", "/custom"), ("About Us", "/about"), ("Bag", "/bag"), ("Home", "/")]:
        page.locator(".nav-links a", has_text=label).first.click(); page.wait_for_timeout(500)
        check("nav", f"nav '{label}' → {path}", page.url.rstrip("/").endswith(path.rstrip("/")) or (path == "/" and page.url.rstrip("/") == SITE), page.url)

    # ---------- 3. Home carousel ----------
    page.goto(SITE + "/"); page.wait_for_timeout(1500)
    srcs = page.eval_on_selector_all(".dan-stage-img", "els => els.map(e => e.getAttribute('src'))")
    check("home", "carousel has 12 photos", len(srcs) == 12, len(srcs))
    check("home", "carousel has no rival/football/ice-hockey photos", not any(re.search(r"rival|football|ice_hockey", s) for s in srcs), srcs)
    check("home", "carousel has 12 dots", page.locator(".dan-stage-dots button").count() == 12)
    caps = []
    for i in range(12):
        page.locator(".dan-stage-dots button").nth(i).click(); page.wait_for_timeout(120)
        caps.append(page.locator(".dan-stage-caption").count())
    check("home", "every slide has a 'Shop it' caption", all(caps), caps)
    page.reload(); page.wait_for_timeout(1500)
    srcs2 = page.eval_on_selector_all(".dan-stage-img", "els => els.map(e => e.getAttribute('src'))")
    check("home", "order changes between visits (sorted sets equal)", sorted(srcs) == sorted(srcs2) and srcs != srcs2)

    # category tile → filtered products
    page.locator(".tile, .category-tile, a[href*='category=']").first.click(); page.wait_for_timeout(800)
    check("home", "category tile opens a filtered product list", "category=" in page.url, page.url)

    # ---------- 4. Bag (guest) ----------
    page.goto(f"{SITE}/products/{PID}"); page.wait_for_selector(".detail h1")
    page.locator(".detail button", has_text=re.compile(r"^M$")).first.click()
    page.locator(".btn-primary.btn-block").click(); page.wait_for_timeout(200)
    page.locator(".btn-primary.btn-block").click(); page.wait_for_timeout(200)
    check("bag", "guest add → confirmation shown", page.locator(".added-note").count() == 1)
    check("bag", "badge shows 2 after two adds", page.locator(".nav-links .bag-count").inner_text() == "2")
    page.locator(".detail button, .detail a", has_text=re.compile("navy", re.I)).first.click(); page.wait_for_timeout(400)
    page.locator(".detail button", has_text=re.compile(r"^L$")).first.click()
    label = page.locator(".btn-primary.btn-block").inner_text()
    check("bag", "uncommon color button says custom order", "custom order" in label.lower(), label)
    page.locator(".btn-primary.btn-block").click(); page.wait_for_timeout(200)
    check("bag", "badge shows 3", page.locator(".nav-links .bag-count").inner_text() == "3")
    page.goto(SITE + "/bag"); page.wait_for_timeout(800)
    lines = page.locator(".bag-item").count()
    sub = page.locator(".bag-row b").inner_text()
    check("bag", "bag page lists 2 lines, subtotal $264.00", lines == 2 and sub == "$264.00", f"{lines} lines, {sub}")
    check("bag", "custom-order line marked 2–3 weeks", "2–3 weeks" in page.inner_text(".bag-list"))
    check("bag", "checkout disabled", page.locator(".bag-summary button[disabled]").count() == 1)
    page.locator(".bag-item").first.locator("[aria-label=More]").click(); page.wait_for_timeout(150)
    check("bag", "+ raises badge to 4", page.locator(".nav-links .bag-count").inner_text() == "4")
    page.reload(); page.wait_for_timeout(800)
    check("bag", "bag survives reload", page.locator(".nav-links .bag-count").inner_text() == "4")
    for _ in range(2):
        page.locator(".bag-item .link-btn", has_text="Remove").first.click(); page.wait_for_timeout(150)
    check("bag", "removing everything empties bag, badge gone", page.locator(".nav-links .bag-count").count() == 0 and "empty" in page.inner_text("main").lower())
    page.screenshot(path=str(OUT / "bag_empty.png"))

    # ---------- 5. Chat (no AI) ----------
    page.goto(SITE + "/about"); page.wait_for_timeout(500)
    check("chat", "chat stays collapsed on load", page.locator(".chat-panel").count() == 0)
    page.wait_for_timeout(12500)
    check("chat", "bark bubble appears after ~12 s", page.locator(".bark, .bark-bubble, [class*=bark]").count() > 0)
    open_chat(page, "dan")
    check("chat", "welcome question shown in Dan voice", "Current Student, Alumnus" in page.inner_text(".chat-list"))
    size = page.evaluate("() => { const r=document.querySelector('.chat-panel').getBoundingClientRect(); return r.width*r.height/(innerWidth*innerHeight) }")
    check("chat", "mini chat ≤ 1/4 of window", size <= 0.2505, round(size, 3))
    page.click(".chat-size"); page.wait_for_timeout(500)
    size = page.evaluate("() => { const r=document.querySelector('.chat-panel').getBoundingClientRect(); return r.width*r.height/(innerWidth*innerHeight) }")
    check("chat", "expanded chat ≤ 1/4 of window", size <= 0.2505, round(size, 3))
    page.click(".chat-size"); page.wait_for_timeout(400)

    # rival via welcome question
    page.locator(".chat-list button", has_text="Rival").click(); page.wait_for_timeout(600)
    page.locator(".chat-list button", has_text="Princeton").click(); page.wait_for_timeout(1500)
    check("rival", "no rival image inside the chat", page.locator(".chat-panel img[src*=rival_]").count() == 0)
    check("rival", "rival banner image on page", page.locator(".rival-banner img[src*=rival_princeton]").count() == 1)
    w = page.evaluate("() => document.querySelector('.rival-banner img').offsetWidth")
    check("rival", "rival image is 330 px (50% larger)", w == 330, w)
    check("rival", "Dan nudges toward the page", bool(re.search(r"top of the page|up top", page.inner_text(".chat-list"))))
    check("rival", "Yale overload on (html[data-rival])", page.evaluate("() => document.documentElement.dataset.rival") == "princeton")
    page.screenshot(path=str(OUT / "rival_banner.png"))
    for path in ["/products", f"/products/{PID}", "/custom", "/bag", "/"]:
        page.goto(SITE + path); page.wait_for_timeout(500)
        check("rival", f"banner present on {path}", page.locator(".rival-banner").count() == 1)
    page.locator(".rival-banner button", has_text="Back to the regular site").click(); page.wait_for_timeout(300)
    check("rival", "'Back to the regular site' restores the normal look", page.locator(".rival-banner").count() == 0 and not page.evaluate("() => document.documentElement.dataset.rival"))

    # start over → alumni decade
    open_chat(page, "dan")
    page.fill(".chat-form input", "start over"); page.click(".chat-form button[type=submit]"); page.wait_for_timeout(800)
    check("chat", "'start over' brings the welcome question back", page.locator(".chat-list button", has_text="Alumnus").count() > 0)
    page.locator(".chat-list button", has_text="Alumnus").last.click(); page.wait_for_timeout(500)
    page.locator(".chat-list button", has_text="1920s").last.click(); page.wait_for_timeout(2600)
    check("decade", "1920s theme applied", page.evaluate("() => document.documentElement.dataset.era") == "1920s")
    check("decade", "chat closes after decade pick", page.locator(".chat-panel").count() == 0)
    check("decade", "decade banner with 1920s Dan", page.locator(".era-banner img[src*=dan_1920s]").count() == 1)
    page.screenshot(path=str(OUT / "decade_1920s.png"))
    page.locator(".era-banner button", has_text="Not you").click(); page.wait_for_timeout(500)
    check("decade", "'Not you? Change' removes the theme", not page.evaluate("() => document.documentElement.dataset.era"))

    # nudge toward Dan (brand voice, 15 s)
    page.goto(SITE + "/about"); page.wait_for_timeout(400)
    open_chat(page, "brand")
    page.wait_for_timeout(13500)
    check("nudge", "no nudge before 15 s", page.locator(".dan-nudge").count() == 0)
    page.wait_for_timeout(2500)
    check("nudge", "nudge appears after 15 s", page.locator(".dan-nudge").count() == 1 and "nudge" in page.locator(".voice-toggle button", has_text="Chat with Dan").get_attribute("class"))
    page.locator(".dan-nudge .link-btn").click(); page.wait_for_timeout(300)
    check("nudge", "nudge link switches to Dan and clears", page.locator(".dan-nudge").count() == 0 and "active" in page.locator(".voice-toggle button", has_text="Chat with Dan").get_attribute("class"))

    # ---------- 6. Chat with the AI (a few real replies) ----------
    ai = ctx.new_page()
    ai.goto(SITE + "/about"); ai.wait_for_timeout(500)
    open_chat(ai, "dan")
    if ai.locator(".chat-list button", has_text="Friend").count():
        ai.locator(".chat-list button", has_text="Friend").click(); ai.wait_for_timeout(1200)
    r1 = ask(ai, "show me hoodies")
    n_links = ai.locator(".chat-list a.chat-product").count()
    check("ai", "Dan answers 'show me hoodies' with product links", n_links > 0, r1[:120])
    check("ai", "product cards also appear on the page", ai.locator("[data-testid=chat-results] .card, [data-testid=chat-results] a").count() > 0)
    al = newest_aligned(ai)
    check("ai", "newest bubble top aligned with chat top (or chat at bottom)", al["ok"], al)
    ai.locator(".chat-list a.chat-product").first.click(); ai.wait_for_timeout(1200)
    check("ai", "chat product link opens product page and minimizes chat", "/products/" in ai.url and ai.locator(".chat-panel").count() == 0, ai.url)
    open_chat(ai)
    r2 = ask(ai, "Is the Champion Full Zip Hood available in XL, and how much is it?")
    inv = httpx.get(f"http://localhost:8000/api/products/{PID}").json()
    xl = next(s["quantity"] for s in inv["inventory"] if s["size"] == "XL")
    check("ai", "stock answer has the right price ($88)", "88" in r2, r2[:200])
    check("ai", "stock answer consistent with XL stock", ("sold out" in r2.lower()) == (xl == 0), f"XL={xl}: {r2[:160]}")
    r3 = ask(ai, "take me to the design with dan page")
    ai.wait_for_timeout(1000)
    check("ai", "'take me to design with dan' navigates to /custom", ai.url.endswith("/custom"), ai.url)
    r4 = ask(ai, "My cousin goes to Harvard")
    check("ai", "naming Harvard puts rival banner on page (not in chat)", ai.locator(".rival-banner img[src*=rival_harvard]").count() == 1 and ai.locator(".chat-panel img[src*=rival_]").count() == 0)
    check("ai", "scrolled to top so banner is visible", ai.evaluate("scrollY") < 5, ai.evaluate("scrollY"))
    ai.screenshot(path=str(OUT / "ai_harvard.png"))
    ai.locator(".voice-toggle button", has_text="Campus Customs").click(); ai.wait_for_timeout(300)
    r5 = ask(ai, "What sizes do your crewnecks come in?")
    check("ai", "store voice answers (no Dan stage directions)", "*" not in r5 and len(r5) > 20, r5[:160])

    # ---------- 7. Sign in through the UI ----------
    email = f"uitest+{secrets.token_hex(4)}@example.test"; pw = "T3st-" + secrets.token_urlsafe(10)
    su = ctx.new_page()
    su.goto(SITE + "/create-account"); su.wait_for_timeout(500)
    for sel, val in [("input[autocomplete=given-name]", "Ui"), ("input[autocomplete=family-name]", "Tester"), ("input[type=email]", email)]:
        su.locator(sel).first.fill(val)
    pws = su.locator("input[type=password]")
    pws.nth(0).fill(pw); pws.nth(1).fill(pw)
    su.locator("form.auth-card button.btn-primary").click(); su.wait_for_timeout(1500)
    check("account", "create account through the form signs you in", su.locator(".nav-links", has_text="Hi, Ui").count() == 1, su.url)
    su.goto(SITE + "/account"); su.wait_for_timeout(800)
    check("account", "account page loads when signed in", "/account" in su.url and "Ui" in su.inner_text("main"))
    su.locator(".nav-links button", has_text="Log Out").click(); su.wait_for_timeout(800)
    su.goto(SITE + "/login"); su.wait_for_timeout(400)
    su.locator("input[type=email]").fill(email); su.locator("input[type=password]").fill(pw)
    su.locator("form.auth-card button.btn-primary").click(); su.wait_for_timeout(1500)
    check("account", "log back in through the form", su.locator(".nav-links", has_text="Hi, Ui").count() == 1)

    # ---------- 8. Phone layout ----------
    m = browser.new_context(viewport={"width": 375, "height": 812}, is_mobile=True, has_touch=True)
    mp = m.new_page()
    for path in ["/", "/products", f"/products/{PID}", "/custom", "/about", "/bag", "/login"]:
        mp.goto(SITE + path, wait_until="networkidle"); mp.wait_for_timeout(500)
        hs = mp.evaluate("() => document.documentElement.scrollWidth > innerWidth + 1")
        check("phone", f"{path}: no horizontal scroll at 375 px", not hs)
    mp.goto(f"{SITE}/products/{PID}"); mp.wait_for_selector(".detail h1")
    mp.locator(".detail button", has_text=re.compile(r"^S$")).first.click()
    mp.locator(".btn-primary.btn-block").click(); mp.wait_for_timeout(300)
    check("phone", "bag badge visible next to menu button", mp.locator(".nav-bag-mobile .bag-count").is_visible())
    mp.locator(".nav-toggle").click(); mp.wait_for_timeout(300)
    check("phone", "menu opens", mp.locator(".nav-links.open").is_visible())
    mp.screenshot(path=str(OUT / "phone_menu.png"))
    browser.close()

passed = sum(r["ok"] for r in results)
(OUT / "results.json").write_text(json.dumps(results, indent=1))
print(json.dumps({"passed": passed, "total": len(results), "failed": [r for r in results if not r["ok"]]}, indent=1))
