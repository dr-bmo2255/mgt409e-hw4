# Campus Customs: Usability Improvements

> **A note on timing.** The problem set asks for this file to be written *before or as* we build. I got excited and built these improvements early, while working on Problems 3–7, so this file **reconstructs them retrospectively**. Each section uses the reason I gave when I asked for the feature (recorded at the time in `AI_prompts.md`), says where it lives in the code, and links to the verification at the bottom.

| # | Improvement | Type | Built during | Helps |
|---|---|---|---|---|
| 1 | Expandable chat window + compact chat text | **Front-end** | Problem 7 (follow-up) | Shopper |
| 2 | White product image backgrounds | **Front-end** | Problem 3 (follow-up) | Shopper + business |
| 3 | "Chat with Dan" voice (Handsome Dan persona with shared memory) | **Agent / backend** | Problem 5 (bonus) | Shopper + business |
| 4 | Stronger password policy (number + symbol, enforced on the server) | **Agent / backend** | Problem 4 (follow-up) | Shopper + business |

---

## Front-end improvement 1: Expandable chat window with compact text

**What I asked for:** once the chat shows product thumbnails, the shopper has to do a lot of scrolling. I asked for (1) a smaller but still easy-to-read font, (2) the "mini" chat window to grow automatically to at least half the page when it fills up, while staying an overlay, (3) the window to shrink back to mini size when the shopper clicks on the main page, and (4) a collapse button.

**Why (my reason at the time):** *"I am building additional features to make this easier to use and be more polished."*

**How it helps**
- **Shopper:** a browse question like "what hoodies do you have?" returns a reply plus product thumbnails, which used to overflow a 380×560 box. Now the window grows to at least half the screen, so the whole answer is readable without scrolling inside a small box. Clicking back on the page (or a product card the chat placed there) returns it to mini size, so the chat never blocks shopping. The ⤢ / ⤡ button gives manual control.
- **Business:** less friction in the chat means more questions get asked and answered, so more shoppers find a product. The compact text also makes the store feel polished rather than cramped.

**How it works**
- `frontend/src/components/ChatWidget.tsx`: after each reply, a layout effect checks whether the message list overflows. If it does, `expanded = true`. A `pointerdown` listener outside the chat (or Esc) sets it back to mini. The header has a ⤢ / ⤡ toggle next to ×. **New chat** and re-opening return to mini.
- `frontend/src/index.css`:
  - Mini: 380 × 560 px.
  - Expanded: `width: max(50vw, 560px)`, `height: max(50vh, 100vh − 120px)`, still `position: fixed` in the corner, with product thumbnails in a grid.
  - Bubbles: 0.84rem (≈13.4px), 1.45 line height. Thumbnails: 38px.
  - Phones (≤ 600px): expanded fills the screen minus 12px, with no horizontal scroll.
- The chat also shows only 3 thumbnails per reply, with "+N more shown on the page". The full set appears as product cards on the page (Problem 7).

---

## Front-end improvement 2: White product image backgrounds

**What I asked for:** 74 of the 102 product photos had black backgrounds (transparent PNGs saved as JPG, plus one with a black frame), while the rest were white. I asked for them all to have white backgrounds to match.

**Why (my reason at the time):** *"I am keeping the images consistent with each other to have a professional appearing website."* And in Problem 9: *"I wanted the store items to appear seamlessly on the webpage rather than looking like a slapped together photo album."*

**How it helps**
- **Shopper:** product grids, chat results, and product pages look uniform, so the eye goes to the garment instead of a black box. Dark navy garments are no longer lost against a black background.
- **Business:** a consistent, clean catalog looks trustworthy and professional, closer to a real retailer than a "slapped together photo album". That supports conversion and the Campus Customs brand.

**How it works**
- `scripts/whiten_image_backgrounds.py` flood-fills near-black pixels (max RGB < 14) **connected to the image border** with white, so black logos and dark details inside the garment are untouched. It also fills tall, narrow, pure-black gaps between arm and body (wide dark areas like the inside of a hood are kept), then clears a ~2px dark fringe.
- The threshold was tuned from 40 down to 14 after the first pass erased parts of very dark navy garments. Every image was checked on a contact sheet.
- Originals are kept in `data/products_original/`. The DB `image_file_path` values are unchanged.
- `backend/main.py` sends `Cache-Control: no-cache` on `/media/*`, so browsers re-check and show the corrected images right away.

---

## Agent / backend improvement 3: "Chat with Dan" voice

**What I asked for (bonus beyond the problem set):** a toggle on the chatbot between **"Chat with Campus Customs"** (the official brand voice) and **"Chat with Dan"**, in the voice of Handsome Dan, Yale's bulldog mascot. Dan is a preppy Ivy League bulldog: smart, loves sports, disdains every other Ivy, and still does unexpected "dog" things. Switching voices must keep the conversation's context seamlessly. Later, I accepted the suggestion to **remember which voice answered** each saved message: *"I was offered a feature that I did not think of and I wanted to include it. It was a good idea to remember which voice responded to the user."*

**Why it's agent/backend:** the toggle only sends `voice: "dan"`. The persona, the voice switching, the shared memory, and the saved voice labels all happen in the agent and the backend.

**How it helps**
- **Shopper:** shopping becomes fun and memorable (*sniffs the crewneck approvingly*), especially for students, alumni, and gift buyers, without losing accuracy. Prices, stock, and safety rules are identical in both voices. Shoppers can switch mid-conversation and Dan still remembers their size, budget, and the items discussed.
- **Business:** gives the store personality and school spirit that a generic chatbot can't, which encourages longer chats, return visits, and word of mouth. The brand voice stays available for shoppers who just want straight answers.

