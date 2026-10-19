# Campus Customs: Storefront Design (Problem 10)

> Written as we build. Part A produced the art (Ask Dan Image Studio: 54 Handsome Dan category images covering all 102 products). Part B uses it to make the site feel like a real Campus Customs storefront and to make customers **stay longer and buy**.

## Design goals
1. **Feel like the real store.** Yale navy, collegiate serif type, warm New Haven photography. It should look like a shop that has been on Broadway for years, not a template.
2. **Make Handsome Dan the host.** Every product has a Dan image for its category. Dan greets you, models the merchandise, and pops up in the chat before the products.
3. **Delight → dwell → decide.** Small surprises (Dan reveals, hover swaps, motion) keep people browsing. Clear hierarchy and honest stock info help them choose.
4. **Fast and accessible.** Web-optimized images (WebP, ~13 MB for all 54 categories at two sizes), lazy loading, keyboard support, and `prefers-reduced-motion` respected.

## Planned changes
| Area | Change | Why it helps customers stay / buy |
|---|---|---|
| **Chat search → Dan reveal** *(Part B requirement)* | When a chat search finds products, the matching Dan image pops up first (e.g. football → Dan running the ball against Harvard), then the products slide in. | A moment of fun before the sell builds anticipation and emotional connection, and shows instantly that the shop "got" the request. |
| Typography | Serif display face for headlines (collegiate, heritage) + clean sans for body and UI. | Instant brand signal; easier scanning (headlines vs. details). |
| Color & surfaces | Yale blue `#00356B`, ink navy, warm cream, with a restrained brass accent for prices and badges. | Matches the brand people are shopping for; warmth reads "boutique", not "discount site". |
| Home hero | Rotating Dan photo stage (crossfade + slow zoom) with a headline and two clear CTAs. | Personality in the first second; a clear next step. |
| "Shop with Dan" | Category tiles and rails (colleges, sports, family gifts) illustrated with the Dan images. | Turns browsing into exploring; makes niche identities (your college, your sport, your role) easy to find. |
| Product cards | Hover / focus swaps the product photo for "Dan's take" on that category; badges for low stock. | Two looks per card; honest scarcity nudges purchase. |
| Product page | Gallery with product photo + Dan image; a size grid with stock meters. | Confidence about the item and the size before buying. |
| Chat feel | Dan's face as the avatar, paw-print typing indicator, springy message entrance, Dan voice styling. | A chat that feels like a character, not a form, so people ask more and find more. |
| Motion | Scroll reveals, staggered card entrances, micro-interactions. All disabled under reduced motion. | Polish and flow without slowing anyone down. |
| Seasonal | October feature: "Halloween at Trumbull" with the one-off pumpkin image. | Timely, shareable content gives a reason to come back. |

## Implementation log (what shipped)

### 0. Art pipeline: `Dan Image Resources/` → the site
- All Handsome Dan images live in **`Dan Image Resources/`** (git-ignored, 171 MB):
  - `catalogue_new/`: the 35 created in Part A
  - `catalogue_existing/`: the 19 originals, renamed to their category id
  - `one_off/`: the Trumbull pumpkin
  - `brand/`: Welcome Dan
  - a README index of which products each image covers
- `scripts/import_dan_images.py` turns them into web-optimized **WebP** files in `data/dan/`: 1200 px + 480 px for each of the 54 categories (13.5 MB total), Dan's face cropped for the chat avatar, and `dan_map.json` (102 products → 54 Dan categories).
- Backend: `/media/dan/*` is served. Every product carries a `dan` block (image, caption, category). Chat responses carry a `dan` block for the category the search landed in: the most common Dan category among the matched products (`catalog.dan_for_products`).

### 1. Chat search → Dan reveal (Part B requirement)
- **In the chat bubble:** the reply text, then the **Dan image pops in** (spring scale + slight rotation, 0.7 s), then the product thumbnails rise in one by one starting at 0.85 s.
- **On the page:** the "From your chat" section opens with a **"Dan found it"** banner (the full Dan scene + a serif caption). The product cards then stagger in after ~0.9 s.
- **Example:** "Do you have any football shirts?" → Dan running the football **against Harvard** → the 3 football shirts. Works in both voices ("Got any lacrosse gear?" in Dan's voice → Dan's lacrosse image → Lacrosse Left Chest Crewneck).
- *Why:* a beat of delight before the sell confirms the shop understood ("that's exactly football"), builds anticipation, and makes the moment memorable and shareable. Customers who are entertained browse longer.

