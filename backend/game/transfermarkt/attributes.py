"""FIFA-style attribute heuristics from TM position, age, and market value."""

from __future__ import annotations

import math
import random
from typing import TypedDict

from game.models import Position

EUR_TO_USD_RATE = 1.08

# Position group weights for overall (must sum to 1.0).
_OVR_WEIGHTS: dict[str, dict[str, float]] = {
    Position.GK: {
        "pac": 0.05,
        "sho": 0.02,
        "pas": 0.12,
        "dri": 0.05,
        "defending": 0.28,
        "phy": 0.18,
        "aerial": 0.12,
        "mentality": 0.10,
        "injury_resistance": 0.08,
    },
    Position.DEF: {
        "pac": 0.12,
        "sho": 0.04,
        "pas": 0.10,
        "dri": 0.08,
        "defending": 0.26,
        "phy": 0.16,
        "aerial": 0.14,
        "mentality": 0.06,
        "injury_resistance": 0.04,
    },
    Position.MID: {
        "pac": 0.14,
        "sho": 0.12,
        "pas": 0.22,
        "dri": 0.18,
        "defending": 0.10,
        "phy": 0.10,
        "aerial": 0.04,
        "mentality": 0.06,
        "injury_resistance": 0.04,
    },
    Position.FWD: {
        "pac": 0.18,
        "sho": 0.24,
        "pas": 0.12,
        "dri": 0.18,
        "defending": 0.04,
        "phy": 0.12,
        "aerial": 0.04,
        "mentality": 0.04,
        "injury_resistance": 0.04,
    },
}


class PlayerAttributes(TypedDict):
    pac: int
    sho: int
    pas: int
    dri: int
    defending: int
    phy: int
    aerial: int
    mentality: int
    injury_resistance: int
    overall: int


def parse_market_value_eur(raw: str) -> int:
    """Parse TM market value strings like '€30.00m', '€500k', '€-', '-'."""
    raw = raw.strip().replace("\xa0", " ")
    if not raw or raw in {"-", "€-"}:
        return 0
    raw = raw.replace("€", "").strip().lower()
    multiplier = 1
    if raw.endswith("m"):
        multiplier = 1_000_000
        raw = raw[:-1]
    elif raw.endswith("k"):
        multiplier = 1_000
        raw = raw[:-1]
    try:
        value = float(raw)
    except ValueError:
        return 0
    return int(value * multiplier)


def market_value_to_usd(eur: int, rate: float = EUR_TO_USD_RATE) -> int:
    return int(eur * rate)


def tm_position_to_game_position(tm_position: str) -> str:
    pos = tm_position.strip().lower()
    if "goalkeeper" in pos or pos == "gk":
        return Position.GK
    if any(
        x in pos
        for x in (
            "back",
            "centre-back",
            "center-back",
            "defender",
        )
    ):
        return Position.DEF
    if any(
        x in pos
        for x in (
            "forward",
            "winger",
            "striker",
        )
    ):
        return Position.FWD
    return Position.MID


def _base_rating_from_value(eur: int) -> float:
    """Log-scale 40–91 from market value (EUR)."""
    if eur <= 0:
        return 58.0
    # ln(1M) ~ 13.8, ln(100k) ~ 11.5
    ln = math.log(max(eur, 50_000))
    rating = 32 + ln * 3.35
    return max(40.0, min(91.0, rating))


def _age_pace_modifier(age: int) -> float:
    if age <= 21:
        return 4.0
    if age <= 24:
        return 2.0
    if age <= 28:
        return 0.0
    if age <= 32:
        return -3.0
    return -6.0


def _age_physical_modifier(age: int) -> float:
    if age < 22:
        return -1.0
    if age <= 29:
        return 1.0
    if age <= 33:
        return 0.0
    return -2.0


def compute_player_attributes(
    tm_position: str,
    age: int,
    market_value_eur: int,
    *,
    seed: int | None = None,
) -> PlayerAttributes:
    """
    Derive FIFA-style stats from TM metadata.

    Formula (see docs/transfermarkt-import.md):
    - base = log market value → ~40–91
    - position templates add/subtract per stat; small deterministic jitter from seed
    """
    game_pos = tm_position_to_game_position(tm_position)
    base = _base_rating_from_value(market_value_eur)
    rng = random.Random(seed)

    def stat(center: float, spread: float = 4.0) -> int:
        val = center + rng.uniform(-spread, spread)
        return int(max(1, min(99, round(val))))

    pace = base + _age_pace_modifier(age)
    phy = base + _age_physical_modifier(age)
    aerial = base + (3 if game_pos == Position.DEF else 0)
    mentality = base + rng.uniform(-2, 4)
    injury = base + rng.uniform(-3, 3) + (2 if age < 24 else 0)

    if game_pos == Position.GK:
        attrs = {
            "pac": stat(pace - 8),
            "sho": stat(base - 25),
            "pas": stat(base - 2),
            "dri": stat(base - 10),
            "defending": stat(base + 6),
            "phy": stat(phy),
            "aerial": stat(aerial + 4),
            "mentality": stat(mentality + 2),
            "injury_resistance": stat(injury),
        }
    elif game_pos == Position.DEF:
        attrs = {
            "pac": stat(pace - 2),
            "sho": stat(base - 8),
            "pas": stat(base - 2),
            "dri": stat(base - 4),
            "defending": stat(base + 5),
            "phy": stat(phy + 2),
            "aerial": stat(aerial + 4),
            "mentality": stat(mentality),
            "injury_resistance": stat(injury),
        }
    elif game_pos == Position.MID:
        attrs = {
            "pac": stat(pace),
            "sho": stat(base),
            "pas": stat(base + 4),
            "dri": stat(base + 2),
            "defending": stat(base - 4),
            "phy": stat(phy),
            "aerial": stat(aerial - 2),
            "mentality": stat(mentality + 1),
            "injury_resistance": stat(injury),
        }
    else:
        attrs = {
            "pac": stat(pace + 3),
            "sho": stat(base + 5),
            "pas": stat(base),
            "dri": stat(base + 3),
            "defending": stat(base - 10),
            "phy": stat(phy + 1),
            "aerial": stat(aerial),
            "mentality": stat(mentality),
            "injury_resistance": stat(injury),
        }

    attrs["overall"] = overall_from_stats(game_pos, attrs)
    return PlayerAttributes(**attrs)


def overall_from_stats(game_position: str, attrs: PlayerAttributes) -> int:
    weights = _OVR_WEIGHTS.get(game_position, _OVR_WEIGHTS[Position.MID])
    overall_f = sum(attrs[k] * weights[k] for k in weights)
    return int(max(1, min(99, round(overall_f))))
