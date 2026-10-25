"""Match DB players to Sports.ru roster entries."""

from __future__ import annotations

import unicodedata

from .parser import SportsRuPlayer

_MATCH_THRESHOLD = 62


def _normalize_slug(slug: str) -> str:
    text = unicodedata.normalize("NFKD", slug)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.lower().strip()


def _slug_tokens(slug: str) -> list[str]:
    return [t for t in _normalize_slug(slug).split("-") if t and t.isalpha()]


def match_score(transfermarkt_slug: str, sports_slug: str) -> int:
    if not transfermarkt_slug or not sports_slug:
        return 0
    if sports_slug.isdigit():
        return 0
    tm = _normalize_slug(transfermarkt_slug)
    sp = _normalize_slug(sports_slug)
    if tm == sp:
        return 100
    if sp.startswith(tm + "-") or tm.startswith(sp + "-"):
        return 88
    tm_tokens = _slug_tokens(tm)
    sp_tokens = _slug_tokens(sp)
    if not tm_tokens or not sp_tokens:
        return 0
    if tm_tokens[-1] == sp_tokens[-1] and len(tm_tokens[-1]) >= 4:
        return 78
    overlap = set(tm_tokens) & set(sp_tokens)
    if len(overlap) >= 2:
        return 70 + min(10, len(overlap) * 3)
    if len(overlap) == 1 and len(next(iter(overlap))) >= 5:
        return 65
    return 0


def match_player_to_sports_ru(
    transfermarkt_slug: str,
    roster: list[SportsRuPlayer],
    *,
    used_slugs: set[str],
) -> SportsRuPlayer | None:
    best: SportsRuPlayer | None = None
    best_score = 0
    for athlete in roster:
        if athlete.slug in used_slugs:
            continue
        score = match_score(transfermarkt_slug, athlete.slug)
        if score > best_score:
            best_score = score
            best = athlete
    if best is None or best_score < _MATCH_THRESHOLD:
        return None
    return best
