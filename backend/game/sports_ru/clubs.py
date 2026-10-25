"""Map local crest slugs → Sports.ru club URL segments."""

from __future__ import annotations

CREST_SLUG_TO_SPORTS_RU: dict[str, str] = {
    "arsenal": "arsenal",
    "aston-villa": "aston-villa",
    "afc-bournemouth": "bournemouth",
    "brentford": "brentford",
    "brighton": "brighton",
    "chelsea": "chelsea",
    "coventry-city": "coventry-city-fc",
    "crystal-palace": "crystal-palace",
    "everton": "everton",
    "fulham": "fulham",
    "hull-city": "hull",
    "ipswich-town": "ipswich-town",
    "leeds-united": "leeds",
    "liverpool": "liverpool",
    "manchester-city": "manchester-city",
    "manchester-united": "mu",
    "newcastle-united": "newcastle",
    "nottingham-forest": "nottingham-forest",
    "sunderland": "sunderland",
    "tottenham-hotspur": "tottenham",
}


def sports_club_slug_from_crest_url(crest_url: str) -> str | None:
    if "/crests/clubs/" not in crest_url:
        return None
    crest_slug = crest_url.rsplit("/", 1)[-1].removesuffix(".png")
    return CREST_SLUG_TO_SPORTS_RU.get(crest_slug)
