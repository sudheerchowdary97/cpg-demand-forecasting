"""Package-local master data for the synthetic generator.

Mirrors scripts/branding.py (which carries colors/icons for docs), but kept
inside the package so data generation has no dependency on the docs tooling.
Hierarchy: market -> channel -> retailer -> store; brands split Food / Beverage.
"""

from __future__ import annotations

# market -> {"Food": [...], "Beverage": [...]}
GEOS: dict[str, dict[str, list[str]]] = {
    "UK": {
        "Food": ["Walkers", "Doritos", "Quaker", "Cheetos", "Ruffles"],
        "Beverage": ["Pepsi", "Pepsi Max", "7UP", "Tropicana", "Lipton"],
    },
    "Australia": {
        "Food": ["Smith's", "Doritos", "Red Rock Deli", "Cheetos", "Quaker"],
        "Beverage": ["Pepsi", "Solo", "Mountain Dew", "Gatorade", "Sobe"],
    },
    "India": {
        "Food": ["Lay's", "Kurkure", "Doritos", "Quaker", "Cheetos"],
        "Beverage": ["Pepsi", "Mountain Dew", "7UP", "Tropicana", "Sting"],
    },
    "Pakistan": {
        "Food": ["Lay's", "Kurkure", "Doritos", "Quaker", "Cheetos"],
        "Beverage": ["Pepsi", "7UP", "Mountain Dew", "Aquafina", "Sting"],
    },
}

# market -> list of (channel, [retailers/banners], store_weight)
MARKET_CHANNELS: dict[str, list[tuple[str, list[str], int]]] = {
    "India": [
        ("Traditional / General Trade", ["Kirana Store", "Paan Shop"], 6),
        ("Modern Trade — Hypermarket", ["Reliance Smart Bazaar", "DMart", "Lulu Hypermarket"], 2),
        (
            "Modern Trade — Supermarket",
            ["More Retail", "Spencer's Retail", "Ratnadeep", "Triveni", "Reliance Fresh", "V-Mart"],
            2,
        ),
        ("E-commerce", ["Amazon", "Flipkart", "JioMart"], 1),
        ("Q-commerce", ["Blinkit", "Zepto", "Swiggy Instamart", "BigBasket"], 1),
        ("Wholesale / Cash & Carry", ["Metro C&C", "Udaan"], 1),
    ],
    "Pakistan": [
        ("Traditional / General Trade", ["Kiryana Store", "General Store"], 6),
        ("Modern Trade — Hypermarket", ["Carrefour", "Imtiaz", "Metro/Makro"], 2),
        ("Modern Trade — Supermarket", ["Al-Fatah", "Naheed", "Chase Up", "Green Valley"], 2),
        ("E-commerce", ["Daraz"], 1),
        ("Q-commerce", ["Bazaar", "GrocerApp"], 1),
    ],
    "UK": [
        (
            "Modern Trade — Supermarket",
            ["Tesco", "Sainsbury's", "ASDA", "Morrisons", "Waitrose"],
            5,
        ),
        ("Discounters", ["Aldi", "Lidl"], 2),
        ("Convenience", ["Co-op", "One Stop", "Tesco Express"], 2),
        ("E-commerce", ["Ocado", "Amazon Fresh"], 1),
        ("Wholesale / Cash & Carry", ["Booker", "Bestway"], 1),
    ],
    "Australia": [
        ("Modern Trade — Supermarket", ["Woolworths", "Coles"], 5),
        ("Discounters", ["ALDI"], 2),
        ("Independents / Convenience", ["IGA", "7-Eleven"], 2),
        ("Warehouse Club", ["Costco"], 1),
        ("E-commerce", ["Woolworths Online", "Amazon AU"], 1),
    ],
}

# Relative per-store daily volume by channel (GT = many small stores; MT/wholesale bigger).
CHANNEL_VOL: dict[str, float] = {
    "Traditional / General Trade": 0.5,
    "Modern Trade — Hypermarket": 2.6,
    "Modern Trade — Supermarket": 1.7,
    "Discounters": 1.4,
    "Convenience": 0.7,
    "Independents / Convenience": 0.7,
    "Warehouse Club": 3.0,
    "E-commerce": 1.2,
    "Q-commerce": 0.9,
    "Wholesale / Cash & Carry": 3.4,
}

# Pack sizes per category, with a relative volume factor and base price.
PACKS: dict[str, list[tuple[str, float, float]]] = {
    "Beverage": [
        ("330ml Can", 1.0, 40),
        ("500ml PET", 0.8, 60),
        ("1.5L PET", 0.6, 90),
        ("2L PET", 0.5, 110),
    ],
    "Food": [("45g", 1.0, 20), ("75g", 0.8, 35), ("150g", 0.6, 60), ("200g", 0.5, 80)],
}

# Relative market size (drives base volume).
MARKET_SCALE: dict[str, float] = {"UK": 1.0, "Australia": 0.7, "India": 2.4, "Pakistan": 1.3}
