"""Pydantic / PydanticAI structured types for the chat API and the agent."""

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field

Voice = Literal["brand", "dan"]
# Pages the chat can take a shopper to (the website maps each to a real route; no free-form URLs).
SitePage = Literal["home", "products", "design_with_dan", "bag", "about", "account", "login", "create_account"]
Category = Literal["Quarter-Zips", "Jackets & Fleece", "Hoodies", "Crewnecks", "Long Sleeve", "T-Shirts"]
MAX_PAGE_RESULTS = 12
Role = Literal["user", "assistant"]

MAX_MESSAGE_CHARS = 2000
MAX_HISTORY_TURNS = 30


# --- Agent-side types -----------------------------------------------------------


class CustomerContext(BaseModel):
    """Who is chatting. Built on the server from the session cookie + users table,
    never from anything the browser claims. No password_hash, ever."""

    user_id: int = Field(exclude=True)  # server-side only (saving history); not shown to the model
    first_name: str
    last_name: str
    email: str
    member_since: str | None = Field(default=None, description="Account creation date (YYYY-MM-DD)")
    returning_customer: bool = Field(default=False, description="True if they have chatted with us before")


class PageContextIn(BaseModel):
    """What the browser reports about the page the shopper is looking at (untrusted input)."""

    path: str = Field(default="/", max_length=200)
    product_id: str | None = Field(default=None, max_length=120)
    category: str | None = Field(default=None, max_length=40)
    search: str | None = Field(default=None, max_length=100)


class PageContext(BaseModel):
    """Page context after the server has checked it against the database.
    product_name / price come from the DB, not from the browser."""

    path: str
    page_type: Literal["home", "products", "product", "about", "account", "login", "signup", "chat_results", "custom", "bag", "other"]
    product_id: str | None = None
    product_name: str | None = None
    product_price: float | None = None
    category: str | None = None
    search: str | None = None


@dataclass
class ShopDeps:
    """Per-request context the agent's instructions and tools can read (PydanticAI deps)."""

    voice: Voice = "brand"
    customer: CustomerContext | None = None  # None = guest
    page: PageContext | None = None
    switched_voice: bool = False  # the previous assistant turn was in the other voice
    # Dan's catchphrases already used in recent replies, and a fresh one suggested for this reply (Part C2).
    recent_phrases: list[str] = field(default_factory=list)
    suggested_phrase: str | None = None
    visitor: str | None = None  # Part E: self-reported visitor type, e.g. "Yale alumnus from the 1960s"


class DesignBrief(BaseModel):
    """A custom Handsome Dan image the shopper wants on Custom Dan Gear (Problem 10 Part C).
    The agent only drafts it. Generating it is the shopper's button press, which goes through
    the server's guards (signed in, 3 per day, site budget, moderation)."""

    title: str = Field(max_length=60, description='Short name for the design, e.g. "Dan the Yale Bowl quarterback"')
    scene: str = Field(
        max_length=500,
        description="What the image shows: where Handsome Dan is, what he wears or holds, his pose, and the fun detail. "
        "One continuous scene, Dan the clear hero. No real people, no logos or brands, no other mascots.",
    )
    style: Literal["photo", "sticker"] = Field(
        default="photo",
        description="photo = a square photo print; sticker = a bold die-cut illustration of Dan with no background "
        "(looks best on hoodies, cups and notebooks)",
    )
    text: list[str] = Field(
        default_factory=list,
        max_length=3,
        description='The ONLY words allowed in the image, spelled exactly (e.g. ["YALE"]). Usually empty.',
    )


class AgentReply(BaseModel):
    """What the agent must return: the API contract between the agent and the website.
    The backend turns product_ids into real product cards from the database (so prices and
    stock on cards can never be invented) and the frontend renders them on the page."""

    reply: str = Field(description="The message to show the shopper in the chat. Markdown allowed (bold, short lists).")
    product_ids: list[str] = Field(
        default_factory=list,
        max_length=MAX_PAGE_RESULTS,
        description="Matching products to show ON THE PAGE as cards: exact product_id values copied from "
        "tool results, most relevant first, up to 12. Empty when no specific products apply.",
    )
    results_title: str | None = Field(
        default=None,
        max_length=60,
        description='Short plain heading for the on-page results, e.g. "Hoodies", "Navy crewnecks under $60", '
        '"Berkeley College gear". None when product_ids is empty.',
    )
    see_all_category: Category | None = Field(
        default=None,
        description="Set when the shopper is browsing a whole category and there are more matches than you "
        "listed, so the page can link to the full category.",
    )
    go_to: SitePage | None = Field(
        default=None,
        description="Set ONLY when the shopper asks to go to / open / be taken to a page of this website "
        '(e.g. "take me to Design with Dan", "open my bag", "where do I log in?"). The website then takes them there.',
    )
    custom_design: DesignBrief | None = Field(
        default=None,
        description="Set ONLY when the shopper asks you to create / design a custom Handsome Dan image for Custom Dan "
        "Gear. The chat shows it as a card with a 'Create this Dan' button. Leave None otherwise.",
    )


# --- Tool result types (what tools hand back to the model) ------------------------
# Every number here is copied from campus_customs.db by the tool, never produced by the model.

StockStatus = Literal["in_stock", "low_stock", "sold_out", "not_offered"]


class SizeStock(BaseModel):
    """Plain size/quantity pair (used on product cards sent to the website)."""

    size: str
    quantity: int


class SizeAvailability(BaseModel):
    """One size of one product, with its status already decided, so the model can't
    blur "0 left" into "available"."""

    size: str = Field(description="XS, S, M, L, XL or XXL")
    quantity: int = Field(description="Units on hand right now (0 = sold out)")
    status: StockStatus = Field(description="in_stock (>5), low_stock (1-5), sold_out (0)")