### 2. Typography & color (brand system)
- **Libre Caslon Display** for headlines, prices and wordmark (heritage, collegiate); **Libre Caslon Text italic** for accents ("*handsomely*"); **Inter** for UI and body.
- Tokens: Yale blue `#00356B`, ink navy `#001A35`, paper `#FBF9F4`, cream, **brass `#B08D3C`** for kickers, the primary CTA and prices-of-note; coral only for "low stock".
- Pill buttons with soft depth; a frosted sticky header; an ink-navy footer.
- *Why:* the site now looks like the brand customers are buying. Serif headings vs. sans details create a clear **hierarchy**: what it is → what it costs → what to do.

### 3. Home page
- **Dan stage hero:** 5 rotating Dan photos (crossfade + slow Ken Burns zoom, 5 s each, dot controls), each with a *"Shop it →"* caption linking to exactly those products. Proof points underneath: 102 styles · XS–XXL live stock · 30-day returns.
- **Find your fit:** the 6 category tiles are Dan photos (Dan in the hoodie, crewneck, tee…) with zoom on hover.
- **Halloween at Trumbull:** an October feature built on the Part A one-off (Dan carving his own face into a pumpkin) → Shop Trumbull / All colleges.
- **Shop with Dan rails:** horizontally scrolling, snap-aligned rails for *Colleges*, *Sports*, *Family gifts* and *Grad schools*. Each card is a Dan scene with an item count, linking to `/products?dan=<category>`.
- *Why:* the first screen shows personality and a clear next step. The rails turn identity ("my college", "my sport", "for Grandpa") into an easy path to the right products, so customers buy for themselves **and** for gifts.

### 4. Product cards & listing
- Hover or keyboard focus **cross-fades the product photo to "Dan's take"** on that category (with a 🐶 tag). Color swatches replace color words, and serif prices.
- The `?dan=` filter shows a **Dan banner** above the matching products.
- *Why:* two looks per card without a click; swatches can be scanned faster than text.

### 5. Product page
- A gallery with **The item / Dan's take** tabs (cross-fade), plus a Dan quote with his avatar.
- **Stock meters** per size (navy bar; coral "5 left"; greyed "Sold out") instead of a number table.
- *Why:* customers see stock and their size at a glance. Honest low-stock signals create urgency **without** fake scarcity, and Dan adds warmth at the decision point.

### 6. Chat feel
- **Dan's face** is the launcher (with an occasional head-tilt "nudge") and the Dan-voice avatar.
- Springy message entrance, and a 🐾🐾🐾 paw-print typing indicator.
- *Why:* the assistant feels like a character, not a form. People ask more questions, and every question is a chance to surface products.

### 7. Motion & accessibility
- Scroll-reveal (IntersectionObserver), staggered card entrances, card hover lift, Ken Burns hero.
- **`prefers-reduced-motion`** turns off all animation and makes reveals instant.
- Alt text on every Dan image; ARIA labels on the carousel, rails and gallery tabs; visible keyboard focus.
- Lazy-loaded WebP images, and a mobile layout with no horizontal scroll.

## Why this should help customers stick around and buy
| Lever | Mechanism |
|---|---|
| **Emotional hook** | Dan's personality turns shopping into entertainment (reveals, rails, seasonal story), so visitors stay longer. |
| **Relevance** | Every category, college, sport and family role has its own Dan scene, so shoppers recognize themselves quickly. |
| **Gift discovery** | The Family rail and the Mom/Dad/Grandpa scenes surface a second purchase reason ("for my dad"). |
| **Confidence** | Stock meters, the Dan's take gallery and honest "low stock" signals answer the size question before it blocks checkout. |
| **Brand trust** | Heritage serif + Yale blue + licensed messaging read as an established, official store. |
| **Repeat visits** | Seasonal features (Halloween at Trumbull) give people a reason to come back and share. |

