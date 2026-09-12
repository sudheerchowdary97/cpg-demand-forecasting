"""Per-market holiday / festival calendars (approximate, for synthetic data).

Dates are illustrative for 2022-2024 and intentionally approximate — festivals
like Diwali and Eid move each year. Each entry carries a demand-lift multiplier
so the generator can inject market-specific peaks the model must learn.
"""

from __future__ import annotations

import datetime as dt

# market -> list of (ISO date, name, demand-lift multiplier)
_HOLIDAYS: dict[str, list[tuple[str, str, float]]] = {
    "UK": [
        ("2022-12-25", "Christmas", 1.6),
        ("2023-12-25", "Christmas", 1.6),
        ("2024-12-25", "Christmas", 1.6),
        ("2022-12-31", "New Year", 1.4),
        ("2023-12-31", "New Year", 1.4),
        ("2024-12-31", "New Year", 1.4),
        ("2022-04-17", "Easter", 1.3),
        ("2023-04-09", "Easter", 1.3),
        ("2024-03-31", "Easter", 1.3),
        ("2023-05-01", "Bank Holiday", 1.15),
        ("2024-05-06", "Bank Holiday", 1.15),
    ],
    "Australia": [
        ("2022-12-25", "Christmas", 1.6),
        ("2023-12-25", "Christmas", 1.6),
        ("2024-12-25", "Christmas", 1.6),
        ("2022-01-26", "Australia Day", 1.4),
        ("2023-01-26", "Australia Day", 1.4),
        ("2024-01-26", "Australia Day", 1.4),
        ("2022-04-25", "ANZAC Day", 1.2),
        ("2023-04-25", "ANZAC Day", 1.2),
        ("2024-04-25", "ANZAC Day", 1.2),
    ],
    "India": [
        ("2022-10-24", "Diwali", 1.9),
        ("2023-11-12", "Diwali", 1.9),
        ("2024-11-01", "Diwali", 1.9),
        ("2022-03-18", "Holi", 1.4),
        ("2023-03-08", "Holi", 1.4),
        ("2024-03-25", "Holi", 1.4),
        ("2022-08-15", "Independence Day", 1.3),
        ("2023-08-15", "Independence Day", 1.3),
        ("2024-08-15", "Independence Day", 1.3),
    ],
    "Pakistan": [
        ("2022-05-02", "Eid al-Fitr", 1.9),
        ("2023-04-22", "Eid al-Fitr", 1.9),
        ("2024-04-10", "Eid al-Fitr", 1.9),
        ("2022-07-10", "Eid al-Adha", 1.7),
        ("2023-06-29", "Eid al-Adha", 1.7),
        ("2024-06-17", "Eid al-Adha", 1.7),
        ("2022-08-14", "Independence Day", 1.3),
        ("2023-08-14", "Independence Day", 1.3),
        ("2024-08-14", "Independence Day", 1.3),
    ],
}


def holiday_map(market: str) -> dict[dt.date, tuple[str, float]]:
    """Return {date: (name, lift)} for a market."""
    out: dict[dt.date, tuple[str, float]] = {}
    for iso, name, lift in _HOLIDAYS.get(market, []):
        out[dt.date.fromisoformat(iso)] = (name, lift)
    return out


def is_southern_hemisphere(market: str) -> bool:
    """Australia's seasons are flipped vs the northern-hemisphere markets."""
    return market == "Australia"