class ProductSummary(BaseModel):
    """Search result row: enough to recommend and compare, not the full record."""

    product_id: str = Field(description="Exact id to pass to other tools and to product_ids")
    name: str = Field(description="Display name to use in replies")
    category: str
    garment_type: str
    price: float = Field(description="USD, exactly as listed in the catalog")
    colors: list[str]
    description: str
    in_stock_sizes: list[str]
    sold_out_sizes: list[str]
    total_stock: int


class SearchResults(BaseModel):
    """search_products result: the best matches plus how many exist in total, so the agent
    never reports "12 hoodies" when 12 is only how many it was shown."""

    total_matches: int = Field(description="How many products in the catalog match, in total")
    showing: int = Field(description="How many are in `products` (capped by limit)")
    products: list[ProductSummary]
    more_available: bool = Field(description="True when total_matches > showing; mention the total and set see_all_category")


class ProductInfo(BaseModel):
    """Full record for one product: description, price, colors, and stock by size."""

    product_id: str
    name: str
    category: str
    garment_type: str
    description: str
    colors: list[str]
    search_tags: list[str]
    price: float = Field(description="USD, exactly as listed in the catalog")
    price_display: str = Field(description='Price formatted for the reply, e.g. "$68.00"')
    sizes: list[SizeAvailability]
    in_stock_sizes: list[str]
    sold_out_sizes: list[str]
    total_stock: int
    stocked_color: str | None = Field(default=None, description="The color the stock counts are for (the one on the shelf now)")
    custom_order_colors: list[str] = Field(
        default_factory=list,
        description="Other colors this item comes in. Not in inventory: custom orders, any size, ready for pickup at 57 Broadway or delivery in 2-3 weeks",
    )


class PriceInfo(BaseModel):
    """Answer to "how much is X?"."""

    product_id: str
    name: str
    price: float
    currency: Literal["USD"] = "USD"
    price_display: str
    note: str = "Listed price. No sales, coupons, or discounts are available."


class StockReport(BaseModel):
    """Answer to "is X in stock (in size Y)?"."""

    product_id: str
    name: str
    price_display: str
    requested_size: str | None = Field(description="Normalized size the shopper asked about, if any")
    requested_status: StockStatus | None = Field(description="Status of requested_size; None if no size was asked")
    requested_quantity: int | None = Field(description="Units of requested_size on hand; None if no size asked or not offered")
    sizes: list[SizeAvailability] = Field(description="Every size the product comes in, XS→XXL")
    in_stock_sizes: list[str]
    sold_out_sizes: list[str]
    total_stock: int
    stocked_color: str | None = Field(default=None, description="The color the stock counts are for (the one on the shelf now)")
    custom_order_colors: list[str] = Field(
        default_factory=list,
        description="Other colors this item comes in. Not in inventory: custom orders, any size, ready for pickup at 57 Broadway or delivery in 2-3 weeks",
    )
    requested_color: str | None = Field(default=None, description="Color the shopper asked about, if any")
    summary: str = Field(description="One plain sentence stating the stock facts; safe to paraphrase, never contradict")


class ProductMatch(BaseModel):
    product_id: str
    name: str
    price: float


class ProductNotFound(BaseModel):
    """Returned when a product reference can't be matched to exactly one item."""

    query: str
    message: str
    suggestions: list[ProductMatch] = Field(description="Closest real products (may be empty). Ask the shopper which one, or say none match.")


# --- HTTP API types -------------------------------------------------------------------


class ChatTurn(BaseModel):
    role: Role
    content: str = Field(max_length=MAX_MESSAGE_CHARS * 4)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)
    voice: Voice = "brand"
    # Where the shopper is on the site, so "this" / "this one" can be resolved.
    page: PageContextIn | None = None
    # The voice of the previous assistant reply, so the agent knows the shopper just switched.
    previous_voice: Voice | None = None
    # Part E: who the shopper said they are in the welcome question (self-reported, short).
    visitor: str | None = Field(default=None, max_length=120)
    # Only used for signed-out shoppers. Signed-in shoppers' history comes from the database.
    history: list[ChatTurn] = Field(default_factory=list, max_length=200)


class DanImage(BaseModel):
    """A Handsome Dan category image shown before / beside products."""

    asset_id: str
    image_url: str
    thumb_url: str
    caption: str
    category: str
    group: str
    aspect: float


class ProductCard(BaseModel):
    product_id: str
    name: str
    category: str
    price: float
    image_url: str
    colors: list[str]
    description: str
    total_stock: int
    inventory: list[SizeStock]
    dan: DanImage | None = None


class DraftedBrief(DesignBrief):
    """A DesignBrief saved on the server; generating it sends only brief_id back."""

    brief_id: int


class ChatResponse(BaseModel):
    """POST /api/chat response. `products` is what the website renders as on-page cards."""

    reply: str
    products: list[ProductCard]
    results_title: str | None = None
    see_all_category: Category | None = None
    # Shown BEFORE the products: the Dan image for the category the search landed in.
    dan: DanImage | None = None
    # A drafted Custom Dan Gear design (saved server-side; the browser only gets its id back).
    design: DraftedBrief | None = None
    # A page the shopper asked to be taken to; the chat navigates there and shows a link.
    go_to: SitePage | None = None
    voice: Voice


class ChatHistoryMessage(BaseModel):
    role: Role
    content: str
    voice: Voice | None = None
    products: list[ProductCard] = Field(default_factory=list)
    created_at: str | None = None