## Verified in the browser (Oct 18, 2026)
- Home: hero Dan stage (football vs. Harvard first), category tiles, Halloween band, best sellers, four Dan rails. Mobile 375 px: no horizontal scroll, launcher shows only Dan's face.
- Chat search "Do you have any football shirts?" (brand voice): **Dan football vs. Harvard image appeared first**, then 3 products. Page banner "Dan found it · Dan's in the game: Football", then the cards.
- Dan voice on mobile, "Got any lacrosse gear?": Dan lacrosse image → Lacrosse Left Chest Crewneck.
- Product page (Yale Sports Hoodie Hockey): "Dan's take" tab cross-fades to Dan playing ice hockey; stock meters show XS sold out and M "5 left".
- Card hover on Hoodies swaps to Dan in the giant hoodie with the "Dan's take" tag. The `?dan=dan_college_trumbull` banner works.
- No new console errors.

---

# Part C: Custom Dan Gear ("Design with Dan")

> A focused, customer-facing version of the Ask Dan Image Studio, built into the shop. Customers dream up a Handsome Dan, the shop creates the image, and they put it on a tee, crewneck, hoodie, mousepad, insulated cup, notebook or folder, the way custom-gear sites like CustomInk work.

## How it works for a customer
1. **Pick your gear.** The 7 blank products are real product photos: AI-generated blanks, made once for **$0.37** total (7 × ~$0.053).
2. **Pick your Dan.** There are three tabs:
   - **Create new:** describe an idea, choose **Photo** or **Sticker** (or let Dan decide), and press **Draft it**. Dan's art director (a PydanticAI agent) writes a short brief. Pressing **Create this Dan** makes the image.
   - **My designs:** everything the customer has created.
   - **Classic Dan:** 6 of the shop's own Dan images, free to use.
3. **Place it.** Size and position sliders. The mousepad prints full-bleed.
4. **Size & quantity.** Live price per item and total, with quantity breaks. Then **Add to bag**.
5. **Or do it from the chat:** "make me a Dan rowing on the Housatonic for a hoodie" → the shop agent drafts the design, quotes the real price, and shows a **Create this Dan** card → the page opens with Dan "posing" until the image is ready.

## Familiar custom-gear patterns we borrowed
| Pattern (CustomInk-style) | Our version |
|---|---|
| Design lab: big live preview on the left, steps on the right | Sticky mockup preview + 4 numbered steps |
| Product picker with "from" prices | 7 gear tiles with photo and price |
| Clip-art library / upload your own | **Classic Dan** library + **Create new** (AI, with guards) |
| Resize / move the art inside a print area | Size and position sliders; a dashed print-area guide while there's no art |
| Quantity discounts shown up front | "10% off 12+ · 15% off 24+", price per item updates live |
| Bag with editable quantities | `/bag` with mockup thumbnails, +/−, remove, server-computed subtotal |

## Pricing (single-piece, benchmarked to CustomInk)
| Product | Price | Benchmark |
|---|---|---|
| Custom Dan Tee | **$24.99** | CustomInk tees run about $15–25 each for 1–11 pieces |
| Custom Dan Crewneck | **$39.99** | CustomInk crewneck sweatshirts are about $35–45 each in small runs |
| Custom Dan Hoodie | **$49.99** | CustomInk hoodies are about $45 each at qty 6, so 1 piece costs more |
| Custom Dan Mousepad | **$14.99** | CustomInk sells mouse pads in bulk only (100 minimum); priced like single-piece print shops |
| Custom Dan Insulated Cup (20 oz) | **$29.99** | Single-piece branded 20 oz tumblers sell for $25–35 |
| Custom Dan Notebook | **$16.99** | Full-color custom notebooks run $12–20 each in small quantities |
| Custom Dan Folder | **$8.99** | Custom pocket folders are a few dollars each in bulk, so a single folder costs more |

XXL apparel is **+$2.00**, a common size upcharge. Quantity breaks are **10% off 12+** and **15% off 24+**. Custom gear is made to order and **can't be returned**, which matches the store's existing returns policy.

