"""Tools the Campus Customs agent can call. All read-only, all straight from
campus_customs.db, so every price and stock count in an answer comes from data,
not from the model's imagination."""

from pydantic_ai import RunContext

import catalog
import custom
from models import (
    PriceInfo,
    ProductInfo,
    ProductMatch,
    ProductNotFound,
    ProductSummary,
    SearchResults,
    ShopDeps,
    SizeAvailability,
    StockReport,
)


def _money(price: float) -> str:
    return f"${price:,.2f}"


def _sizes(p: dict) -> list[SizeAvailability]:
    return [SizeAvailability(size=s["size"], quantity=s["quantity"], status=catalog.stock_status(s["quantity"])) for s in p["inventory"]]


def _summary(p: dict) -> ProductSummary:
    inv = p.get("inventory", [])
    return ProductSummary(
        product_id=p["product_id"],
        name=catalog.display_name(p["name"]),
        category=p["category"],
        garment_type=p["garment_type"],
        price=p["price"],
        colors=p["colors"],
        description=p["description"],
        in_stock_sizes=[s["size"] for s in inv if s["quantity"] > 0],
        sold_out_sizes=[s["size"] for s in inv if s["quantity"] <= 0],
        total_stock=p["total_stock"],
    )


def _not_found(product: str, candidates: list[dict]) -> ProductNotFound:
    if candidates:
        msg = f"'{product}' matches more than one product. Ask the shopper which one they mean, or use the exact product_id."
    else:
        msg = f"No product matches '{product}'. Tell the shopper we don't carry it; search_products can find alternatives."
    return ProductNotFound(
        query=product,
        message=msg,
        suggestions=[ProductMatch(product_id=c["product_id"], name=catalog.display_name(c["name"]), price=c["price"]) for c in candidates],
    )


# --- Discovery ---------------------------------------------------------------------


def search_products(
    query: str = "",
    category: str | None = None,
    color: str | None = None,
    max_price: float | None = None,
    size: str | None = None,
    limit: int = 8,
) -> SearchResults:
    """Search the Campus Customs catalog to find products to recommend.

    Args:
        query: Keywords, e.g. "bulldog hoodie", "Berkeley", "baseball", "mom". Use "" to browse a category.
        category: One of Quarter-Zips, Jackets & Fleece, Hoodies, Crewnecks, Long Sleeve, T-Shirts.
        color: A color word to require, e.g. "navy", "gray", "white".
        max_price: Only items at or below this price in USD.
        size: Only items with stock in this size (XS, S, M, L, XL, XXL, or words like "medium").
        limit: Max results (1-12).

    Returns the best matches (price, colors, in-stock / sold-out sizes) plus total_matches,
    the number of matching products in the whole catalog. total_matches == 0 means nothing
    matches; say so honestly.
    """
    limit = max(1, min(limit, 12))
    matches = catalog.search_all(query, category, color, max_price, catalog.normalize_size(size))
    shown = [_summary(p) for p in matches[:limit]]
    return SearchResults(total_matches=len(matches), showing=len(shown), products=shown, more_available=len(matches) > len(shown))


def list_categories() -> list[dict]:
    """List the shop's product categories with how many styles each has, plus the price range."""
    out: dict[str, dict] = {}
    for p in catalog.load_products():
        c = out.setdefault(p["category"], {"category": p["category"], "styles": 0, "min_price": p["price"], "max_price": p["price"]})
        c["styles"] += 1
        c["min_price"] = min(c["min_price"], p["price"])
        c["max_price"] = max(c["max_price"], p["price"])
    return [out[n] for n in catalog.CATEGORY_NAMES if n in out]


# --- Product info, price, stock ------------------------------------------------------

CUSTOM_ORDER = "custom order, made in any size, ready for pickup at 57 Broadway or delivery in 2-3 weeks"


def _colorways(p: dict) -> tuple[str | None, list[str]]:
    """(color that's actually stocked, colors that are custom orders). Stock counts are for the stocked color only."""
    base = p.get("base_color")
    if not base:
        return None, []
    return base, [c for c in p["colors"] if c != base and c != "multicolor"]


def get_product_info(product: str) -> ProductInfo | ProductNotFound:
    """Everything about one product: description, colors, price, and stock for every size.

    Args:
        product: A product_id (e.g. "crew-left-chest-hoodie") or the product's name (e.g. "Crew Left Chest Hoodie").
    """
    p, candidates = catalog.resolve_product(product)
    if p is None:
        return _not_found(product, candidates)
    sizes = _sizes(p)
    return ProductInfo(
        product_id=p["product_id"],
        name=catalog.display_name(p["name"]),
        category=p["category"],
        garment_type=p["garment_type"],
        description=p["description"],
        colors=p["colors"],
        search_tags=p["search_tags"],
        price=p["price"],
        price_display=_money(p["price"]),
        sizes=sizes,
        in_stock_sizes=[s.size for s in sizes if s.quantity > 0],
        sold_out_sizes=[s.size for s in sizes if s.quantity <= 0],
        total_stock=sum(s.quantity for s in sizes),
        stocked_color=_colorways(p)[0],
        custom_order_colors=_colorways(p)[1],
    )


def get_price(product: str) -> PriceInfo | ProductNotFound:
    """The listed price of one product. Call this for any "how much is…" question.

    Args:
        product: A product_id or the product's name.
    """
    p, candidates = catalog.resolve_product(product)
    if p is None:
        return _not_found(product, candidates)
    return PriceInfo(product_id=p["product_id"], name=catalog.display_name(p["name"]), price=p["price"], price_display=_money(p["price"]))


