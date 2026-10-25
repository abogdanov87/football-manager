"""Parse FC Ratings player pages (FC 27 face stats)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

@dataclass(frozen=True)
class FcIndexEntry:
    name: str
    club_label: str
    url: str
    overall: int
    slug: str


@dataclass(frozen=True)
class FcFaceStats:
    pac: int
    sho: int
    pas: int
    dri: int
    defending: int
    phy: int
    aerial: int
    overall: int


def slug_from_fc_url(url: str) -> str:
    path = urlparse(url).path.strip("/")
    m = re.match(r"(.+)-(\d+)$", path)
    return m.group(1) if m else ""


def parse_search_index(raw_json: str) -> dict[str, FcIndexEntry]:
    data: list[dict[str, Any]] = json.loads(raw_json)
    by_slug: dict[str, FcIndexEntry] = {}
    for item in data:
        if item.get("t") != "player":
            continue
        url = str(item.get("u") or "")
        slug = slug_from_fc_url(url)
        if not slug:
            continue
        by_slug[slug] = FcIndexEntry(
            name=str(item.get("n") or ""),
            club_label=str(item.get("s") or ""),
            url=url,
            overall=int(item.get("r") or 0),
            slug=slug,
        )
    return by_slug


def parse_overall_from_html(html: str) -> int | None:
    m = re.search(r"rated\s+(\d{2})\s+overall", html, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None


def parse_chart_values(html: str) -> list[int]:
    for m in re.finditer(r"data:\s*\[([\d,\s]+)\]", html):
        vals = [int(x.strip()) for x in m.group(1).split(",") if x.strip()]
        if len(vals) in (6, 7):
            return vals
    return []


def face_stats_from_chart(
    values: list[int],
    *,
    overall: int,
    game_position: str,
) -> FcFaceStats:
    if len(values) == 6:
        pac, sho, pas, dri, defending, phy = values
        aerial = int(round((defending + phy) / 2))
    elif len(values) == 7:
        pac, sho, pas, dri, defending, phy, gk = values
        aerial = gk if game_position == "GK" else int(round((defending + phy) / 2))
    else:
        raise ValueError(f"expected 6 or 7 chart values, got {len(values)}")

    return FcFaceStats(
        pac=pac,
        sho=sho,
        pas=pas,
        dri=dri,
        defending=defending,
        phy=phy,
        aerial=aerial,
        overall=overall,
    )


def parse_player_page(html: str, *, game_position: str, fallback_overall: int) -> FcFaceStats:
    values = parse_chart_values(html)
    if not values:
        raise ValueError("chart data not found")
    overall = parse_overall_from_html(html) or fallback_overall
    return face_stats_from_chart(values, overall=overall, game_position=game_position)


def derived_secondary_stats(overall: int, pas: int, dri: int, phy: int) -> tuple[int, int]:
    mentality = int(max(1, min(99, round((overall + pas + dri) / 3))))
    injury = int(max(1, min(99, round((overall + phy) / 2))))
    return mentality, injury
