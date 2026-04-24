"""
Regenerate the favicons so Google's circle crop doesn't leave a white square border.

- public/favicon.png (512x512) is a circular cut of the logo on a transparent
  background, with a small margin of transparency so Google's circle crop
  (which is slightly inside the square bounds) never cuts into content.
- public/apple-touch-icon.png (180x180) is a full-bleed square — iOS rounds
  the corners itself when it's added to the home screen.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "public" / "favicon.png.jpg"
OUT_FAVICON = ROOT / "public" / "favicon.png"
OUT_APPLE = ROOT / "public" / "apple-touch-icon.png"

# Work from the 1200x896 source at high resolution, then downsample.
src = Image.open(SRC).convert("RGBA")
w, h = src.size
side = min(w, h)
# Centre-crop to a square.
left = (w - side) // 2
top = (h - side) // 2
square = src.crop((left, top, left + side, top + side))

def make_circular(base: Image.Image, canvas_size: int, content_ratio: float = 0.94) -> Image.Image:
    """Place `base` centred on a transparent canvas and clip to a circle.

    content_ratio controls how much of the canvas the circle fills — leaving
    a few transparent pixels outside so Google's circle crop never eats the
    edge of the logo.
    """
    content_px = int(canvas_size * content_ratio)
    resized = base.resize((content_px, content_px), Image.LANCZOS)

    canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    offset = (canvas_size - content_px) // 2
    canvas.paste(resized, (offset, offset))

    # Build a circular alpha mask at the content size and composite it over the canvas.
    mask = Image.new("L", (canvas_size, canvas_size), 0)
    ImageDraw.Draw(mask).ellipse(
        (offset, offset, offset + content_px, offset + content_px), fill=255
    )
    # Apply the mask as the alpha channel so everything outside the circle is transparent.
    canvas.putalpha(mask)
    return canvas


def make_square(base: Image.Image, canvas_size: int) -> Image.Image:
    """Full-bleed square — iOS will round the corners itself."""
    return base.resize((canvas_size, canvas_size), Image.LANCZOS)


favicon = make_circular(square, 512)
favicon.save(OUT_FAVICON, "PNG", optimize=True)
print(f"wrote {OUT_FAVICON} ({favicon.size} {favicon.mode})")

apple = make_square(square, 180)
apple.save(OUT_APPLE, "PNG", optimize=True)
print(f"wrote {OUT_APPLE} ({apple.size} {apple.mode})")
