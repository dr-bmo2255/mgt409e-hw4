# Campus Customs: AI shopping assistant & storefront (HW 4)

**Yale SOM · MGT 409E — AI Foundations for Managers · Dr_BMo**

A working customer website for **Campus Customs** (Yale apparel, 57 Broadway, New Haven):
- a **React + Vite + TypeScript** storefront
- a **FastAPI** backend
- a **PydanticAI** shopping agent that answers price and stock questions **only from `campus_customs.db`**

Shoppers can browse, create accounts, chat (as the store or as **Handsome Dan**), see matching products appear on the page, design their own Handsome Dan merchandise, and get a site that adapts to who they are.

> **Notice:** this is not a real retail site. It is not affiliated with Campus Customs. It was created by Dr_BMo for Yale School of Management's class MGT 409E — AI Foundations for Managers.

---

## 👉 Graders: start here

| | What | Open it |
|---|---|---|
| 🌐 | **Live demo site**: the full store, chat and Design with Dan, no setup needed. Real Dan images through **Nov 2, 2026** (then free placeholders); chat open through **Nov 18, 2026**. The first visit may take ~30 s to wake up. | **[https://campus-customs-demo.onrender.com](https://campus-customs-demo.onrender.com)** |
| 🏛️ | **Executive Briefing**: one-page summary; click any section for full detail | **[Live page](https://dr-bmo2255.github.io/mgt409e-hw4/hw4/output/executive_briefing.html)** · [`output/executive_briefing.html`](output/executive_briefing.html) |
| ✅ | **App Check**: screenshots proving honest inventory, search cards and usability | **[Live page](https://dr-bmo2255.github.io/mgt409e-hw4/hw4/output/app_check.html)** · [`output/app_check.html`](output/app_check.html) |
| 🐶 | **Ask Dan Image Studio**: the supervised tool that made all of Dan's art. **Please try it** (free mock mode; see below) | [`ask-dan-image-studio/`](ask-dan-image-studio/) |
| 🧰 | **Harness**: how the system works (models, tools, specs, safety, how to run) | [`output/harness.md`](output/harness.md) |
| 📝 | **Prompt log**: every prompt, by problem, with the reason for each follow-up | [`AI_prompts.md`](AI_prompts.md) |
| 🎨 | Design write-up · usability write-up · agent audit trail | [`design.md`](output/design.md) · [`usability.md`](output/usability.md) · [`audit_trail.json`](output/audit_trail.json) |

The HTML pages also open locally: double-click `output/executive_briefing.html` or `output/app_check.html` after cloning.

---

## The core agent (4 files in `backend/`)

| File | Role |
|---|---|
| [`backend/prompts/prompt.md`](backend/prompts/prompt.md) | The agent's instructions: brand voice, which tool to call, accuracy rules, the page contract, safety. The **project rules** follow a marker and are not sent to the model. |
| [`backend/agent.py`](backend/agent.py) | Builds the PydanticAI agent (Portkey → `gpt-5.6-luna`, fallback `gpt-5.6-terra`), adds the per-request instructions (voice, customer, page, visitor), runs the loop with **usage limits**, and writes the **audit trail**. |
| [`backend/tools.py`](backend/tools.py) | 8 **read-only** tools: `search_products`, `list_categories`, `get_product_info`, `get_price`, `check_stock`, `my_account`, `get_current_page`, `custom_gear_info`. Every number comes from the database. |
| [`backend/models.py`](backend/models.py) | The contracts. `AgentReply` (the structured output: reply + `product_ids` + page/design fields), `ShopDeps`, and typed tool results such as `StockReport` (status decided by code). Fields and reasons: [harness Part I.5](output/harness.md#i5-data-models-backendmodelspy-and-why-these-fields). |

`backend/main.py` exposes `POST /api/chat`: it builds trusted context, runs the agent, and turns `product_ids` into product cards from the database.

---

## Enhancements beyond the base assignment

Significant work went into these (each is documented in `output/design.md`, `output/harness.md` Part II, and `AI_prompts.md`):

1. **★ Two voices, one memory.** Chat as the store or as **Handsome Dan** (preppy, sports-mad, rival-teasing). Switching keeps context, Dan rotates 14 catchphrases, and he greets, errs and refuses in character.
2. **Customer accounts and memory.**
   - PBKDF2 passwords, a strong-password policy, signed HttpOnly sessions and a login throttle.
   - Saved chat history; the agent knows the shopper and the product on screen ("do you have *this* in pink?").
3. **Search that updates the page.** Up to 12 product cards with the real total, introduced by a Handsome Dan image for the category.
4. **Ask Dan Image Studio** (`ask-dan-image-studio/`).
   - A supervised image-generation app: pilot → approvals → capped batches → review / revise → exact-shield compositing → export, with 31 tests.
   - It made **54 category images** covering all 102 products, plus one-offs.
5. **Storefront design built around Dan.** Hero stage, category tiles, "Shop with Dan" rails, a seasonal feature, hover "Dan's take", stock meters and motion.
6. **Custom Dan Gear** (`/custom`). A CustomInk-style design lab:
   - customers describe a Dan, the AI art director drafts it, and they put it on **7 products** with live pricing, quantity breaks and a bag
   - limits: signed-in only, **3 per day**, **$3/day site cap**, moderation that fails closed, content guardrails, refusals in Dan's voice
   - designs are saved for 90 days
7. **137 product colorways.** Every listed color has its own rendered photo; colors that aren't in stock are sold as custom orders ready in 2–3 weeks.
8. **A personal welcome.** Dan barks for attention, then asks *"Are you a Current Student, Alumnus, Family, Friend or Rival?"*
   - **Alumni** see the whole store restyled for their decade (1920s Art Deco … 2010s flat), with a Dan dressed for the era.
   - **Rivals** get "Yale overload" with that rival's Dan image.
   - **Students and families** get their college or family Dan and products.
9. **Agent navigation.** "Take me to Design with Dan" moves the shopper there, limited to the site's real pages.
10. **Safety and accountability.**
    - an append-only **audit trail** of every agent run
    - project rules (model via `OPENAI_MODEL`, secrets only from `.env`, slim dependencies)
    - least-privilege read-only tools
    - quality fixes (a five-legged Dan, ten look-alike college images)
11. **Executive Briefing:** an old-bank-styled summary for managers, with detail pages.

AI image spend for the whole project was **≈ $15.70**. Every paid batch was approved, capped, and logged.

---

## Repository layout

```
hw4/
├── AI_prompts.md            # prompt log (every problem, follow-ups + reasons)
├── requirements.txt         # backend Python deps (pydantic-ai-slim[openai], FastAPI, …)
├── .env.example             # variable names only; copy to .env
├── .gitignore
├── README.md
├── frontend/                # Vite + React + TypeScript storefront
├── backend/
│   ├── main.py              # FastAPI app: uvicorn main:app --reload --port 8000
│   ├── agent.py             # ┐
│   ├── models.py            # │ the core agent
│   ├── tools.py             # │
│   ├── prompts/prompt.md    # ┘ (+ voice_dan.md for Dan's voice)
│   ├── config.py, audit.py  # model/limit settings · append-only audit trail
│   ├── auth.py, db.py, catalog.py, context.py   # accounts, SQLite, catalog helpers, trusted context
│   └── custom.py, design_agent.py, dan_voice.py # Custom Dan Gear, design agent, Dan's phrasebook
├── ask-dan-image-studio/    # the Dan image studio (backend, built dashboard, manifest, references, tests)
├── scripts/                 # image pipelines: import, mockups, colorways, decade Dans, fixes, app-check screenshots
├── data/                    # ← place the data pack here (see below); our rendered art is already committed:
│   ├── dan/                 #    all Handsome Dan images (WebP) + dan_map.json
│   ├── custom/mockups/      #    blank products for Custom Dan Gear
│   └── products/colorways/  #    137 rendered colorway photos + colorways.json
└── output/
    ├── executive_briefing.html, briefing_images/
    ├── harness.md, design.md, usability.md
    ├── app_check.html, app_check_images/
    ├── audit_trail.json
    └── decade_dans_review.jpg, college_variety_review.jpg
```

**Not in the repo, on purpose:** `.env` files, `data/campus_customs.db`, the original product photos (`data/products/*.jpg`), customer-made designs, the studio's run state, the course input zips, and full-size PNG sources.

---

## Live demo (Render)
**https://campus-customs-demo.onrender.com** runs this exact code with the assignment's data pack. It's deployed from a private copy of this repo (`scripts/sync_deploy.sh`), so the database and photos are never in the public repo.
- **Public-demo limits:** the chat and design drafting allow 20 messages per visitor per hour and 300 per day site-wide.
- **Real Dan images through November 2, 2026:** Design with Dan makes **real** images (with OpenAI moderation first), still limited to 3 per customer per day and a $3/day site cap. After that date it switches to free placeholder images automatically.
- **Time window:** the chat, drafting and image creation close by themselves after **November 18, 2026**. Browsing keeps working.
- **Free hosting:** the site sleeps when idle (the first visit takes ~30 s), and accounts and designs made there reset when it restarts.

## Run it

### 1. Place the data pack: use the ORIGINAL files from the assignment
Copy the assignment's data pack, **unchanged**, into `hw4/data/`:
```
data/
├── campus_customs.db        # the store database, exactly as provided
└── products/                # the product photos (*.jpg), exactly as provided
                             # (data/products/colorways/ is already here from the repo — keep it)
```
**Use the original database and photos from the assignment.** Don't substitute another copy, and don't edit them by hand. On first start the backend upgrades them to exactly the version this project was built and tested with. The upgrade is automatic, one-time, and logged:

| What we changed during the project | What the backend does on first start | Log line |
|---|---|---|
| **Problem 2:** 3 catalogue rows ship as stubs with no colors and a "Vision blocked" description (Benjamin Franklin T-Shirt, Berkeley Sweater Fleece Jacket, Timothy Dwight College Crewneck). The owner reviewed the photos and supplied the real details. | Fills in those 3 rows from [`backend/data_fixes.json`](backend/data_fixes.json), only while they're still the original stubs | `[db] Applied Problem 2 catalogue fixes to 3 product(s)` |
| **Problems 4–10:** new tables (customer designs, bag) and a `voice` column for saved chats | Adds them. It never drops or rewrites existing data. | (silent) |
| **Problem 3:** 74 product photos have black backgrounds (flattened transparent PNGs); we made them white for a consistent storefront | Keeps the originals in `data/products_original/` and writes white-background versions with the same script ([`scripts/whiten_image_backgrounds.py`](scripts/whiten_image_backgrounds.py)), about 15 s | `[setup] Done: 74 of 102 photos updated` |

**Why the database isn't uploaded:**
- The assignment asks us not to commit `campus_customs.db` or the product images.
- Our working copy also holds **test accounts** (with password hashes) and **test chat histories** that shouldn't be published.

Instead, the only content changes we made are applied in code to the original file. We verified this from a fresh clone using the untouched data pack: after the first start, the catalogue and inventory match our working database row for row, and all 102 photos match ours byte for byte.

### 2. Add your keys
```bash
cp .env.example .env        # then set PORTKEY_API_KEY and SESSION_SECRET (any long random string)
```
The chat uses **Portkey** (`PORTKEY_API_KEY`). Creating *real* AI images also needs `OPENAI_API_KEY` in `ask-dan-image-studio/.env`. To try Custom Dan Gear for free, set `CUSTOM_IMAGE_PROVIDER=mock` in `.env`.

### 3. Back end (Python 3.12)
```bash
cd backend
uv sync                                   # or: python3.12 -m venv .venv && .venv/bin/pip install -r ../requirements.txt
.venv/bin/uvicorn main:app --reload --port 8000
```
Check: http://localhost:8000/api/health → `{"status":"ok","products":102,"agent_model":"gpt-5.6-luna"}`

### 4. Front end (Node 20+)
```bash
cd frontend
npm install
npm run dev                               # → http://localhost:5173 (proxies /api and /media to :8000)
```

### 5. Things to try
- Open the chat ("Chat with Dan"). Wait ~12 s on the home page and Dan barks first.
- Answer the welcome question as an **Alumnus → 1920s**, or as a **Rival → Princeton**.
- Ask: *"Is the Yale Bowl T-Shirt in stock in XL?"* or *"What hoodies do you have?"*
- Say *"Take me to Design with Dan"*, or pick a color on a product page.

---

## 🐶 Try the Ask Dan Image Studio

The studio is how every Handsome Dan image on the site was made: human-supervised, with approvals and hard spending caps.
It starts in **Mock mode**, which is **free**: it makes labeled placeholder images, so you can walk through the whole
workflow (inventory → generate → review → revise → approve → export) without an API key or any cost.

```bash
cd ask-dan-image-studio/backend
uv sync
.venv/bin/uvicorn app:app --port 8765     # → http://localhost:8765  (dashboard is pre-built)
```
**Worth looking at:**
- **Overview:** the 54-category asset plan.
- **Generate / Review:** the version strip and side-by-side compare.
- **🐶 Ask Dan chat:** draft a one-off Dan (needs `PORTKEY_API_KEY`).
- **Place exact supplied shield:** pixel-exact official shields on garments.
- **Batch control:** the pilot → batch authorization guards.

Tests: `uv run pytest` (31 tests). More detail: [`ask-dan-image-studio/README.md`](ask-dan-image-studio/README.md).

---

## Models, limits and rules (short version)
- **Text:** `gpt-5.6-luna` via Portkey (env `OPENAI_MODEL`), set in one place, `backend/config.py`.
- **Images:** `gpt-image-2.5-sunburst` (direct OpenAI).
- **Agent loop:** ≤ 8 model requests and ≤ 12 tool calls per message.
- **Results:** ≤ 12 product cards; messages ≤ 2,000 characters; the last 30 turns of history.
- **Rules:** recorded in [`backend/prompts/prompt.md`](backend/prompts/prompt.md) (project rules section). Every agent run is appended to [`output/audit_trail.json`](output/audit_trail.json).

---

*Not a real retail site · not affiliated with Campus Customs · created by Dr_BMo for Yale SOM MGT 409E — AI Foundations for Managers.*
