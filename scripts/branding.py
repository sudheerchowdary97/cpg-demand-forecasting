"""Reusable PepsiCo-styled branding helpers for the per-task summary workbooks.

DISCLAIMER
----------
This is an INDEPENDENT, illustrative learning / portfolio project. It is NOT
affiliated with, authorized by, sponsored by, or endorsed by PepsiCo, Inc.
The brand names, colors, and icons produced here are STYLIZED, ORIGINAL
representations used only to mock a client-styled deliverable -- they are NOT
official PepsiCo logo assets. All trademarks (PepsiCo, Pepsi, Lay's, Doritos,
Gatorade, Tropicana, Quaker, Cheetos, Ruffles, Mountain Dew, 7UP, Aquafina,
Rockstar, etc.) are the property of their respective owners.

To use officially approved brand assets instead of the generated ones, drop PNGs
named ``<initials>.png`` into ``assets/brand/official/`` and set
``USE_OFFICIAL = True`` below.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.font_manager as fm
from PIL import Image as PILImage
from PIL import ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
GEN_DIR = ROOT / "assets" / "brand" / "generated"
OFFICIAL_DIR = ROOT / "assets" / "brand" / "official"
USE_OFFICIAL = False  # flip to True once approved assets exist in OFFICIAL_DIR

# ---- PepsiCo corporate palette (hex, no leading '#') ----------------------
PEPSI_BLUE = "004B93"
PEPSI_BLUE_DARK = "00307A"
PEPSI_BLUE_LIGHT = "1F6FBF"
PEPSI_RED = "EB1700"
WHITE = "FFFFFF"
DONE_GREEN = "E2EFDA"

_FONT_PATH = fm.findfont("DejaVu Sans")


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(_FONT_PATH, size)


# ---- Flagship PepsiCo brands ---------------------------------------------
# (display, category, hex_color, initials, text_color, emoji, forecasting_note)
BRANDS: list[tuple[str, str, str, str, str, str, str]] = [
    (
        "Pepsi",
        "Carbonated soft drinks",
        "004B93",
        "P",
        "FFFFFF",
        "\U0001f964",
        "Top-volume CSD; strong summer & holiday peaks, heavy promo lift.",
    ),
    (
        "Mountain Dew",
        "Carbonated soft drinks",
        "3FA535",
        "MD",
        "FFFFFF",
        "\U0001f3d4",
        "Youth-skewed CSD; limited-time flavors drive sharp launch spikes.",
    ),
    (
        "Gatorade",
        "Sports drinks",
        "F47920",
        "G",
        "FFFFFF",
        "⚡",
        "Sports/heat-driven; demand tracks temperature and sports seasons.",
    ),
    (
        "Tropicana",
        "Chilled juices",
        "F9A61A",
        "T",
        "FFFFFF",
        "\U0001f34a",
        "Chilled juice; short shelf life, breakfast + winter-cold seasonality.",
    ),
    (
        "Aquafina",
        "Bottled water",
        "00A9E0",
        "A",
        "FFFFFF",
        "\U0001f4a7",
        "Water; strong summer and heatwave sensitivity.",
    ),
    (
        "7UP",
        "Carbonated soft drinks",
        "0A8A3B",
        "7",
        "FFFFFF",
        "\U0001f964",
        "CSD; festive/holiday and mixer demand.",
    ),
    (
        "Lay's",
        "Salty snacks (Frito-Lay)",
        "FFD200",
        "L",
        "004B93",
        "\U0001f954",
        "DSD salty snack; freshness-critical, very high promo frequency.",
    ),
    (
        "Doritos",
        "Salty snacks (Frito-Lay)",
        "D71920",
        "D",
        "FFFFFF",
        "\U0001f53a",
        "Snack; big-game/event and limited-edition spikes.",
    ),
    (
        "Cheetos",
        "Salty snacks (Frito-Lay)",
        "F58025",
        "C",
        "FFFFFF",
        "\U0001f406",
        "Snack; steady base with promo-driven lift.",
    ),
    (
        "Ruffles",
        "Salty snacks (Frito-Lay)",
        "E4002B",
        "R",
        "FFFFFF",
        "\U0001f954",
        "Snack; party/occasion and promo sensitive.",
    ),
    (
        "Quaker",
        "Foods / oats",
        "C8102E",
        "Q",
        "FFFFFF",
        "\U0001f963",
        "Ambient breakfast; longer shelf life, winter skew.",
    ),
    (
        "Rockstar",
        "Energy drinks",
        "1A1A1A",
        "RS",
        "FFD200",
        "⚡",
        "Energy; convenience-channel, weekday skew.",
    ),
]


def rounded_icon(
    hex_color: str,
    text: str,
    text_color: str = "FFFFFF",
    size: int = 72,
    radius: int = 16,
    out: Path | None = None,
) -> PILImage.Image:
    """A rounded, brand-colored tile with the brand's initials (original art)."""
    img = PILImage.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([1, 1, size - 2, size - 2], radius=radius, fill=f"#{hex_color}")
    fnt = _font(int(size * 0.42))
    bb = d.textbbox((0, 0), text, font=fnt)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.text(
        ((size - tw) / 2 - bb[0], (size - th) / 2 - bb[1]), text, font=fnt, fill=f"#{text_color}"
    )
    if out is not None:
        img.save(out)
    return img


def brand_roundel(size: int = 72, out: Path | None = None) -> PILImage.Image:
    """A stylized red/white/blue tricolor roundel accent (original, generic)."""
    img = PILImage.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    box = [1, 1, size - 2, size - 2]
    d.pieslice(box, 180, 360, fill=f"#{PEPSI_RED}")  # top half
    d.pieslice(box, 0, 180, fill=f"#{PEPSI_BLUE}")  # bottom half
    d.rectangle([1, int(size * 0.40), size - 2, int(size * 0.60)], fill=f"#{WHITE}")
    d.ellipse(box, outline=f"#{PEPSI_BLUE_DARK}", width=2)
    if out is not None:
        img.save(out)
    return img


def generate_all() -> dict[str, Path]:
    """Regenerate every icon on disk and return a name -> path map."""
    GEN_DIR.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    roundel_path = GEN_DIR / "roundel.png"
    brand_roundel(out=roundel_path)
    paths["_roundel"] = roundel_path

    for name, _cat, color, initials, tcolor, _emoji, _note in BRANDS:
        official = OFFICIAL_DIR / f"{initials.lower()}.png"
        if USE_OFFICIAL and official.exists():
            paths[name] = official
            continue
        slug = name.lower().replace(" ", "").replace("'", "")
        p = GEN_DIR / f"{slug}.png"
        rounded_icon(color, initials, tcolor, out=p)
        paths[name] = p
    return paths


if __name__ == "__main__":
    made = generate_all()
    print(f"Generated {len(made)} brand assets in {GEN_DIR.relative_to(ROOT)}")
