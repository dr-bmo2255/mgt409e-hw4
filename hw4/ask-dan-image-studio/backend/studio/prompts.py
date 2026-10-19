"""Prompt construction: identity block + per-asset scene + exact permitted text + negatives + feedback."""

IDENTITY = (
    "SUBJECT: Handsome Dan, Yale University's mascot: a friendly, stocky BROWN-AND-WHITE ENGLISH BULLDOG. "
    "Match the dog in the reference photos exactly: same brown-and-white coat distribution, broad face, heavy jowls, "
    "deep facial wrinkles, underbite, expressive dark eyes, short muzzle and stocky, low body. He is a real dog, "
    "never a human, a costume, a cartoon or a different breed. Photorealistic editorial photography, realistic fur, "
    "natural lighting, shallow depth of field. Dan is the clear hero and fills much of the frame."
)

NEGATIVES = (
    "AVOID: collages, split panels, borders, captions, watermarks, signatures, gibberish or invented text, fake book titles, "
    "misspellings, extra or missing limbs, extra tails, human hands on Dan, distorted paws, implausible or broken sports "
    "equipment, invented crests or logos, any heraldry not supplied, the words 'Dan' added to any school, college or team "
    "name, and the generic 'autumn Gothic steps with books, tote bag, mug and laptop' composition."
)


def build_prompt(asset: dict, feedback: str | None = None, has_shield: bool = False, is_revision: bool = False,
                 override: str | None = None) -> str:
    words = asset.get("permitted_text") or []
    text_rule = ("EXACT TEXT: the only readable words allowed anywhere in the image are: "
                 + ", ".join(f'"{w}"' for w in words) + ". Spell them exactly; no other words." if words
                 else "EXACT TEXT: no readable words.")
    shield_rule = ""
    if asset.get("shield_slug"):
        shield_rule = (
            "SHIELD: the last reference image is the OFFICIAL shield. If a shield appears on clothing, it must be a faithful copy "
            "of that supplied image (same shape, colors and charges). If you cannot reproduce it exactly, leave a clean, "
            "flat, well-lit patch area on the chest instead of inventing one; the real shield will be composited afterwards."
            if has_shield else
            "SHIELD: no official shield was supplied for this school; do not draw any crest or heraldry."
        )
    scene = override or (
        f"SCENE ({asset['display_name']}): setting: {asset['setting']}. Outfit: {asset['outfit']}. "
        f"Pose/action: {asset['pose']}. Humor: {asset['humor']}."
    )
    parts = [IDENTITY, scene, text_rule, shield_rule, NEGATIVES,
             "FORMAT: one single square image, one continuous scene."]
    if is_revision:
        parts.insert(1, "REVISION: the FIRST reference image is the current draft. Keep everything that works in it and change only what the feedback asks.")
    if feedback:
        parts.append(f"REVIEWER FEEDBACK TO APPLY: {feedback}")
    return "\n\n".join(p for p in parts if p)
