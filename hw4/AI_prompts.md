# AI Prompt Log — Campus Customs

A log of the prompts I typed to the AI coding assistant, organized by problem number and name.
Follow-up prompts are marked, along with my own explanation of why I needed them.

---

## Problem #0 — Validation Warm-up

**Prompt 1**
> create a new folder called HW #4A

**Prompt 2**
> Don't do anything yet. I'll just give you context. Campus Customs needs a real customer website with a helpful chatbot. We will build a React plus Vite TypeScript font end and a Python fast API backend whose brain is a pedantic AI agent. Shoppers will be able to browse products, create an account, chat about merch, see matching items appear on the page, and get honest answers about price and stock from a local database. We will be given a database called campus underscore customs.db with tables for the product catalog, inventory by size, and users with hashed passwords. Product image file paths are in the catalog table. Research yellbulldogblue.com to learn the style of Campus Customs page and information for the agent prompt. We will use portkey underscore API underscore key or whichever API key I have for the agent's AI calls. If we are using OpenAI through portkey, use any models in the 5.6 or 6 series. You may want smarter models for harder agent steps. We're going to work one problem at a time with the vibe coder. We're going to type each problem in my own words. We're not going to paste URLs. We are not going to give screenshots of the problems to finish everything. And in the end, we will just push our project to a public GitHub repo. We will submit the repo URL on Canvas. And the last problem shows the file tree. We will not commit database or products, product images. The data I'm going to give you has already been downloaded in a data.zip file, which I have unzipped. I will give you that shortly.

**Prompt 3**
> check to make sure that you have access to github and to my portkey_Api_key. do not expose that key

**Prompt 4** *(follow-up)*
> go ahead and install tool github CLI. are you checking the env file in root for that portkey?

*Why I needed it:* I wanted to verify connections to github and I wanted to verify access to portkey because that has been a prior issue in problem sets.