def check_stock(product: str, size: str | None = None, color: str | None = None) -> StockReport | ProductNotFound:
    """How many of a product are in stock, for one size or all sizes, and whether a color is stocked or a custom order.
    Call this for any "is it in stock / do you have it in M / how many left / is the navy one available" question.

    Args:
        product: A product_id or the product's name.
        size: Optional size the shopper asked about: XS, S, M, L, XL, XXL (words like "medium" or "2XL" work).
        color: Optional color the shopper asked about (e.g. "navy").
    """
    p, candidates = catalog.resolve_product(product)
    if p is None:
        return _not_found(product, candidates)
    name = catalog.display_name(p["name"])
    sizes = _sizes(p)
    in_stock = [s.size for s in sizes if s.quantity > 0]
    sold_out = [s.size for s in sizes if s.quantity <= 0]
    total = sum(s.quantity for s in sizes)

    want = catalog.normalize_size(size)
    match = next((s for s in sizes if s.size == want), None) if want else None
    status = (match.status if match else "not_offered") if want else None

    others = ", ".join(f"{s.size} ({s.quantity})" for s in sizes if s.quantity > 0) or "none"
    if want is None:
        summary = f"{name}: {total} in stock across all sizes. In stock: {others}." + (f" SOLD OUT: {', '.join(sold_out)}." if sold_out else "")
    elif status == "not_offered":
        summary = f"{name} does not come in size {want}. Sizes in stock: {others}."
    elif status == "sold_out":
        summary = f"{name} is SOLD OUT in size {want} (0 left). Sizes still in stock: {others}."
    elif status == "low_stock":
        summary = f"{name} is in stock in size {want}, but only {match.quantity} left."
    else:
        summary = f"{name} is in stock in size {want}: {match.quantity} available."

    # Colors: stock counts are for the stocked color; the other colorways are custom orders (Part D).
    stocked, custom = _colorways(p)
    want_color = next((c for c in p["colors"] if color and (c.lower() in color.lower() or color.lower() in c.lower())), None)
    if color and stocked:
        if want_color and want_color in custom:
            summary = f"{name} in {want_color} is a {CUSTOM_ORDER}. (The stock counts are for the {stocked} version.)"
        elif want_color == stocked:
            summary += f" (Counts are for the {stocked} version, the color in stock.)"
        else:
            summary = f"{name} doesn't come in {color}. Colors: {', '.join(p['colors'])}. " + summary
    elif stocked and custom:
        summary += f" Counts are for {stocked}; {', '.join(custom)} = {CUSTOM_ORDER}."

    return StockReport(
        product_id=p["product_id"],
        name=name,
        price_display=_money(p["price"]),
        requested_size=want,
        requested_status=status,
        requested_quantity=match.quantity if match else None,
        sizes=sizes,
        in_stock_sizes=in_stock,
        sold_out_sizes=sold_out,
        total_stock=total,
        stocked_color=stocked,
        custom_order_colors=custom,
        requested_color=want_color or color,
        summary=summary,
    )


# --- Shopper & page context (Problem 8) -------------------------------------------


def my_account(ctx: RunContext[ShopDeps]) -> dict:
    """Who is chatting: the signed-in shopper's own name, email, member-since date, and whether
    they've chatted before. Guests get {"signed_in": false}. This is the ONLY customer
    information available; there is no way to look up any other customer."""
    c = ctx.deps.customer
    if c is None:
        return {"signed_in": False}
    return {"signed_in": True, **c.model_dump()}  # model_dump excludes user_id


def get_current_page(ctx: RunContext[ShopDeps]) -> dict:
    """What page the shopper is looking at right now. On a product page this includes the
    product's id, name, price, colors, and stock by size, so "this", "this one", or "it"
    can be resolved without asking."""
    page = ctx.deps.page
    if page is None:
        return {"known": False}
    out = {"known": True, **page.model_dump(exclude_none=True)}
    if page.product_id:
        info = get_product_info(page.product_id)
        if isinstance(info, ProductInfo):
            out["product"] = info.model_dump(include={"product_id", "name", "price_display", "colors", "description", "in_stock_sizes", "sold_out_sizes"})
    return out


# --- Custom Dan Gear (Problem 10 Part C) -------------------------------------------


def custom_gear_info(ctx: RunContext[ShopDeps]) -> dict:
    """Custom Dan Gear: the 7 blank products a shopper can put their own Handsome Dan image on
    (name, price, sizes), quantity discounts, and how many Dan images this shopper can still create
    today. Prices come from the shop's custom price list, not the apparel catalog."""
    c = ctx.deps.customer
    return {
        "products": [
            {"name": p["name"], "price_display": f"${p['price']:,.2f}", "sizes": p["sizes"], "color": p["color"], "about": p["blurb"]}
            for p in custom.CUSTOM_PRODUCTS
        ],
        "xxl_upcharge": f"+${custom.XXL_UPCHARGE:,.2f} on XXL apparel",
        "quantity_discounts": [f"{pct:.0%} off each when ordering {n}+" for n, pct in sorted(custom.QTY_BREAKS)],
        "design_page": "/custom",
        "creation_rules": f"Signed-in shoppers can create up to {custom.USER_DAILY_LIMIT} new Dan images per day. "
                          "Classic Dan designs from the shop are always free to use.",
        "allowance": custom.allowance(c.user_id if c else None),
        "saved_designs": f"Every Dan a shopper creates is saved in their account for {custom.RETENTION_DAYS} days, "
                         "so they can come back and put it on more gear. After that it's deleted.",
        "returns": "Custom items are made to order and can't be returned.",
    }


SHOP_TOOLS = [search_products, list_categories, get_product_info, get_price, check_stock, my_account, get_current_page, custom_gear_info]
