"""Reusable PepsiCo-styled branding helpers for the per-task summary workbooks.

Uses the user-supplied brand assets in ``docs/brands_icons/`` (official PepsiCo
logo + the multi-geo portfolio infographic) and generates lightweight, original
brand-colored icons for the per-brand rows.

DISCLAIMER
----------
Independent, illustrative learning / portfolio project. NOT affiliated with,
authorized by, or endorsed by PepsiCo, Inc. The generated brand-colored tiles
are ORIGINAL representations, not official product logos. The PepsiCo logo and
portfolio infographic are user-supplied assets used here for an internal,
client-styled mock deliverable. All trademarks belong to their respective owners.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.font_manager as fm
from PIL import Image as PILImage
from PIL import ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]

# ---- Asset locations ------------------------------------------------------
DOCS_ICONS = ROOT / "docs" / "brands_icons"  # raw, user-supplied source drops
RAW_LOGO = DOCS_ICONS / "PepsiCo_Icon.png"
RAW_INFOGRAPHIC = DOCS_ICONS / "Brands_Geos.png"

GEN_DIR = ROOT / "assets" / "brand" / "generated"
OFFICIAL_DIR = ROOT / "assets" / "brand" / "official"
LOGO_OFFICIAL = OFFICIAL_DIR / "pepsico_logo.png"  # committed copy of the logo
LOGO_SMALL = GEN_DIR / "pepsico_logo_small.png"  # downscaled, for title bars
INFOGRAPHIC = GEN_DIR / "brands_geos.jpg"  # downscaled JPEG, for the map sheet

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


# ---- Brand master data ----------------------------------------------------
# name -> (kind, hex_color, initials, text_color, emoji)
BRAND_INFO: dict[str, tuple[str, str, str, str, str]] = {
    # Foods (Frito-Lay / Quaker and local snack brands)
    "Lay's": ("Food", "FFD200", "L", "004B93", "\U0001f954"),
    "Walkers": ("Food", "E4002B", "W", "FFFFFF", "\U0001f954"),
    "Smith's": ("Food", "E8A33D", "S", "004B93", "\U0001f954"),
    "Doritos": ("Food", "D71920", "D", "FFFFFF", "\U0001f53a"),
    "Cheetos": ("Food", "F58025", "C", "FFFFFF", "\U0001f406"),
    "Ruffles": ("Food", "004B93", "R", "FFFFFF", "\U0001f954"),
    "Quaker": ("Food", "C8102E", "Q", "FFFFFF", "\U0001f963"),
    "Kurkure": ("Food", "E4002B", "K", "FFFFFF", "\U0001f336"),
    "Red Rock Deli": ("Food", "2B2B2B", "RRD", "FFFFFF", "\U0001f954"),
    # Beverages
    "Pepsi": ("Beverage", "004B93", "P", "FFFFFF", "\U0001f964"),
    "Pepsi Max": ("Beverage", "111111", "PM", "FFFFFF", "\U0001f964"),
    "7UP": ("Beverage", "0A8A3B", "7", "FFFFFF", "\U0001f964"),
    "Tropicana": ("Beverage", "F9A61A", "T", "FFFFFF", "\U0001f34a"),
    "Lipton": ("Beverage", "F6C700", "Li", "004B93", "\U0001f375"),
    "Solo": ("Beverage", "F2A900", "So", "004B93", "\U0001f34b"),
    "Mountain Dew": ("Beverage", "3FA535", "MD", "FFFFFF", "\U0001f3d4"),
    "Gatorade": ("Beverage", "F47920", "G", "FFFFFF", "⚡"),
    "Sobe": ("Beverage", "6CBE45", "Sb", "FFFFFF", "\U0001f98e"),
    "Sting": ("Beverage", "E4002B", "St", "FFFFFF", "⚡"),
    "Aquafina": ("Beverage", "00A9E0", "A", "FFFFFF", "\U0001f4a7"),
}

# ---- Geographies (from the user-supplied portfolio infographic) -----------
# name -> (flag_emoji, tagline, food_brands, beverage_brands)
GEOS: dict[str, tuple[str, str, list[str], list[str]]] = {
    "UK": (
        "\U0001f1ec\U0001f1e7",
        "Great tasting brands for British lifestyles.",
        ["Walkers", "Doritos", "Quaker", "Cheetos", "Ruffles"],
        ["Pepsi", "Pepsi Max", "7UP", "Tropicana", "Lipton"],
    ),
    "Australia": (
        "\U0001f1e6\U0001f1fa",
        "Iconic brands for an active, outdoor lifestyle.",
        ["Smith's", "Doritos", "Red Rock Deli", "Cheetos", "Quaker"],
        ["Pepsi", "Solo", "Mountain Dew", "Gatorade", "Sobe"],
    ),
    "India": (
        "\U0001f1ee\U0001f1f3",
        "Popular brands for every occasion.",
        ["Lay's", "Kurkure", "Doritos", "Quaker", "Cheetos"],
        ["Pepsi", "Mountain Dew", "7UP", "Tropicana", "Sting"],
    ),
    "Pakistan": (
        "\U0001f1f5\U0001f1f0",
        "Great taste, every day.",
        ["Lay's", "Kurkure", "Doritos", "Quaker", "Cheetos"],
        ["Pepsi", "7UP", "Mountain Dew", "Aquafina", "Sting"],
    ),
}


def markets_for(brand: str) -> list[str]:
    """Return the list of in-scope geographies that carry a given brand."""
    out = []
    for geo, (_flag, _tag, food, bev) in GEOS.items():
        if brand in food or brand in bev:
            out.append(geo)
    return out


def _slug(name: str) -> str:
    return name.lower().replace(" ", "").replace("'", "")


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
    fnt = _font(int(size * 0.40))
    bb = d.textbbox((0, 0), text, font=fnt)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.text(
        ((size - tw) / 2 - bb[0], (size - th) / 2 - bb[1]), text, font=fnt, fill=f"#{text_color}"
    )
    if out is not None:
        img.save(out)
    return img


def image_size(path: Path) -> tuple[int, int]:
    with PILImage.open(path) as im:
        return im.size


def _prepare_logo() -> None:
    """Commit a copy of the logo and build a small version for title bars."""
    OFFICIAL_DIR.mkdir(parents=True, exist_ok=True)
    GEN_DIR.mkdir(parents=True, exist_ok=True)
    if RAW_LOGO.exists():
        with PILImage.open(RAW_LOGO) as im:
            im = im.convert("RGBA")
            im.save(LOGO_OFFICIAL)
            small = im.copy()
            small.thumbnail((480, 72))
            small.save(LOGO_SMALL)
    elif LOGO_OFFICIAL.exists() and not LOGO_SMALL.exists():
        with PILImage.open(LOGO_OFFICIAL) as im:
            im = im.convert("RGBA")
            im.thumbnail((480, 72))
            im.save(LOGO_SMALL)


def _prepare_infographic() -> None:
    """Downscale + JPEG-compress the portfolio infographic (keeps the xlsx small)."""
    GEN_DIR.mkdir(parents=True, exist_ok=True)
    if RAW_INFOGRAPHIC.exists():
        with PILImage.open(RAW_INFOGRAPHIC) as im:
            im = im.convert("RGB")
            im.thumbnail((1100, 1100))
            im.save(INFOGRAPHIC, format="JPEG", quality=80, optimize=True)


def generate_all() -> dict[str, Path]:
    """(Re)build all assets and return a name -> path map used by the workbook."""
    GEN_DIR.mkdir(parents=True, exist_ok=True)
    for stale in list(GEN_DIR.glob("*.png")) + list(GEN_DIR.glob("*.jpg")):
        stale.unlink()  # clear stale assets from prior runs
    _prepare_logo()
    _prepare_infographic()

    paths: dict[str, Path] = {}
    if LOGO_SMALL.exists():
        paths["_logo"] = LOGO_SMALL
    if INFOGRAPHIC.exists():
        paths["_infographic"] = INFOGRAPHIC

    for name, (_kind, color, initials, tcolor, _emoji) in BRAND_INFO.items():
        p = GEN_DIR / f"{_slug(name)}.png"
        rounded_icon(color, initials, tcolor, out=p)
        paths[name] = p
    return paths


if __name__ == "__main__":
    made = generate_all()
    print(f"Generated {len(made)} assets in {GEN_DIR.relative_to(ROOT)}")