**Prompt 5** *(follow-up)*
> ok. so create an env file in root (not HW#4A that I can paste my key. open that file and I will paste it.

*Why I needed it:* I am doing this problem set from a different computer that past ones, so i had to create a new env file.

**Prompt 6** *(follow-up)*
> open it in textedit

*Why I needed it:* i needed to paste it.

**Prompt 7** *(follow-up)*
> ok. check it, test it

*Why I needed it:* verification.

**Prompt 8** *(follow-up)*
> run gh auth login

*Why I needed it:* git hub access was there, but it didn't have the tool to create the repository.

**Prompt 9** *(follow-up)*
> ok. done. check it

*Why I needed it:* verification.

**Prompt 10**
> ok. data file it there. unzip it and open the folder in finder for em to inspect it.

**Prompt 11**
> Those are 2 folders that I'm going to use for an idea I have for a later question

---

## Problem #1 — Create the AI Prompt Log (AI_Prompt.md)

**Prompt 1**
> ok. THis is probelm #1 - Create AI_Prompt.md and keep this updated as we work. This is a log of what I typed to you. As we go through the problem set, I will tell you what step we are on and you will divide this log into problem number and name of problem. There must be at least 1 prompt in each section. If I type a followup prompt, record that and then ask me to explain in my own words why I needed it. Record that as well.

**Prompt 2** *(follow-up)*
> sure. call that "Problem 0 - Validation Warm-up"

*Why I needed it:* I gave step 0 a proper title.

---

## Problem #2 — Analyze the Database

**Prompt 1**
> Problem 2 - Analyze the database: I want you to review the database data/campus_customs.db. understand the fields of the table - such as catalogue, inventory, and users. Start output/harness.md. write down each table and its fields and a short line on why each field matters for the shop or chatbot. WE will continue to add to this harness file as we go.

**Prompt 2** *(follow-up)*
> open the image files for the 3 products without colors listed. I'll review and give those to you to populate the database

*Why I needed it:* I'm cleaning up the database for the agent.

**Prompt 3** *(follow-up)*
> I'm cleaning up the database for the agent. The color of all 3 of those times is gray. are there any other missing database fields?

*Why I needed it:* verification of any other missing data.

**Prompt 4** *(follow-up)*
> yes. record those descriptions. response #3 - verification of any other missing data.

*Why I needed it:* _(not answered — I moved on to Problem #3)_

---

## Problem #3 — Build the Campus Customs Website

**Prompt 1**
> moving on. - problem #3. Build the Campus Customs website. Scaffold a React + Vibe + Typescript front end for Campus Customs. Put a nav bar at the top that links to the following main pages: Home, Products, About Us, Log In, Create Account. Pull any design and style choices as well as wording from yalebulldogblue.com for Home and About Us pages, but write these in your own voice. Do not copy the original site text. On the products page, show product images from the catalogue (use the image paths in the database) with basic product info (like name, price, short description, anything else pertinent.). Make each product open a single-item page with a large image on one side, full product text on the other - description, price, size / stock (when you have them). Clicking on a card on products should take the shopper there. Add a chat interface in the bottom right of the site - a floating chat panel would be nice. It does not need to talk to an agent yet - leave this as a stub that will call the backend that we create later in the homework project. You will also need a small API to read the database. Start a simple FastAPI app in backend/main.py to just serve products and images and we will expand this later into the agent backend in problem 5. Let me know if anything doesn't work out.

**Decision** *(answer to the AI's question)*
> Vite breaks on the "#" in the folder name "HW #4A" — rename to: **HW 4A**

**Prompt 2** *(follow-up)*
> Re: Images that have black backgrounds because they are transparent - I want them to have white backgrounds to match the other iamges

*Why I needed it:* I am keeping the images consistent with each other to have a professional appearing website.

---

## Problem #4 — Create Account and Login

**Prompt 1**
> ok. Problem #4 - Create account and login. Build a normal create-account / login flow. Create account needs first name, last name, email, password and confirm password. Login needs email and password. New Accounts go into the USERS table. Be sure to store passwords securely so neither human nor AI hackers can access them. There is already a seed database with a test user. Although I imagine this is how you will create the password structure, i'll be explicit. [use hash'ed password storage. never unhash the stored value. re-hash what the user typed. read the salt out of the stored string. no not make new ones at login. Hash the password with the same salt, compare to stored hash. use a constant-time compare. Signup and login must use the same hash settings. confirm function by logging in as the seeded test user AND as a brand new account that you create from our own app. I will do a human confirmation from the website later as well. prompt me to do that when you're ready. Update the output/harness.md file with how the auth works (what you store for a user and how the passwords are protected.)

**Prompt 2** *(follow-up — my response to the AI asking for the hash settings)*
> This is the additional information I am given that I didn't write earlier. Please record that statement as my response.

*Attached (from the assignment):* seeded test user email `test@campuscustoms.yale.edu`, its test password (given in the assignment, not repeated here), and the hash function: **PBKDF2-HMAC-SHA256, 120,000 iterations**, stored as `pbkdf2_sha256$salt$hash`.

*Why I needed it:* This is the additional information I was given in the assignment that I didn't write earlier — the AI needed the seeded user's login and the exact hash settings to match them.

**Prompt 3** *(follow-up)*
> the functionality works, but I want to enhance it. I want better password strength - make users choose at least 1 number and at least 1 symbol. Also when i am at the create user page, the last name field overhangs the background frame. fix that

*(Attached a screenshot of the Create Account page showing the Last name box sticking out past the card.)*

*Why I needed it:* I wanted stronger passwords. There was a visual error on the frontend that I fixed.

---

## Problem #5 — PydanticAI Agent Backend

**Prompt 1**
> 5 - PydanticAI agent Backend: build a shop chatbot as a pydantic behind FastAPI, and plugit into the front-end chat widget. Put the API app in backend/main.py - we should be running that with Uvicorn. Keep the agent as these four files next to it: backend/prompts/prompt.md (system prompt, which we will grow later); backend/angent.py (agent entry / wiring); backend/tools.py (tools agent can call); backend/models.py (Pydantic/ PydanticAI structured types). In main.py expose a chat route so a message from the website returns a reply from the agent along with whatever else is needed for products/ auth. use the AI model API key / portkey_api_key for the agent. Put campus customs voice and saftey basics into prompts/prompt.md (we will expand tools and safety later). Start or update types in models.py for chat replies / product cards as needed. In output/harness.md, note how the front end talks to FastAPI and how the agent is loaded (prompt file + model). Make sure that the backend runs from the backend/ folder as such "uvicorn main:app --reload --port 8000"

***

### ★★★ BONUS ENHANCEMENT (beyond the original problem set) ★★★

**Prompt 1 (continued) — bonus request**
> Here is an enhancement over the original problem set. Note it as such in the AIprompts.md file as such. Put some *** around it to call attention to the bonus work. I want there to be a toggle switch on the frontend of the chatbot. The user will have the option of "Chat with Campus Customs" in the official "brand voice" or they can "Chat with Dan" in the voice of Handsome Dan, Yale's bulldog mascot. When in the voice of Dan, he should be a preppy ivy-league bulldog, be smart, like sports, disdain all of the other Ivy League schools other than Yale, and then at the same time, do some unexpected "dog" things still. When switching from voice to voice, I want the backend agent (or agents if necessary) to still remember the context of the prior chat conversation seamlessly. If there are any problems with this, make me aware.

*Notes from the build:* one PydanticAI agent serves both voices with a shared conversation history; the voice is a per-message instruction (`backend/prompts/voice_dan.md`), so switching keeps full context. File named `backend/agent.py` (the prompt said "angent.py"). Problem flagged: saved chats don't store which voice wrote each reply (the provided `chat_messages` table has no voice column).

***

**Prompt 2** *(follow-up — answer to the AI's question about the schema)*
> Yes — add a nullable voice column to chat_messages so saved replies keep their voice label after reload.

*Why I needed it:* I was offered a feature that I did not think of and I wanted to include it. It was a good idea to remember which voice responded to the user.

---

## Problem #6 — Tools: Product Info and Stock

**Prompt 1**
> Problem 6 - Tools: product info and stock
>
> Give the agent tools that look up real information from campus_customs.db: product description, price, how many are in stock (by size when the customer asks). The agent must use the database. It must not invent prices or quantities. If a size is out of stock, say so clearly. Expand prompts/prompt.md so that the agent knows to call these tools for price and stock questions. Add or update return types in models.py. In output/harness.md list each tool and explain which model fields we have chosen for lookup results and why.

*Notes from the build:* added `get_price`, `check_stock`, and `get_product_info` (accept a product name or id; sizes like "medium"/"2XL" are understood); each returns typed results from `models.py` with stock status decided in code. Verified every answer against the database.

---

## Problem #7 — Chat Search That Updates the Page

**Prompt 1**
> Problem 7: chat search that updates the page
> Now another feature (that is required in the homework). When a customer asks about a type of item - for example "what hoodies do you have?" - the agent should search the catalogue and the website should dynamically show those matching items as product cards (like we had earlier - image, name, price, short info). This is an API contract: the agent returns structured product matches and then the front end renders them on the website. Confirm that this works no matter which voice the chatbot is in. After the dynamic product cards are loaded, confirm that the same single-item page behavior that we built in step 3 still works. Each product card, including the ones that the chat just put on the page, should still open the detailed view (large image + full info) when clicked. Update the prompts/prompt.md and output/harness.md so it is clear how search results reach the page.

*Notes from the build:* the agent's structured reply (`product_ids`, `results_title`, `see_all_category`) becomes database-backed `ProductCard`s in the `/api/chat` response; the website shows them in a "From your chat" section using the same product card component, so every card opens the Problem 3 detail page. Tested in both voices. Caught and fixed a wrong count ("12 hoodies" → real total 27).

**Prompt 2** *(follow-up)*
> I have another usability feature. When the chatbot window has a lot of images, you have to do a lot of scrolling. first, use a smaller, but still easy to read font. Second, when the chat mini-window (that's what I'm calling the current size) gets full, I want to the chat window to dynamically grow to at least half of the entire webpage. Make sure that it still is an overlay window. When the user clicks back on the main webpage, the chat window can shrink back to mini-size. there should be a collapse button as well if it is not already there. My response to your next question is: "I am building additional features to make this easier to use and be more polished."

*Why I needed it:* I am building additional features to make this easier to use and be more polished.

---

## Problem #8 — Customer Memory

**Prompt 1**
> Problem 8: Customer Memory
>
> WHen a shopper is logged in, save their chat history in the database in an appropriate table and reload it when the return. The agent should know WHO is chatting (name, email) - put that in the agent deps (or an equivalent clear pattern) and/or tools the agent can call. Also pass enough page context that if someone is on a product page and asks "do you have this in pink?" The agent knows which item they mean. You can put code into the agent context. Guests can still chat, but the chat history needs to persist only for logged-in users. Document in output/harness.md how user chat history is stored, what customer fields the agent sees, and how page context is passed.

*Notes from the build:* the agent's deps now carry a server-verified `CustomerContext` (name, email, member since, returning customer) and a `PageContext` (current page and on-screen product, checked against the database). New tools `my_account` and `get_current_page`. Signed-in chats are saved to `chat_messages` and reloaded; guest chats are never saved. Tested "do you have this in pink?" on product pages, identity questions, privacy, and memory across a fresh login.

---

## Problem #9 — Usability Improvements

**Prompt 1**
> Problem 9: Usability improvements.
>
> So I have already started some of these earlier in the homework. Reference the additional features that I have already added - the Dan Voice and the expandable chat window.
>
> Here is the problem: Now that this core shop works, we are improving it. We need to make 2 front-end usability improvement and 2 agent/ backend improvements. The problem set asks to write to output/usability.md BEFORE OR AS we build. Unfortunately, I was so excited about this project that I got ahead of myself. So, we will have to re-construct the past. Retrospectively, write to the usablity.md file what I added and why it helps either the shopper or the business. I have actually given you the context for why I added those features when we were building them. We will confirm at the end of this problem all of the improvements that we made function correctly. The graders will specifically be looking for these 4 items.
>
> I think the expanding chat window is a front-end feature while Dan's Voice is a backend feature. Would you confirm my thoughts on that?

*AI's answer:* Confirmed. The expanding chat window is front-end (all in the browser). Dan's Voice is agent/backend (persona prompt, one agent switching voices per message with shared memory, voice saved in the database); the toggle is just how the shopper picks it. The AI suggested the white image backgrounds (front-end) and the stronger password policy (backend) as the other two, since both already had my reasons on record.

**Prompt 2** *(follow-up — answer to the AI's question)*
> oh. I forgot about those. Yes. So rebuilding the image files with white backgrounds was definitely a front-end feature. The rationale was that I wanted the store items to appear seamlessly on the webpage rather than looking like a slapped together photo album. record that.

*Why I needed it:* I wanted the store items to appear seamlessly on the webpage rather than looking like a slapped together photo album.

**Prompt 3** *(follow-up)*
> I would characterize the stronger passwords was a backend feature. Agree?

*AI's answer:* Agreed. The rule is enforced on the server (`password_problems()` in `backend/auth.py`), so it can't be bypassed; the on-page checklist only mirrors it for convenience.

*Why I needed it:* I asked because I didn't want to mistakenly count it as a front-end change. I knew the answer in retrospect.

---

## Problem #10 — Style the Website

### Part A — Ask Dan Image Studio (Handsome Dan image generation tool)

**Prompt 1**
> Problem 10: Style the website
>
> We are to add creative design so that it feel like a real Campus Customs storefront - fonts, color, hierarchy, motion, production presentation. Chat feel. The innovative, the more points. Write the to output/design.md what we changed and why it should help customers stick around and make a purchase.
>
> So, we've already started some of this with Dan's voice in the chat. We will continue to develop this.
>
> Part A: This is going to involve a little side-project of Handsome Dan Image Creation tool in a new OpenAI's GPT Image 2.5 Sunburst agent to produce various images of Handsome Dan, Yale's bulldog mascot. Here is a set of instructions that I was working on with ChatGPT to accomplish this.
>
> Read ASK_DAN_CLAUDE_CODE_IMAGE_STUDIO_SPEC.txt completely.
>
> Build the Ask Dan Image Studio application according to the specification.
>
> Begin by examining the supplied ZIP files and reconciling the product inventory.
>
> I want a functioning local dashboard where I can generate, review, approve, reject, and revise individual images.
>
> Use the original Handsome Dan images as character references and the supplied Yale shields for institutional branding.
>
> Do not make any paid image-generation API calls until the application is working and I have approved the initial three-image test.
>
> Work through the development independently, but ask me when an important design decision or authorization is needed.
> There will be a Part B to Problem 9 that we will do later, but you don't have to ask me why I prompted again

*(Attached: ASK_DAN_CLAUDE_CODE_IMAGE_STUDIO_SPEC.txt, ask_dan_data2_audit.xlsx, ask_dan_data2_checklist.txt, Dan Final Images(2).zip, Dan images reference.zip)*

*Notes from the build (Phase 0, no paid calls):* built `ask-dan-image-studio/` (FastAPI + React dashboard on http://127.0.0.1:8765, `start.command` launcher, 25 tests). Independently re-verified the audit: 102 products / 102 photos / 54 Dan categories / 19 existing / 35 missing — identical counts; only 2 renamed files ("Dan Ivy Harvard Sideeye.png", "Dan Crew Rowing.png"). Cropped 31 official shields from the labeled screenshots. Confirmed `gpt-image-2.5-sunburst` is a real OpenAI model available through my Portkey key (estimated ~$0.35/image at 1536×1536 high). Full mock run tested generate → revise → exact-shield composite → compare → approve/reject → export → restart; mock results then cleared. Waiting for my approval before the 3 paid pilot images.

**Prompt 2** *(answer to the AI's question — authorization for paid images)*
> Yes. Confirm the proposed Dan references (Welcome Dan, Babe Ruth, Swimming, Ice Hockey), switch to OpenAI gpt-image-2.5-sunburst at 1536x1536 high, and run the 3-image paid pilot (about $1.06, cap $15). Then stop for my review.

**Prompt 3** *(follow-up, sent while the pilot was running)*
> If needed I have additional API credits on a personal account

*Pilot attempt result ($0 spent):* the first run failed because an old, invalid PORTKEY_API_KEY in my shell overrode the `.env` (fixed with `override=True`). The second run showed the class Portkey key is pinned to an Azure chat deployment, so it cannot make images; free invalid-size probes confirmed every routing option. Next step: my personal OpenAI key in `ask-dan-image-studio/.env`.

*Why I needed it:* I used personal credits because the Portkey key was not valid for the image creation tool used.

**Prompt 4** *(answer — personal key added)*
> It is uplaoded and saved. goahead and try

*Pilot result:* verified my personal OpenAI key (free model list + a free invalid-size probe), then generated exactly 3 images with `gpt-image-2.5-sunburst` at 1536×1536 high: SOM, lacrosse, hoodie. **Actual cost $0.376 total (~$0.125 each, from reported usage)**; the pilot authorization is used up, so nothing else can generate until I review. All three passed automated QA and are PENDING_REVIEW.

**Prompt 5** *(my pilot review)*
> Yale SOM looks great. Lacrosse has no changes needed. THe hoodie photo has drawstrings coming out of Dan's nose. That needs to be fixed

*Result:* approved SOM v1 and lacrosse v1. Revised the hoodie once (feedback: drawstrings must hang down, not out of Dan's nose; current image sent as the edit reference) → v2 fixed, $0.126. The revision first exposed an over-cautious cost estimate (~$0.34 vs actual ~$0.13), so estimates now calibrate from real usage (+25% margin). **Total spent: $0.50.** Hoodie v2 awaits my approval.

**Prompt 6** *(final pilot decision)*
> Approve hoodie v2. The pilot is complete.

*Pilot outcome:* all 3 pilot images approved (SOM v1, lacrosse v1, hoodie v2). Total cost $0.50.

**Prompt 7** *(follow-up — new studio feature)*
> Stop here. I have a revision. If iPlease include in the image creation studio a chat window to talk to the agent that we can make one-off images even if its not in the catalogue yet

*Why I needed it:* Chat window resizing was a design enhancement needed.

*Notes from the build:* added the **🐶 Ask Dan chat** tab to the studio. A PydanticAI agent turns plain-language requests into editable image briefs (official shields only, exact allowed text), and "Create & generate" makes a one-off `dan_custom_*` image through the same review/cost guards. Chat requests like "make this one nighttime" become precise revisions. One-offs stay separate from the 35 catalogue assets and export to `custom_png/`. Tested end to end with the free mock provider (Trumbull pumpkin brief kept, ready to generate); spend unchanged at $0.50; 29 tests pass.

**Prompt 8** *(authorization)*
> Generate the Trumbull pumpkin one-off for real (about $0.16) so I can review it.

*Result:* generated the Trumbull pumpkin one-off for $0.126 (total spend now $0.63). The model drew the right three bull heads but with inverted colors, so I used the free exact-shield tool. That exposed a real bug: the shield cropper had made every white pixel transparent, including white shield fields (Trumbull, Morse, Davenport…). Fixed (only border-connected background is transparent), rebuilt all 31 shields, added a regression test (30 tests pass), rejected the bad composite v2 with a reason, and made v3 with the exact official Trumbull shield. v1 and v3 await my review.

**Prompt 9** *(follow-up — review feedback)*
> ok. The shield here has the right colors, but the shield is overlying the pumpkin and his neckercheif. It has to flow better on his sweater

*Result:* upgraded the free shield compositor: (1) **occlusion** — the shield is only drawn on garment fabric; large vivid warm shapes in front (pumpkin, neckerchief, fur) stay in front, small specks from an old drawn patch are ignored; (2) **fabric blend** — knit texture borrowed from plain sweater next to the shield plus a scene-lighting tint, so it reads as part of the sweater. New dashboard controls ("Keep objects in front", "Fabric blend"), new test (31 pass). Saved as v4 (free); v3 rejected with my feedback. Spend unchanged at $0.63.

*Why I needed it:* Shields were not rendering realistically on the Dan images.

**Prompt 10** *(decision)*
> Approve v4 of the Trumbull pumpkin.

*Result:* Trumbull pumpkin v4 approved (first one-off image). Totals: 3/35 catalogue images approved + 1 one-off; $0.63 spent.

**Prompt 11** *(authorization — Phase 2)*
> Authorize and run the next supervised batch of 5 catalogue images (about $0.80), then stop for my review.

*Batch 1 result:* generated dan_apparel_other, dan_crewneck, dan_jacket, dan_performance, dan_tshirt — $0.125 each ($0.62 batch, $1.25 total), all passed automated QA, all PENDING_REVIEW; studio paused (authorization used up). AI flag for review: the T-shirt Dan has a long plumed tail (English bulldogs have short screw tails).

**Prompt 12** *(authorization — all remaining catalogue images)*
> ok. go ahead and generate all missing catalogue assets

*Result:* generated all 27 remaining catalogue images in 6 supervised batches (≤5 each, each with its own authorization; nothing auto-approved): 0 failures, all passed automated QA. **Total spend $4.64 of the $15 cap** (~$0.125/image). Catalogue status: 8/35 approved (3 pilot + 5 apparel I approved in the dashboard), 27 awaiting my review, 19 existing reused; plus 1 approved one-off (Trumbull pumpkin). AI review flags: family Dad and sport Golf show Dan very upright/human-like; family Grandpa's lower body looks like human legs in trousers; all school shields are small AI-drawn versions to check (exact-shield compositor available); Nursing / Public Health banners cut off mid-word; Medicine monitor shows numbers.

**Prompt 13** *(question)*
> have they all been reviewed?

*Answer:* yes — all 35/35 catalogue images are APPROVED (I approved the remaining 27 in the dashboard at 12:34–12:35); 0 pending. All are v1 except the hoodie (v2). With the 19 existing images, every one of the 54 Dan categories for the 102 products is covered, plus 1 one-off. Total spend $4.64.

**Prompt 14** *(final export)*
> Yes, create the final export (approved PNGs, mapping, updated workbook and checklist, and review and cost report) and check it.

*Result:* `ask-dan-image-studio/output/exports/ask_dan_export_20261018-123641.zip` (~127 MB, 43 files). Verified: 35 catalogue PNGs + 1 one-off in `custom_png/`, all valid PNGs ≥1024 px; product→Dan mapping JSON + CSV with 102 rows, every product has a Dan image (35 approved new + 19 existing); workbook keeps the original 4 sheets plus a new "Studio Status" sheet, Dan Asset Checklist updated (35 APPROVED, 19 EXISTING); TXT checklist (35 approved, 19 existing, 0 needs review, 0 missing, 1 custom); report shows $4.64 total from actual reported usage; credential scan clean.

**Prompt 15** *(request)*
> summarize Part A in the appropriate document log we've been keeping

#### Part A — Summary

**What I built:** *Ask Dan Image Studio* (`ask-dan-image-studio/`), a local, human-supervised app (FastAPI + React dashboard at http://127.0.0.1:8765, `start.command` launcher) that creates the Handsome Dan images the Campus Customs catalogue needs, plus one-off images on request. It follows ChatGPT's specification (`ASK_DAN_CLAUDE_CODE_IMAGE_STUDIO_SPEC.txt`).

**How it went, step by step**
1. **Inventory (no cost):** the AI independently re-checked the previous audit against the real data. It got the same counts (102 products, 102 photos, 54 Dan categories, 19 existing, 35 to make) and found two renamed files. It turned my 30 shield screenshots into clean official shield files and picked original "Dan" photos (never "Dan2") as identity references.
2. **Built the dashboard and safety rails:** overview, catalogue mapping, asset queue, generate/review (approve, revise with feedback, reject, compare versions), batch control, settings and export. Paid images need my authorization, a hard spending cap, a per-image cap and attempt limits. It was tested first with free placeholder images.
3. **Model:** `gpt-image-2.5-sunburst` (OpenAI), confirmed in OpenAI's docs. The class Portkey key turned out to be text-only, so images use my personal OpenAI key, kept in a local `.env` and never shown.
4. **Pilot (3 images):** School of Management and lacrosse approved; the hoodie needed one fix (drawstrings coming out of Dan's nose) and v2 was approved.
5. **My addition — Ask Dan chat:** a chat window where I describe any image (even one not in the catalogue). An AI agent drafts an editable brief and I click to generate. First one-off: Dan carving a Trumbull College pumpkin.
6. **Shield fixes:** the free "place exact shield" tool now keeps objects in front (pumpkin, neckerchief) and blends the shield into the sweater's knit. Along the way the AI found and fixed a bug that had made white shield fields transparent.
7. **Full run:** the remaining 32 catalogue images were made in supervised batches of up to 5 (0 failures), and I reviewed and approved them all in the dashboard.
8. **Final export:** `ask_dan_export_20261018-123641.zip` with 35 catalogue PNGs, 1 one-off, the product→Dan mapping (JSON/CSV), the updated audit workbook and checklist, and the review & cost report. The credential scan was clean.

**Results**

| | |
|---|---|
| Catalogue Dan images | **35/35 approved** + 19 existing reused = all 54 categories, covering all 102 products |
| One-off images | 1 approved (Trumbull pumpkin) |
| Total cost | **$4.64** (~$0.125 per image, actual reported usage; the cap was $15) |
| Tests | 31 automated tests (no real network calls in tests) |

**Problems found and fixed during Part A:** an old invalid API key in my shell overriding `.env`, the text-only Portkey key, retries blocked after a failed job, cost estimates 3× too high (now calibrated from actual usage), test placeholders that could have slipped into exports, and the shield transparency and overlap issues.

**Where things are:** app and README in `ask-dan-image-studio/`; approved images in `ask-dan-image-studio/output/approved/`; export ZIP in `ask-dan-image-studio/output/exports/`; inventory report in `ask-dan-image-studio/reports/inventory_report.md`. Next: **Part B**, styling the website and writing `output/design.md`.

### Part B — Style the Website

**Prompt 1**
> Yes, let's start Part B of Problem 10: styling the website and writing output/design.md.

**Prompt 2** *(Part B requirement)*
> Part B
> When an item is searched for in the chatbot, an image of Handsome Dan will appear for the user prior to product presentation. E.g When we look for a football-related inventory item, an image of Dan playing football against Harvard will pop up prior to presenting the appropriate products available for purchase.

**Prompt 3** *(Part B instruction)*
> The images that we created of Handsome Dan will be your resources. Place them in their own folder for reference

*Result:* created `Dan Image Resources/` (git-ignored, 171 MB): `catalogue_new/` (35 created), `catalogue_existing/` (19 originals renamed to their category id), `one_off/` (Trumbull pumpkin), and a README index of which products each image covers.

*Notes from the build:* the Dan images are the site's art (served as WebP from `data/dan/`, built from `Dan Image Resources/`). Shipped: the chat **Dan reveal before products** (chat bubble + on-page "Dan found it" banner; football → Dan vs. Harvard), a Caslon + Inter type system with Yale blue/ink/brass colors, a home "Dan stage" hero, Dan category tiles, a Halloween at Trumbull feature, Shop with Dan rails (colleges/sports/family/schools), hover "Dan's take" on cards, a product-page Dan gallery + stock meters, Dan-face chat launcher/avatar and paw typing indicator, scroll reveals with reduced-motion support. Documented in `output/design.md`.

**Prompt 4** *(request)*
> Looks great. SUmmarize it in the appropriate space like part A was

#### Part B — Summary

**What I built:** a storefront redesign that makes the site feel like the real Campus Customs store, with **Handsome Dan as the host**. The Dan images created in Part A became the site's art. The full write-up is in `output/design.md`.

**How it went, step by step**
1. **Art pipeline:** put all Dan images in their own reference folder, `Dan Image Resources/` (35 created, 19 original, 1 one-off, Welcome Dan, plus an index). A script makes web-optimized versions for the site (`data/dan/`, 13.5 MB) and maps all 102 products to their 54 Dan categories.
2. **My requirement — Dan reveal before products:** when a chat search finds items, the matching Dan image pops up first, then the products slide in, both in the chat and in the on-page "Dan found it" banner. Example: football shirts → **Dan running the football against Harvard** → the football shirts. Works in both voices and on phones.
3. **Brand look:** collegiate serif (Libre Caslon) for headings and prices, Inter for text; Yale blue, ink navy, cream and a brass accent.
4. **Home page:** a rotating "Dan stage" hero linking to products, Dan photos on the category tiles, a **Halloween at Trumbull** feature using my one-off pumpkin image, and "Shop with Dan" rails for colleges, sports, family gifts and grad schools.
5. **Products:** cards swap to "Dan's take" on hover and show color swatches; the product page has an item / Dan's take gallery and stock meters per size ("5 left", "Sold out").
6. **Chat feel:** Dan's face as the chat button and avatar, paw-print typing dots, springy messages.
7. **Motion & access:** scroll fade-ins and staggered cards, all turned off for reduced-motion users; alt text, keyboard focus, no sideways scrolling on phones.
8. **Checked in the browser:** desktop and mobile, both chat voices, hover swaps, gallery tabs, stock meters, the Dan filter banner, no new console errors. Fixed along the way: an unreadable "Ask Dan" button, uneven grids, a banner crop cutting off Dan's face, and gallery thumbnails hidden under the image.

**Why it should help sales:** Dan makes shopping fun (people stay longer); every college, sport and family role has its own Dan scene (shoppers find themselves fast); the family rail suggests gifts (a second purchase); stock meters and honest low-stock labels answer the size question; the heritage look builds trust; seasonal features give reasons to come back.

**Where things are:** `output/design.md` (design write-up), `Dan Image Resources/` (art, not committed), `scripts/import_dan_images.py` (rebuilds the site images), `frontend/src/` (pages, components, `index.css` design tokens), and `output/harness.md` section 10 (technical notes).

### Part C — Custom Dan Gear (customer-facing image studio)

**Prompt 1**
> Part 9C
> I want the focused version of the Dan image generation Studio to be a part of the Campus Custom website. We can use the image generation one-off feature on the backend through the front-end chatbot. The customer can create images of Dan and when they find one they like, then can then have it applied to a generic tee , crewneck, hoodie, mousepad, insulated cup, notebook, folder. It should be familiar to other custom gear websites that exist. I do understand that these are not current catalogue items in our database, but we can place a generic "Custom Dan Tee" "Custom Dan Mousepad" and the like for each item offered. Use appropriate pricing that you can borrow from a similar existing website like CustomInk.com

*Decisions (answers to the AI's questions):* product previews = **AI-generated blank product photos** (one-time ≈$0.90); customer limits = **Strict** — signed-in customers only, 3 images per customer per day, $3/day site-wide cap, content-safety checks. Pricing benchmarked to CustomInk single-unit ranges (tees $15–25 for 1–11; hoodies ≈$45/ea at qty 6; accessories are bulk-only there, so single prices are estimates): Tee $24.99, Crewneck $39.99, Hoodie $49.99, Mousepad $14.99, Insulated Cup $29.99, Notebook $16.99, Folder $8.99.

**Summary of Part C (what was built)**
- **Design with Dan** (`/custom`): a CustomInk-style design lab with a live preview and 4 steps (gear → Dan → place → size & quantity) for 7 generic products: Custom Dan Tee, Crewneck, Hoodie, Mousepad, Insulated Cup (20 oz), Notebook and Folder.
  - Blank product photos were AI-generated once (7 images, **$0.37**).
  - The preview layers the design onto the photo with fabric shading.
  - Sticker-style designs get their background cut out.
- **Creating Dans:** customers describe an idea → a PydanticAI art-director agent drafts a brief → **Create this Dan** makes the image with the Studio's one-off generator (`gpt-image-2.5-sunburst` + Dan reference photos). The same thing works **from the chat**: the shop agent drafts the design, quotes real prices with a new `custom_gear_info` tool, and shows a Create card.
- **Strict guards:**
  - signed-in customers only
  - 3 creations per customer per day, one at a time
  - a $3/day site-wide cap
  - safety checks: blocklist, agent rules, moderation that fails closed, and the model's own safety system
  - the browser never sends a prompt, and the server always recomputes prices
- **Bag** (`/bag`) with quantity breaks (10% off 12+, 15% off 24+), an XXL +$2 upcharge, a nav count, and a Home page promo band. Checkout stays disabled (demo).
- **Verified:** in the browser with a free mock image provider (all 7 products, drafting, creating, chat → create, bag pricing, mobile), plus scripted guard tests (daily limit, ownership, blocked brands, sizes). Docs: `output/design.md` (Part C) and `output/harness.md` §11.

**Prompt 2 (follow-up)**
> Yes, create one real test Dan image (about $0.10) as the test customer and show me how it looks on the gear.

*Why I needed it:* I needed to verify that it works in real time.

*Result:* the real paid path worked end to end. On the hoodie page, the agent drafted "Dan the Yale crew coxswain" (sticker style), and one real image was made in 36 s for **$0.07**. It was a clean cut-out with no background, and it looked right on the hoodie, tee, cup and notebook previews.


### Part C2 — Saved designs, guardrails, and Dan's voice

**Prompt 1**
> Part C2.  If the customer does make a custom image, save it in their account for 90 days in case they decide to come back in the future and purchase other product with it again.  Be sure the customer is aware of the limit.  There have to be guardrails on what Dan images can be made.  There can never be anything sexual, with foul language, disparaging of any demographic, or overly violent. The cartoon violence toward the "rivals" images is acceptable.  If the image creation request is rejected, we must respond to the user in a clever Dan voice.
>
> In the chat bot, if there is no internet connection or other error, Rather than a generic statement, make that error appear in the voice of Dan.  Something like "I seem to have trouble finding where I buried that.  You are going to have to ask me later." Or make some more appropriate reference to Dan and needing an internet connection.  It can be any of 5 different phrases.   Also, in the opening statement that Dan makes in the chat window, I want it to vary each time.  One of 7-10 different phrases.  Dan also has "quite right, old sport" stated constantly everywhere.  We need at least 10 appropriate phrases for him.  Be sure to test these out.

**Summary of Part C2 (what was built)**
- **Saved for 90 days:** created Dans stay in the customer's account for 90 days, and customers are told on the Create note, in My designs, on each design tile, in the bag, on the Account page ("My Dan designs") and by the chat agent. Expired designs, their files and any bag lines using them are deleted automatically.
- **Guardrails:** never sexual, foul language, disparaging any group, or overly violent; cartoon slapstick rivalry is allowed. There are 4 layers: local checks, agent rules, OpenAI moderation (with a violence threshold so cartoon tackles pass), and the image model's safety system. Refusals are always written **in Dan's voice** (witty, kind, with a fun alternative) and don't use a daily creation.
- **Dan's voice in the chat:**
  - errors use 1 of 5 Dan lines instead of a generic message
  - the opening greeting is 1 of 9 lines
  - Dan rotates 14 signature phrases, with "quite right, old sport" rationed, and the server tells the agent which phrases he used recently
  - product pages now each get their own phrase
- **Tested:**
  - 12/12 guardrail cases (real agent and moderation, no images)
  - the 90-day purge
  - greetings: 7 different in 10 chats
  - error lines with the backend stopped: no back-to-back repeats
  - an 8-turn chat: 7 different catchphrases, zero "old sport"
  - the production build


### Part D — Product photos for every color

**Prompt 1**
> Part D There are some items that are available in multiple colors yet there is only one images.  For example "Super Heavyweight Crewneck Arched Yale Crest". When you click the color on the webpage I want to see a matching color shirt appear.  You may need to render additional images to make that happen.

*Finding:* the catalog's `colors` lists the colors **in each design** (garment + print), not separate colorways, and stock is tracked per size only.
*Decision (answer to the AI's question):* **Treat as colorways** — render each listed color as a garment colorway (print recolored to stay readable), ~138 images (~$8–9, hard cap $12), with a 3-image pilot for review first.

*Pilot (3 images, $0.18):* Super Heavyweight Crewneck in navy and white, Basic Hoodie Big Yale in white. The design was kept exactly, only the fabric changed, and print colors flipped where needed to stay readable.

**Prompt 2** *(authorization)*
> The pilot looks good. Approve rendering the remaining 134 colorways (about $8.10, hard cap $12), then show me a review sheet.


**Summary of Part D (what was built)**
- Each listed color is now a **colorway** with its own product photo: **137 new photos for 90 products** ($8.42 including the 3-image pilot, cap $12).
  - Each one is an AI edit of the real product photo that changes only the fabric color and keeps the print readable.
  - Two base colors were corrected by eye.
  - Every render was checked on six review sheets.
- **Product page:** "Color: ___" swatch buttons swap the photo; card color dots open the product in that color. The chat assistant explains that stock is per size across colors.

**Prompt 3** *(follow-up)*
> Please make a note to the professor that I have intentionally expanded the product inventory in choosing additional colors.  It is called "Campus Customs" after all.

*Why I needed it:* It is called "Campus Customs" after all. Offering more colors was a deliberate choice, not a misreading of the data.

> **Note to the professor:** I intentionally expanded the product inventory by choosing additional colors. The catalog's `colors` field originally described the colors *in* each design, and I chose to offer each of those colors as its own colorway, with a rendered product photo for every one (137 new colorways across 90 products). It is called "Campus Customs" after all.

**Prompt 4** *(follow-up to Part D)*
> when we pick a new color for the product from the webpage and it is not currently in inventory, indicate that it is a custom order and will be ready for pickup or delivery in 2-3 weeks.

*Why I needed it:* The new colors I added aren't in the store's inventory yet, so shoppers need to know they're custom orders with a lead time.

*Result:*
- Only each item's **original (photographed) color** is in inventory; every other color is now a **custom order**.
- **On the product page**, choosing a custom color:
  - tags it "custom" on its swatch
  - shows a notice: *"🧵 Custom order — Navy isn't on our shelves yet, so we'll make it for you in any size. It will be ready for pickup at 57 Broadway or delivery in 2–3 weeks."*, with a link back to the in-stock color
  - shows made-to-order sizes instead of the stock meters
  - changes the button to "Custom order · ready in 2–3 weeks"
- **In the chat**, the tools now report `stocked_color` and `custom_order_colors`, and `check_stock` accepts a color. Navy in M → custom order, 2–3 weeks; heather gray in M → "only 5 left".
- Tested on the page and with the real agent.

## Problem #10 Part E — Who's visiting? (welcome question, decade themes, rival mode)

**Prompt 1**
> Part E
> The first thing that should happen when you get to the website is that in the chat window, a question should appear "Are you a Current Student, Alumnus, Family, Friend or Rival?" If the answer is alumn, then I want the entire website to be re-imagined in the style of that decad - colors, fonts, and embellishments, all change to match.  An image of Dan dressed in the clothing of that decade should appear as well.  For example, if the Alum is from the 1920's, the entire website should become ArtDeco, and Dan should look like he fell out of the Great Gatsby and have a flapper at his side.  The earliest decade we have to imagine will be the 1920s.  If they respond with Student, ask which college or grad school and lead them to the appropriate Dan image and catalogue item.  If family or friend, to appropriate products.  If RIVAL is answered, ask which one.  At that point, Heavily increase the YALE branding presence on the website and show the Dan image of the appropriate rival.

*Decision (answer to the AI's question):* "make decade dans. all other rival images were previously made and given in a zip file" → generate the **11 decade Dans** (~$0.80, cap $3); use the 7 existing **Dan Ivy** rival images from `Dan Final Images` (Harvard, Princeton, Brown, Columbia, Cornell, Dartmouth, Penn).

**Summary of Part E (what was built)**
- **Welcome question** in the chat on arrival, with one-tap answers. The answer is remembered, and "Change" asks again.
- **Student** → college or school → Dan image and those catalogue items. **Family** → which family member → Dan image and products. **Friend** → 6 gift picks.
- **Alumnus** → decade → the whole site re-styled (colors, fonts, decorations) for 11 decades, 1920s–2020s, with a banner of Dan dressed for that decade (1920s: Art Deco plus Gatsby Dan with a flapper). 11 decade Dans: $0.77.
- **Rival** → which Ivy → "Yale overload" (Yale-blue header, YALE marquee, watermark, card ribbons, a giant YALE in the hero and footer) plus that rival's existing Dan image.
- The shop agent also receives what the visitor said and tailors its suggestions.
- Tested every path in the browser (desktop and phone) and with the real agent.


## Problem #10 Part F — Fix the field hockey Dan

**Prompt 1**
> Part F
> We need to fix the field hockey image.  In it Dan has 5 legs.

**Summary of Part F (what was fixed)**
- The Part A field hockey Dan had **5 legs**: the "dribbling with a paw on the stick" pose confused the image model.
- I regenerated it with a pose a real bulldog can manage (the stick carried in his mouth, the ball at his paws) and an explicit anatomy rule (exactly four legs, nothing held in the paws). It's at the same size and quality as the catalogue (1536 px, high).
- I made 2 candidates ($0.19) and picked **v1**, where all four legs are visible. It replaces the image everywhere (product pages, rails, chat reveal). The 5-legged original is kept in `Dan Image Resources/fixes/`.

## Problem #11 — Site Testing (app check)

**Prompt 1**
> Problem 11: Site Testing (app check)
>
> You and I will test the site separately.  Document testing in output/app_check.html (a page that we can double-click open.  Include clear screenshots and short captions for:
> 1. Chat checking the inventory level of an item (honest stock/price from the DB)
> 2. Dynamic search-results cards appearing after category questions (i.e hoodies)
> 3. Test one of the usability features from problem 9
>
> Make the HTML easy to grade: a heading for each check, a screenshot, one to two sentences of what the screenshot proves.  Put the screenshot image files in output/app_check_images/ and link them from app_check.html with relative paths (e.g. app_check_iumages/inventory.png)

**Summary of Problem 11 (what was done)**
- Built **`output/app_check.html`**, a page that opens with a double-click. It has a heading, screenshot(s) and a 1–2 sentence caption for each check, and all 7 images live in `output/app_check_images/` with relative links.
  1. **Inventory in chat:** "Is this shirt in stock in XL and in M? How much is it?" on the Yale Bowl T-Shirt → *sold out in XL, only 5 left in M, $32.00*. That matches the database row (XL 0, M 5, $32.00) and the page's stock meters.
  2. **Search-results cards:** "What hoodies do you have?" → the real total (27 hoodies) and **12 product cards** on the page under a Dan banner.
  3. **Usability (Problem 9):** the expandable chat: mini → auto-expands to fit the reply → shrinks back (still open) when you click the page.
- The screenshots were taken in Google Chrome by a repeatable script (`scripts/app_check_screenshots.py`, Playwright), which also saves the chat replies and database values.
- **Bugs found and fixed while testing:**
  - The chat's auto-expand ran before reply images loaded, so it never expanded. It now re-checks as the images load.
  - A reply said "12 shown" when 11 cards appeared. A prompt rule now ties that number to the cards actually returned; 3 out of 3 re-runs were correct.

**Prompt 2** *(follow-up to Part E, after my own testing)*
> So I've found a couple of things about the chat bot.  I don't like that it opens instantly when the site loads.  It should be collapsed in the corner.  But if 10-15 seconds pass and no one has opened Dan's chat yet, it needs to have a dynamic word bubble pop out of it and start "barking" and getting the users attention.  I only want the "student, alum, rival..." question asked when chatting with Dan as the first question, not with the campus customs side.   I also need a way to get back to that initial question, so perhaps when the New Chat button is pressed, or when someone says "start over" or "go back to the first question" we go back to that initial question.  If someone along the way specifically says they are a rival, Dan should ask which one.   or if the user bring up the name of one of the other IVY schools, then the rival Dan image should be produced.

*Why I needed it:* I tested the site myself and found these behaviors with the chat bot that I wanted changed.

*Result (Part E follow-up):*
- **Collapsed on load:** the chat no longer opens by itself.
- **Barking bubble:** if nobody opens it within ~12 seconds, a speech bubble pops out of Dan's chat button and "barks" ("Woof!" → "Woof! Woof!" → "*sniff sniff* Psst… over here!" → "I'm Handsome Dan! Want help finding gear?") while the button bounces. Clicking the bubble opens Dan's chat, and × dismisses it for the visit.
- **Welcome question in Dan's voice only:** the Campus Customs side just says hello.
- **Back to the first question:** **New chat**, typing "start over" or "go back to the first question", or "Not you? Change" all clear the conversation and the earlier answer, and Dan asks again.
- **Rivals:**
  - Typing "I'm a rival" mid-chat makes Dan ask *which school?* with buttons; picking one turns on rival mode and shows that rival's Dan.
  - Naming any other Ivy in a message ("my cousin goes to Princeton") attaches that rival's Dan image to the reply.
  - "Brown" and "Penn" only count in school-like phrases, so "brown hoodie" and "Penn State" don't trigger it. The detectors were unit-tested on 15 phrases.
- Every path was tested in the browser.

**Prompt 3** *(follow-up, found in my testing)*
> i asked dan to bring me to the design with dan page. it does not link there.

*Why I needed it:* Dan should be able to take shoppers to pages on the site when they ask, and he couldn't.

*Result:*
- The agent's structured reply has a new `go_to` field, limited to the site's real pages: Design with Dan, bag, products, about, account, log in, create account, home.
- When a shopper asks to go somewhere, the chat takes them there and leaves a **"Go to …" button** in the reply.
- Tested against the real agent:
  - 4 out of 4 navigation requests went to the right page ("bring me to the design with Dan page", "take me to my bag", "where do I sign up?", "where do I go to make my own Dan shirt?"), in both voices.
  - An ordinary question (navy hoodies) didn't navigate.
  - In the browser, "Bring me to the design with Dan page" moved from Home to Design with Dan, with the link in Dan's reply.

**Prompt 4** *(follow-up)*
> when the chat moves on from discussion of rivals, the website returns to hits default "not-Yale-heavy" mode

*Why I needed it:* The Yale-heavy rival look should only last while the conversation is about rivals; after that the site should go back to normal.

*Result:*
- Rival mode (the Yale-overload look) now follows the conversation:
  - **Ends** as soon as the shopper's next message isn't about rivals; the site returns to its normal look.
  - **Kept:** the fact that they're a rival fan, so Dan still teases.
  - **Returns** when they bring up a rival or the rivalry again ("Harvard", "rival", "The Game"), switching to whichever school they named.
- **Tested in the browser:** Princeton → overload on; "Do you have any navy hoodies?" → off; "What would annoy a Harvard fan the most?" → on again, now Harvard.

## Problem #10 Part G — More variety in the college Dans

**Prompt 1**
> There are several of the Dan undergrad college images that look very simlar.  we need to render new ones with the Dan image studio for those to improve variety

*Finding:* all 11 college images were originals from `Dan Final Images`; 10 of them (all but Benjamin Franklin) reuse the same "Dan on autumn Gothic steps with a banner, books, tote, mug and laptop" layout, which the studio's own rules ban.
*Decision (answer to the AI's question):* **re-render all 10 look-alikes** in the Ask Dan Image Studio (~$1.25, hard cap $3), each with its own college-specific scene and the official college shield, and review before publishing.

**Summary of Part G (what was done)**
- **New scenes:** in the **Ask Dan Image Studio**, each of the 10 look-alike college images got its own college-specific scene, set as a prompt override, plus its **official college shield** as a reference:
  - Berkeley: pancake-flipping brunch chef
  - Branford: Harkness Tower carillon
  - Davenport: snowball fight
  - Grace Hopper: the 1940s computer "first bug"
  - Jonathan Edwards: the JE spider mascot
  - Morse: a telegraph key in the modernist courtyard
  - Pierson: croquet on the summer lawn
  - Saybrook: muddy intramural soccer
  - Timothy Dwight: late-night grilled cheese
  - Trumbull: a library nap under stained glass
- **The old template was banned:** no steps, autumn leaves, books, tote, mug or laptop.
- **Rendering:** through the studio's normal guards (two authorized batches of 5, $0.80 each), **$1.26 total** (studio lifetime spend now $5.89 of its $15 cap).
- **Review:** old vs. new on `output/college_variety_review.jpg`. All 10 chest shields match the official shields; the old banners had inaccurate crests.
- **Published:** all 10 approved in the studio and live on the site (rail, chat reveal, Student welcome path). The originals were kept in `Dan Image Resources/replaced_college_originals/`.

## Problem #12 — Audit trail, safety, finish harness

**Prompt 1**
> Problem 12: Audit trail, safety, finish harness
>
> Keep an append-only output/audit_trail.json of agent-loop activity (time, tool name, short args/ result, stop reason) Do not wipe it between runs.  Here are some safety rules as well.  You can add to them if appropriate. Record them all in prompts/prompt.md
>
> *(Rules given: AI model — `gpt-5.6-luna` default, configurable via `OPENAI_MODEL`, smaller model only for simple low-risk tasks; API keys and secrets — never hard-code, load from `.env`, `PORTKEY_API_KEY` for Portkey calls, `OPENAI_API_KEY` only for direct OpenAI calls, `.env` in `.gitignore` with a `.env.example`, never print secrets, rotate if exposed; App appearance — old bank / green glass / brass / leather / oak style for executive-summary HTML by default, responsive and accessible; Dependencies — `pydantic-ai-slim[openai]` in `requirements.txt`, not the full `pydantic-ai`; Dash run and stop rules — `use_reloader=False`, check for orphan servers on the port, kill the whole process tree; Dropbox and OneDrive — pause sync or exclude `.venv` while installing, keep venvs local and uncommitted; Project hygiene — keep each app self-contained, small focused changes, verify clean start.)*
>
> Finish the output/harness.md so it is clear how the system works.  Model fields in models.py and why we chose them.  The tools and abilities, the safety rules, the Specs (loop limits, results caps, models, how to run from & back)
>
> Once you've done this I want this all assembled into an HTML page called "Executive Briefing". Style it like an old bank with green glass, oak, brass.  The first page needs to be a top-level summary page and if the exec wants any details, he can click into each section and get a full detail description.  Make a link to the app check HTML available from that page. At the bottom of this page as well as the bottom of every html page produced I want you to note that this is not a real retail site.  It is not affiliated with campus customs.  That it was created by Dr_BMo for Yale School of Management's class MGT 409E - AI Foundations for Managers.

**Summary of Problem 12 (what was done)**
- **Audit trail:** `output/audit_trail.json` is append-only. Every shop-agent and design-agent run logs `run_start`, each `tool_call` and `tool_result` (short, with emails and numbers masked), and `run_end` with the stop reason (`final_output (stop)`, `usage_limit`, `content_filter`, `error`). New entries rewrite only the closing bracket, so old entries never change and nothing wipes the file.
  - **Verified:** 40 concurrent appends left the file valid with every earlier byte unchanged. Live chats logged `check_stock`, `get_price` and `search_products`.
- **Rules:** recorded in `backend/prompts/prompt.md` below a `<!-- PROJECT RULES` marker. They're kept in the file but not sent to the model. That covers every rule given, plus project additions: paid-call approval and caps, customer limits, content guardrails, least-privilege tools, the audit trail, loop limits, no committed customer data, additive database changes, browser verification, and the disclaimer.
- **Model:** `gpt-5.6-luna` (env `OPENAI_MODEL`) is set in one place, `backend/config.py`. It was tested through Portkey with tools, and the studio reads the same variable.
- **Hygiene:**
  - `requirements.txt` (top of hw4/) and `ask-dan-image-studio/requirements.txt` use `pydantic-ai-slim[openai]`.
  - `.env.example` lists names only, and `.gitignore` was fixed so it isn't ignored.
  - The secret scan was clean.
  - The 31 studio tests still pass.
- **`output/harness.md`:** finished with a new **Part I — How the system works**:
  - overview diagram
  - how to run the front and back end
  - specs table (models, loop limits, result caps, input caps, accounts, custom-gear limits, ports)
  - the agent loop step by step
  - every model in `models.py` with its fields and why
  - tools and abilities
  - safety rules
  - audit-trail format
  - file map

  The earlier sections became Part II, the build log.
- **`output/executive_briefing.html`:** an old-bank style page (green glass, brass, oak, leather). It opens on a one-page summary (key numbers, Dan gallery, nine section plaques). Each plaque opens a full detail page with a link back, and there are links to `app_check.html`. It works offline by double-click, including on phones.
- **Disclaimer** ("not a real retail site… not affiliated with Campus Customs… created by Dr_BMo for Yale SOM MGT 409E") is now at the bottom of the Executive Briefing, the App Check report, every page of the website, and the Ask Dan Image Studio.

## Problem #13 — Push to GitHub and submit the URL

**Prompt 1**
> Problem 13 - Push it to GitHub and submit URL.
> Put the code in a folder named "hw4" and push it to a public GitHub repository.  I will submit the URL(s)  for the repo - the link graders can open and clone.  There will not be a zip to upload to Canvas for this assignment.  Do Not put real .env campus_customs or product images in the GitHub repo.  You can use the .gitignore for that.  You can use env.example as a placeholder. BUT, for any of the images that WE rendered (like all the Dans), we will need to upload those. I also want to make sure that it was clear to the prof, TAs, and the AI grading tool that significant work went into the enhancements of this project.  I want to make sure that the executive summary page is available to them.  I want to make sure that they see the Dan image creation studio is available to them to inspect and you can encourage them try out.  The basic agent itself is four files under backend/: prompts/prompt.md, agent.py, tools.py, and models.py.  Readme.md should explain how to run the front and back end after placing the data pack.  See uploaded basic file structure.  Additional folders will be needed to add the enhancements, I'm sure.
>
> *(Attached: the expected file structure — `hw4/` with `AI_prompts.md`, `requirements.txt`, `.env.example`, `.gitignore`, `README.md`, `frontend/`, `backend/` (`main.py`, `agent.py`, `models.py`, `tools.py`, `prompts/prompt.md`), `output/` (`harness.md`, `design.md`, `usability.md`, `app_check.html`, `app_check_images/`, `audit_trail.json`); local-only data pack `data/` with `campus_customs.db` and `products/`.)*

**Follow-up (mid-task)**
> this is the first AI project for this class on github.  i would do one repo per project

*Why I needed it:* This is the class's first AI project on GitHub, and I want one repository per project.

**Summary of Problem 13 (what was done)**
- **Repo:** public, one repo for this project: **https://github.com/dr-bmo2255/mgt409e-hw4**, with all code in **`hw4/`** following the given structure.
  - The project folder moved to `mgt409e-hw4/hw4/` (Python environments rebuilt, launch configs updated).
  - `AI_Prompt.md` was renamed to `AI_prompts.md`, and `requirements.txt` moved to the top of `hw4/`.
- **Not in the repo:** `.env` files, `campus_customs.db`, the original product photos, customer designs, the studio's run state, and the course zips. `.env.example` is the placeholder.
  - The backend finds the owner's `.env` outside the repo, or a grader's `hw4/.env`.
- **In the repo:** every image we rendered — all Handsome Dan art (`data/dan/`), the custom-gear mockups, and the 137 product colorways — plus the briefing images and the app-check screenshots.
- **README:** "Graders: start here" links to the Executive Briefing, the App Check, the Image Studio, the harness and this log. It also has the core 4-file agent table, the 11 enhancements, the repo layout, run steps after placing the data pack, and an invitation to try the Ask Dan Image Studio in free mock mode.
- **Live pages (GitHub Pages):** the Executive Briefing and the App Check open in a browser.
- **Verified from a clean clone** with the data pack placed:
  - The backend starts **even without a key** (the store works and the chat explains the setup), which was fixed during this check.
  - With a key, the chat answers correctly.
  - All images load.
  - The website builds.
  - The Image Studio starts in mock mode and makes a $0.00 test image.

**Prompt 2** *(follow-up)*
> i'm just thinking that we altered the database file when we made the Custom Dan image ordering page.   We may need to upload the database rather than ignore it.  If so, update the readme file, explain why and be sure that the graders use the correct db file

*Why I needed it:* I realized we had changed the database during the project, so graders using the original file might not get a working site.

*Result:* I checked the original data-pack database against ours.
- **What actually changed:**
  - The only catalogue changes were the **3 Problem 2 fixes** (colors, description, garment type, tags for the 3 "Vision blocked" stubs).
  - Everything else was additive: new tables and the chat `voice` column, which the backend already creates.
  - Inventory was unchanged.
  - Our copy also holds test accounts and chats.
  - Separately, **74 product photos** had been given white backgrounds in Problem 3.
- **Decision:** don't upload the database. The assignment says not to commit it, and our copy contains test accounts' password hashes and chats. Instead, the backend upgrades the ORIGINAL data pack on first start:
  1. the 3 catalogue fixes come from `backend/data_fixes.json`, applied only while the rows are still stubs
  2. the 74 photo backgrounds are whitened with the same script, originals kept
- **Verified** from a fresh clone with the untouched data pack: the catalogue and inventory are row-for-row identical to ours, and 102 of 102 photos are byte-identical.
- **README:** "Place the data pack" now says to use the ORIGINAL files, shows what is upgraded automatically (with the log lines to look for), and explains why the database isn't uploaded.