## Design choices
- **Realistic previews without a second image call.** The design is layered over the blank photo in CSS. On light products, the product photo is multiplied back over the art (masked to the art's own shape), so shirt folds and shading show through like a real print. The cup gets a curved-edge fade. The navy hoodie keeps the art at full strength.
- **Sticker style** cuts the white background out on the server (flood fill from the border only, so Dan's white fur and the sticker outline stay). That way the art sits directly on a navy hoodie.
- **Home page promo** ("Design your own Handsome Dan") shows a tee, hoodie and cup wearing classic Dan designs, and links into the design lab with that combination already selected.
- **Nav:** a new **Design with Dan** link and a **Bag** link with a brass count badge.
- **Mobile:** single column, with the step tiles hidden so the designer starts above the fold. No horizontal scroll at 375 px.

## Safety and cost guards (the "Strict" choice)
- **Signed-in customers only** can draft or create. Guests can still preview classic Dans on any product.
- **3 creations per customer per day**. An image that fails for free doesn't count. Only **one creation at a time** per customer.
- **A $3/day site-wide spending cap.** In-flight images are reserved at $0.15 each until the actual cost is known.
- **Content safety, in layers:**
  1. A local blocklist for brands, characters and hate symbols, checked before anything is spent.
  2. The art-director agent's rules: no real people, logos or other schools' crests, and nothing violent, sexual, hateful or political.
  3. OpenAI's moderation check on the brief. This fails *closed*: if the check is down, no image is made.
  4. The image model's own safety system.
- **The browser never sends a prompt.** It sends only `brief_id`. Briefs are written and stored on the server, and prices are recomputed on the server.
- **Real cost** is recorded from the API's token usage. Each image uses `gpt-image-2.5-sunburst` at 1024×1024 high quality with 2 Dan reference photos.

## Why this should help sales
- **A reason to buy that nobody else has:** a one-of-a-kind Dan made just for you (your sport, your college, your inside joke).
- **Gifts and groups:** quantity breaks make team, club and family orders natural.
- **Engagement:** creating a design takes a minute or two and gets shared. The chat can start a design at the moment someone is excited about an idea.
- **Low risk:** free classic designs mean everyone can try it. Strict limits keep the image bill predictable (at most $3/day).

## Verified in the browser (Oct 18, 2026)
These checks used the free mock image provider, a real design agent, and a real shop agent:
- **Design lab:** all 7 products render with the print area in the right place: tee, crewneck, navy hoodie, full-bleed mousepad, cup, notebook cover, folder cover.
- **Draft:** "Dan as a hockey goalie at Ingalls Rink…" plus Sticker → the agent drafted "Dan's Ingalls Rink glove save".
- **Create:** went to My designs, and the sticker sat cleanly on the tee and the hoodie (no box behind it after the shading fix).
- **Pricing:** XXL hoodie $51.99. 12 crewnecks → $35.99 each (10% off), $431.88. The bag and nav count updated.
- **Chat:** "Can you make me a custom Dan for a hoodie? Dan rowing crew on the Housatonic…" → the agent quoted $49.99 (XXL $51.99) from `custom_gear_info`, drafted "Dan Rows at Sunrise", and noted no returns. **Create this Dan** opened the design lab with that design selected.
- **Guards (scripted, on a copy of the DB):**
  - the 4th creation in a day was refused
  - another customer couldn't use someone else's design or brief
  - a "Nike" idea was refused for free
  - an unknown classic design was refused, and so was a wrong size
- **Mobile 375 px:** no horizontal scroll. **Production build:** OK. **Console:** no errors.
- **Real paid test (after approval):** the test customer, on the hoodie page, entered "Cheerful Dan in a Yale crew rowing outfit holding a blue oar, sticker style".
  - The agent drafted "Dan the Yale crew coxswain", and **Create this Dan** made a real `gpt-image-2.5-sunburst` image in **36 s** for **$0.0705** (from reported usage).
  - The result was clearly Handsome Dan in a navy-and-white striped rowing shirt and cap with a blue oar. It had a clean die-cut outline and a transparent background, with no stray text.
  - It looked right on the navy hoodie, white tee, cup and notebook previews. The allowance dropped to 2 of 3 left.

---

# Part C2: Saved designs, guardrails, and Dan's voice

## Saved for 90 days
- Every Dan a customer creates is saved in their account for **90 days**, so they can come back and put it on more gear.
- **Customers are told in five places:**
  - the Create note ("Saved in your account for 90 days")
  - a banner in **My designs**
  - each design tile ("Sticker · 89d left", with "saved until Jan 17, 2027" on hover)
  - the bag ("Your design is saved until …")
  - a new **My Dan designs** list on the Account page
- The chat agent and its `custom_gear_info` tool also mention it.
- After 90 days the design is deleted for good: the image files, the database row, and any bag lines that use it (`custom.purge_expired()`, run at startup and whenever designs are listed).

## Guardrails on what Dan images can be made
**Never allowed:**
- anything sexual
- foul language (even censored, like "F***")
- anything disparaging any group of people
- overly violent scenes: blood, gore, injuries, weapons aimed at anyone, or Dan hurt or scared

**Allowed:** good-natured **cartoon** rivalry, written as harmless slapstick. For example, Dan bowling over a Harvard lineman in crimson, or chasing a cartoon Princeton tiger up a tree. Nobody gets hurt, and no school logos.

| Layer | What it catches | Cost |
|---|---|---|
| Local checks (`custom.check_text`) | other brands and characters, foul words, hate symbols, in the idea **and** in the agent's own draft | free, instant |
| Art-director agent rules | sexual, disparaging, overly violent, real people, politics; allows cartoon rivalry | 1 cheap text call |
| OpenAI moderation (`omni-moderation-latest`) | always blocks the sexual, hate, harassment, self-harm, illicit and graphic-violence categories; plain "violence" blocks only above a 0.80 score, so cartoon tackles pass | free, fails closed |
| Image model's own safety system | anything that slips through | — |

## Refusals in Dan's voice
- Every rejection is answered by **Handsome Dan**, even when the shopper is chatting with the brand voice.
- **When the agent declines:** it opens with a short dog action, gives a witty, kind reason, and pitches a fun alternative. Examples:
  - *"trots primly behind a velvet curtain"* That pose is not fit for a Yale bulldog…
  - *"buries the sign beneath a Yale Bowl bench"*… how about Dan holding a "BOOLA BOOLA" sign?
- **When the server declines:** it picks from Dan lines for each reason (`backend/dan_voice.py`): brands, language, unsafe, and the image service declining.
  - Example: *"covers both ears with his paws"* Language! A Yale gentleman-dog keeps it clean.
- A refused idea never uses one of the customer's 3 daily creations.

## Chat errors in Dan's voice
- **Before:** if the chat can't reach the server or the internet, or anything else fails, it showed a generic red error.
- **Now:** Dan shows one of **5** lines, styled as a Dan bubble. The same line never repeats twice in a row, and the shopper's message stays in the box to resend. Examples:
  - *"digs frantically"* I seem to have trouble finding where I buried that…
  - *"barks at the Wi-Fi"* The connection wandered off like a Harvard fan at halftime…
- The design lab uses the same lines for connection failures.

## Dan's opening line varies
Dan's greeting is one of **9** lines, re-picked each time a chat starts (on opening an empty chat, and on New chat). It's never the same line twice in a row.

## More than "quite right, old sport"
- **Dan's repertoire:** 14 signature phrases, including:
  - "Boola boola!"
  - "Splendid choice."
  - "Now that's proper Bulldog blue."
  - "Mother Yale would approve."
  - "Top-drawer stuff."
  - "Capital idea."
  - "Bully for you!"
  - "Fit for The Game."
  - "Paws down, a winner."
  - "That's the Whiffenpoof spirit."
  - "Very Old Campus of you."
  - "Woof. Approved."
- **Rationing:** "Jolly good" and "Quite right, old sport" are allowed only rarely.
- **Rotation:** on each turn, the server finds the phrases Dan used in his last 6 replies, tells the agent not to repeat them, and suggests one fresh phrase. Many replies need no catchphrase at all.
- **Product pages:** the quote was "…Quite right, old sport." on every page. Now each product gets its own stable phrase.

## Tested (Oct 18, 2026)
- **Guardrails:** 12 ideas went through the real design agent and real moderation (no images made); all 12 behaved as intended.
  - **Drafted:**
    - Dan running past a cartoon Harvard lineman
    - chasing a Princeton tiger up a tree
    - bowling over the Harvard defense like pins
    - rowing at sunrise
  - **Refused in Dan's voice:**
    - a sexy lingerie pose
    - an "F*** Harvard" sign
    - "this sh*t is lit"
    - mocking immigrants
    - mocking disabled people
    - mauling with blood
    - a gun at a Princeton fan
    - Nike sneakers
    - (in the browser) a rude hand gesture at Harvard fans; the daily allowance stayed at 2 of 3
- **90 days:**
  - The real design shows "saved until Jan 17, 2027 · 89 days left" in My designs, the account page and the bag.
  - A planted 91-day-old design, its image files and its bag line were all deleted, and the expired design can't be added to the bag (404).
- **Greetings:** 10 new chats gave 7 different openings, with no back-to-back repeats.
- **Errors:** with the backend stopped, 6 sends gave Dan error lines with no back-to-back repeats, and the message stayed in the box.
- **Catchphrases:** an 8-turn Dan-voice chat used **7 different phrases with no repeats and zero "old sport"**. Prices and stock stayed exact (for example, "sold out in XL").
- **Product pages:** 4 products showed 4 different Dan quotes.
- Production build OK, and no console errors in a fresh tab.

---

# Part D: A product photo for every color

> **Note to the professor:** I intentionally expanded the product inventory by choosing additional colors. The catalog's `colors` field originally described the colors *in* each design, and I chose to offer each of those colors as its own colorway, with a rendered product photo for every one (137 new colorways across 90 products). It is called "Campus Customs" after all.

**Problem:** many items list several colors but had one photo.

**Finding:** the catalog's `colors` field lists every color *in* the product (garment + print), not separate colorways, and stock is tracked per size only. With your approval, each listed color is now treated as a **colorway**.

## How it works
- **Detect the color in each existing photo:** `scripts/colorways.py plan` samples plain fabric below the print and matches it to the nearest listed color. Two products were fooled by heathered fabric and were set by eye ("The Game" tee = heather gray, Nursing tee = navy).
- **Render the other colors:** each one is an **image edit of the real product photo** (`gpt-image-2.5-sunburst`). Only the fabric color changes; the design, text, layout, folds and white background stay. If a print would disappear (navy lettering on a navy shirt), just that part of the print is recolored to a contrasting listed color.
- **Results:**
  - **Pilot:** 3 images ($0.18), approved.
  - **Remaining 134:** rendered with 4 parallel workers under a locked **$12 cap**.
  - One temporary OpenAI 520 error stopped the run; the resume skipped finished images.
  - **137 colorways for 90 products, $8.42 total.**
- **Review:** six sheets in `output/colorway_review/` (original + every colorway, 15 products per sheet), all checked by eye. The only weak spot is Pierson's yellow-and-black crest on a yellow shirt, which is still visible.

## On the site
- **Product page:** "Color: Navy" with round **swatch buttons**. Clicking one cross-fades the main photo (and "The item" thumbnail) to that colorway.
- **Product cards:** clicking a color dot opens the product page already showing that color (`?color=navy`).
- **Stocked vs. custom-order colors:** only the original (photographed) color is in inventory. Every other colorway is a **custom order**: the swatch is tagged "custom", a notice says it's made to order in any size and **ready for pickup at 57 Broadway or delivery in 2–3 weeks**, the stock meters give way to made-to-order sizes, and the button reads "Custom order · ready in 2–3 weeks".
- **Chat assistant:** gives the same answer. It knows each item's stocked color and its custom-order colors (for example, "navy in medium is a custom order, 2–3 weeks; the stock counts are for heather gray").

---

# Part E: Who's visiting? (welcome question, decade themes, rival mode)

## The welcome question
The first thing on the site, in the chat window: **"Are you a Current Student, Alumnus, Family, Friend or Rival?"**
- The chat opens by itself for a new visitor, with one-tap answers plus "Just browsing".
- The answer is remembered in the browser, so returning visitors aren't asked again. "Not you? Change" in the banner asks again.
- It's a short **scripted** conversation (instant, free, no AI call) in either chat voice. The answer is also passed to the shop agent, which tailors its suggestions.

| Answer | Follow-up | What happens |
|---|---|---|
| **Current Student** | Which residential college or grad school? (11 colleges, 11 schools) | Dan's image for that college or school appears in the chat, and its catalogue items appear on the page under a "Dan found it" banner |
| **Alumnus** | Which decade did you graduate? (1920s–2020s) | The **whole site** is re-styled for that decade, and a banner on every page shows **Dan dressed for that decade** |
| **Family** | Who are we shopping for? (Mom, Dad, Grandma, Grandpa, Aunt, Uncle, Brother, Cousin) | That family Dan and the matching products ("For Dad", 3 items) |
| **Friend** | — | Six crowd-pleasing gift picks, one from every category |
| **Rival** | Which school? (the 7 other Ivies) | **Yale overload** across the site, plus Dan's image for that rival |

## Decade themes (alumni)
Each decade swaps the colors, fonts and decorations everywhere (header, buttons, cards, headings, chat, footer) through `html[data-era]` in `src/eras.css`.

| Decade | Look | Fonts | Decorations |
|---|---|---|---|
| 1920s | Art Deco / Gatsby: black, gold, cream | Limelight + Josefin Sans | Deco fan pattern, double gold rules, diamond-flanked headings, gold-framed cards, a diamond logo |
| 1930s | Streamline Moderne: teal, cream, rust | Big Shoulders + Libre Baskerville | Speed-line stripes, chrome pill buttons |
| 1940s | Swing-era poster: olive, red, paper | Bebas Neue + Courier Prime | ★ kickers, ticket-stub cards, stamped buttons |
| 1950s | Atomic diner: turquoise, pink | Pacifico + Nunito | Checkerboard trim, starburst dots, chrome cards |
| 1960s | Mod and flower power: orange, magenta, yellow | Righteous + Quicksand | Op-art circles, ✿ kickers, blob cards |
| 1970s | Disco: brown, orange, mustard | Shrikhand + Nunito | Rainbow stripes, ☮ kickers |
| 1980s | Neon synthwave: black, hot pink, cyan | Monoton + Exo 2 | Neon grid, glowing text and cards |
| 1990s | Early web: teal, purple | Permanent Marker + Verdana | Memphis confetti, beveled buttons |
| 2000s | Y2K gloss: aqua, silver | Orbitron + Trebuchet | Glossy gel buttons, bubble gradients |
| 2010s | Flat design: turquoise, coral | Lobster + Raleway | Flat, shadowless UI |
| 2020s | Today's design | — | Banner only |

**Decade Dans:** 11 new images ($0.77), made with the shop's Dan identity rules and reference photos. For example: the 1920s Gatsby Dan in a tuxedo and boater with **a flapper at his side**, the 1950s soda-fountain Dan, the 1980s boombox Dan, and the 2020s video-call Dan.

## Rival mode ("Yale overload")
**Rival Dans:** the 7 **existing** Dan Ivy images (Harvard, Princeton, Brown, Columbia, Cornell, Dartmouth, Penn), cartoon rivalry with nobody hurt.

**Yale branding added everywhere:**
- a Yale-blue header and a scrolling "YALE · BOOLA BOOLA · BULLDOGS" marquee
- a "Visitor from Princeton detected — You're in YALE country now" banner with the rival Dan
- a giant **YALE** above the home headline
- a faint YALE watermark behind every page
- a "YALE ·" prefix on every section heading
- a YALE corner ribbon on every product card
- a giant YALE in the footer

## Tested (Oct 19, 2026)
- **New visitor:** the chat opened by itself with the question. After answering, a reload doesn't ask again, and **Change** clears the theme and asks again.
- **Alumnus:** 1920s → full Art Deco, with the Gatsby Dan banner and gold-framed cards. The 1930s, 1940s, 1950s, 1960s, 1970s, 1980s and 1990s themes were each checked on the home page.
- **Student:** 22 college and school choices; Berkeley → Dan's Berkeley image plus 2 items on the page.
- **Family:** Dad → Dan's Dad image plus 3 items. **Friend:** 6 gift picks.
- **Rival:** Princeton → Yale overload plus Dan vs. Princeton. Cornell checked on a 375 px phone with no horizontal scroll, after fixing a hidden button and a dark menu icon.
- **Agent:** a "Harvard fan" got the Yale vs. Harvard tee suggested, and a "1920s alumnus" got period-flavored suggestions.
- **Part D:** Branford 1/4 Zip `?color=yellow` shows the yellow photo, and all 5 swatches have photos. Production build OK.

---

# Part F: Field hockey Dan fixed
- **The problem:** the Part A field hockey image gave Dan **five legs**. The "paw on the stick while dribbling" pose confused the image model.
- **The fix:** regenerated with `scripts/fix_field_hockey.py` at the same size and quality as the catalogue (1536 px, high).
  - **New pose:** Dan trots across the blue turf carrying the stick in his mouth, with the ball at his front paws.
  - **Anatomy rule:** exactly four legs, and nothing held in the paws.
- **Cost:** 2 candidates for $0.19. v1 was chosen (all four legs visible, Y shin guards on the front legs).
- **Where it changed:** `Dan Image Resources/catalogue_new/dan_sport_field_hockey.png` now holds the new image, and `scripts/import_dan_images.py` rebuilt the site images, so it's updated on the Field Hockey page, product cards and the chat reveal. The old image is kept as `fixes/dan_sport_field_hockey_v0_five_legs.png`.

## Part E follow-up: a quieter, smarter welcome (after the owner's own testing)
- **No pop-up on arrival:** the chat stays collapsed in the corner.
- **Dan barks for attention:** after ~12 seconds with the chat unopened, a speech bubble pops out of Dan's button. It cycles "Woof!" → "Woof! Woof!" → "*sniff sniff* Psst… over here!" → "I'm Handsome Dan! Want help finding gear?" while the button bounces. Clicking it opens Dan's chat, and × dismisses it for the visit. It respects reduced motion.
- **The welcome question is Dan's first question only.** "Chat with Campus Customs" opens with its normal greeting; switching to Dan shows the question.
- **Getting back to the question:** **New chat**, typing "start over" / "go back to the first question", or the banner's "Not you? Change". Each clears the conversation and the earlier answer (and its theme), and Dan asks again.
- **Rivals in conversation:**
  - "I'm a rival" → Dan: *"A rival, eh? Which school, if we must ask?"* with the 7 Ivy buttons → that rival's Dan image plus Yale-overload mode.
  - Naming another Ivy anywhere ("My cousin goes to Princeton…") → that rival's Dan image appears with the reply.
- **Tested in the browser:**
  - The chat stays closed on load; the bark bubble appears at ~12 s.
  - The Campus Customs side shows no question; the Dan side does.
  - "Actually, I'm a rival" → Dartmouth → rival mode plus Dan vs. Dartmouth.
  - "Can we go back to the first question?" → reset to the question.
  - The Princeton mention → Dan vs. Princeton image with the agent's reply.
  - New chat on the Campus Customs side → greeting; switching to Dan → the question.

---

# Part G: More variety in the college Dans
- **The problem:** 10 of the 11 residential-college images (all originals) used the same composition: Dan on autumn Gothic steps with a banner, books, a tote, a mug and a laptop. On the "Your residential college" rail they looked like one picture repeated.
- **The fix, in the Ask Dan Image Studio:** a new scene for each college that plays on something about that college, with the official college shield on Dan's sweater.
  - **Scenes:**
    - Berkeley brunch chef
    - Branford in the Harkness Tower carillon
    - Davenport snowball fight
    - Grace Hopper and the computer "first bug"
    - The Jonathan Edwards spider
    - A Morse code telegraph
    - Pierson croquet
    - Saybrook mud-soccer goal
    - Timothy Dwight midnight grilled cheese
    - A Trumbull library nap
  - **Spend:** 10 images in two authorized batches, **$1.26**.
  - **Review:** reviewed side by side (`output/college_variety_review.jpg`) and approved in the studio.
  - **Shields:** checked against the official shield files, and all 10 are right. The old banners had inaccurate crests.
- **Result:** the rail, the chat's Dan reveal and the Student welcome path now show 11 clearly different Dans. Benjamin Franklin keeps its original statue scene.
