"""Free mock provider: builds a labeled placeholder PNG from the real references, so the whole
review / revise / approve / export flow can be exercised with zero API spend."""

import io
import textwrap

from PIL import Image, ImageDraw, ImageFilter, ImageOps

from .base import GenRequest, GenResult, Provider


class MockProvider(Provider):
    name = "mock"
    paid = False

    def generate(self, req: GenRequest) -> GenResult:
        w, h = (int(x) for x in req.size.split("x"))
        canvas = Image.new("RGB", (w, h), (0, 53, 107))  # Yale blue #00356B
        dan = next((p for p in req.references if "shields" not in str(p)), None)
        if dan:
            im = ImageOps.fit(Image.open(dan).convert("RGB"), (w, h))
            canvas = Image.blend(im.filter(ImageFilter.GaussianBlur(2)), canvas, 0.35)
        shield = next((p for p in req.references if "shields" in str(p)), None)
        if shield:
            s = Image.open(shield).convert("RGBA")
            s.thumbnail((w // 5, h // 5))
            canvas.paste(s, (w - s.width - w // 20, h // 20), s)
        d = ImageDraw.Draw(canvas)
        band = Image.new("RGBA", (w, h // 3), (0, 0, 0, 170))
        canvas.paste(band, (0, h - h // 3), band)
        size = max(18, w // 40)
        lines = [f"MOCK IMAGE  ·  {req.asset_id}", "(no API call, no cost)"] + textwrap.wrap((req.prompt[req.prompt.find("SCENE"):] if "SCENE" in req.prompt else req.prompt)[:260], 70)[:5]
        y = h - h // 3 + size
        for i, line in enumerate(lines):
            d.text((w // 30, y), line, fill=(255, 255, 255) if i else (255, 214, 0), font_size=size if i else int(size * 1.3))
            y += int(size * 1.5)
        buf = io.BytesIO()
        canvas.save(buf, "PNG")
        return GenResult(png_bytes=buf.getvalue(), cost_usd=0.0, cost_is_estimate=False, usage={}, model="mock")