**How it works**
- **One PydanticAI agent and one shared history.** `backend/agent.py` reads `prompts/prompt.md` on every request and, when `voice == "dan"`, adds `prompts/voice_dan.md`. Only the style changes. Tools, accuracy rules, and safety are shared, so switching voices keeps full context.
- `previous_voice` (from the browser for guests, or from the last saved row for signed-in shoppers) tells the agent "the shopper just switched voices".
- `chat_messages.voice` (added safely at startup in `db.ensure_schema()`) stores `brand` or `dan` for each assistant reply, so saved chats keep their **CAMPUS CUSTOMS** / **DAN** labels after a reload.
- Front end: toggle in the chat header. The avatar, title, greeting, suggestions, typing indicator ("*sniff sniff*…"), and on-page results label ("🐶 Fetched by Handsome Dan") change with the voice.

---

## Agent / backend improvement 4: Stronger password policy

**What I asked for:** "better password strength: make users choose at least 1 number and at least 1 symbol." In the same request I asked to fix the Create Account page, where the Last name box stuck out past the card.

**Why (my reason at the time):** *"I wanted stronger passwords. There was a visual error on the frontend that I fixed."*

**How it helps**
- **Shopper:** their account, and the saved chat history and personal details tied to it, is harder to break into by guessing. A live checklist under the password box (8+ characters ✓, 1 number ✓, 1 symbol ✓) shows exactly what's missing before they submit, so no trial and error.
- **Business:** fewer weak passwords means less risk of compromised customer accounts and the trust and support costs that follow. Because the rule is enforced **on the server**, it can't be skipped by calling the API directly.

**How it works**
- `backend/auth.py` → `password_problems()`: signup is rejected with a clear 422 message unless the password is 8–256 characters with at least one digit and at least one symbol (any character that isn't a letter, digit, or space). This sits on top of the existing protections: PBKDF2-HMAC-SHA256 with 120,000 iterations, a random salt per user, constant-time comparison, and lockout after 5 failed logins.
- **Login is unchanged:** existing passwords still work, including the seeded test user's.
- `frontend/src/pages/CreateAccount.tsx`: the same three rules shown as a live checklist. `index.css` lets the form fields shrink to fit the card, which fixed the Last name overflow.

---

## Verification (Problem 9 re-check)

All four were re-tested together on the finished app on **Oct 18, 2026** (FastAPI backend with `gpt-6.1-sol` + the Vite site, in the built-in browser at 1024×768 and through the API).

| # | Improvement | Test | Result |
|---|---|---|---|
| 1 | Expandable chat (front-end) | Opened the chat (Dan voice) on the Hoodies page | Mini **372 × 548**, bubble font **13.44px** |
| | | Asked "What crewnecks do you have?", then "And quarter-zips?" | Auto-expanded to **560 × 648** (≥ ½ width **and** ≥ ½ height of the 1024 × 768 page), still `position: fixed` (overlay). Thumbnails in a grid with "+9 / +8 more shown on the page". |
| | | Clicked on the main page | Shrank back to **380 × 560**, chat **still open** |
| | | ⤢ / ⤡ header button (tested in Problem 7) | Expands and collapses on demand. Phone size (375 × 812): 351 × 712, no horizontal scroll. |
| 2 | White image backgrounds (front-end) | Scanned all 102 files in `data/products/` for black edges | **0** images with black backgrounds (74 were converted, originals kept in `data/products_original/`) |
| | | `curl -I /media/products/basic-hoodie-big-yale.jpg` | `Cache-Control: no-cache`, so browsers re-check images |
| | | Hoodies and Quarter-Zips grids in the browser | Uniform white backgrounds. One browser still had pre-fix copies cached from before the no-cache header. After a refresh, the image edge pixel read **(255, 255, 255)**. A one-time **Cmd+Shift+R** clears any old cached copies. |
| 3 | "Chat with Dan" (agent/backend) | Signed in. Brand voice: "for my brother, size XL, under $70, navy hoodies?" | "**17** navy hoodies under $70 in XL, 12 on the page" (DB check: 17) |
| | | Switched to **Dan**: "What size and budget did I give you, and who is it for? My brother goes to Princeton." | "**size XL**, **under $70**, for **your brother**… Princeton, those orange tigers… *sniffs the shopping list approvingly*". Memory kept, persona on. |
| | | Back to **brand**: "Is the Crew Left Chest Hoodie in stock in his size?" | "in stock in **XL**, **$68**". "His size" was resolved from earlier turns (DB: XL = 20). |
| | | `chat_messages.voice` for those rows | `brand`, `dan`, `brand`, each assistant reply labeled correctly. The website shows DAN / CAMPUS CUSTOMS labels. |
| 4 | Stronger passwords (agent/backend) | `POST /api/auth/signup` with `longenough` | **422**: "must include at least 1 number, include at least 1 symbol" |
| | | `longenough1` / `longenough!` | **422**: missing symbol / missing number |
| | | `Longenough1!` | **201**: account created (throwaway test account deleted afterward) |
| | | Seeded test user login (old password, no symbol) | **200**: existing accounts still work |
| | | Create Account page | Live checklist ticks each rule as you type. Last name field sits inside the card (fixed in Problem 4). |

**Result: all four usability improvements work as designed.**
