"""Exact-shield compositing: paste the user-supplied shield (original artwork) onto a generated image
at a user-chosen position/scale/rotation so it reads as part of the garment. Produces a NEW version;
the generated image is never modified in place.

- occlusion: the shield is only drawn where the underlying pixels look like garment fabric. Warm-colored
  things in front of the garment (a pumpkin, a red neckerchief, Dan's brown fur) stay in front of it.
- fabric: the garment's own knit texture and shading are blended into the shield so it looks woven /
  printed onto the sweater instead of stuck on top. The shield's colors and charges are not redrawn.
"""

import io

from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageStat


def _garment_mask(region: Image.Image) -> Image.Image:
    """255 where the base looks like garment fabric, 0 for vivid warm foreground objects
    (orange pumpkin, red neckerchief, tan/brown fur). Low-saturation beige (e.g. the old AI-drawn
    patch outline) counts as garment, so it gets covered rather than showing through."""
    h, s, v = region.convert("RGB").convert("HSV").split()
    warm_hue = h.point(lambda x: 255 if (x <= 40 or x >= 235) else 0)   # reds → oranges → tans
    vivid = s.point(lambda x: 255 if x > 105 else 0)
    lit = v.point(lambda x: 255 if x > 70 else 0)
    fg = ImageChops.multiply(ImageChops.multiply(warm_hue, vivid), lit)
    # Only LARGE warm shapes are foreground (pumpkin, neckerchief, fur). Small specks (e.g. red tongues of
    # an old drawn patch underneath) are removed with a morphological opening so they don't poke through.
    k = max(5, (min(region.size) // 14) | 1)
    fg = fg.filter(ImageFilter.MinFilter(k)).filter(ImageFilter.MaxFilter(k))
    mask = ImageChops.invert(fg)
    # close knit-texture speckle, then soften so occlusion boundaries look natural
    mask = mask.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(3))
    return mask.filter(ImageFilter.GaussianBlur(1.2))


def _texture_source(base: Image.Image, box, size) -> Image.Image | None:
    """Find a nearby same-size patch of plain garment (most fabric, least detail) to borrow knit texture from."""
    W, H = base.size
    x0, y0, x1, y1 = box
    w, h = size
    best, best_score = None, -1e9
    for dx, dy in ((-w, 0), (w, 0), (0, h), (-w, h // 2), (w, h // 2), (0, -h)):
        bx, by = x0 + dx, y0 + dy
        if bx < 0 or by < 0 or bx + w > W or by + h > H:
            continue
        cand = base.crop((bx, by, bx + w, by + h)).convert("RGB")
        garment = ImageStat.Stat(_garment_mask(cand)).mean[0] / 255
        lum = cand.convert("L")
        detail = ImageStat.Stat(ImageChops.difference(lum, lum.filter(ImageFilter.GaussianBlur(6)))).mean[0]
        score = garment * 100 - detail
        if score > best_score:
            best, best_score = cand, score
    return best


def composite_shield(base_png: bytes, shield_path, cx: float, cy: float, width_frac: float,
                     rotation: float = 0.0, opacity: float = 0.97, shade: float = 0.92,
                     occlusion: bool = True, fabric: float = 0.85) -> bytes:
    base = Image.open(io.BytesIO(base_png)).convert("RGBA")
    W, H = base.size
    shield = Image.open(shield_path).convert("RGBA")
    target_w = max(8, int(W * width_frac))
    scale = target_w / shield.width
    shield = shield.resize((target_w, max(8, int(shield.height * scale))), Image.LANCZOS)
    if rotation:
        shield = shield.rotate(rotation, resample=Image.BICUBIC, expand=True)
    x = int(cx * W - shield.width / 2)
    y = int(cy * H - shield.height / 2)
    box = (x, y, x + shield.width, y + shield.height)
    region = base.crop(box).convert("RGB")

    rgb = ImageEnhance.Brightness(shield.convert("RGB")).enhance(shade)
    alpha = shield.getchannel("A").point(lambda a: int(a * opacity))

    if fabric > 0:
        # Knit texture is sampled from PLAIN garment next to the shield (not from under it, where an
        # old drawn patch would ghost through), then overlaid onto the artwork at low amplitude.
        src = _texture_source(base, box, shield.size) or region
        lum = src.convert("L")
        low = lum.filter(ImageFilter.GaussianBlur(3))
        hp = ImageChops.subtract(lum, low, scale=1.0, offset=128).point(lambda v: max(110, min(146, v)))  # clamp: texture only
        tex = Image.merge("RGB", (hp, hp, hp))
        rgb = Image.blend(rgb, ImageChops.overlay(rgb, tex), min(1.0, fabric))
        # Match scene lighting: tint toward the image's average color, and darken toward the garment's tone.
        avg = ImageStat.Stat(base.convert("RGB").resize((64, 64))).mean
        m = max(avg) or 1
        tint = tuple(0.80 + 0.20 * c / m for c in avg)
        rgb = Image.merge("RGB", [ch.point(lambda v, t=t: int(v * t)) for ch, t in zip(rgb.split(), tint)])
        rgb = ImageEnhance.Brightness(rgb).enhance(1 - 0.12 * fabric)

    if occlusion:
        alpha = ImageChops.multiply(alpha, _garment_mask(region))

    layer = Image.merge("RGBA", (*rgb.split(), alpha))
    # Soft contact shadow so it reads as printed/sewn on, not floating (also respects occlusion).
    shadow = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    shadow.putalpha(alpha.point(lambda a: int(a * 0.18)).filter(ImageFilter.GaussianBlur(max(1, target_w // 70))))
    base.alpha_composite(shadow, (max(0, x + 1), max(0, y + 2)))
    base.alpha_composite(layer, (max(0, x), max(0, y)))
    out = io.BytesIO()
    base.convert("RGB").save(out, "PNG")
    return out.getvalue()
