"""Parse Sports.ru club squad pages (JSON-LD SportsTeam)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

_LD_JSON_RE = re.compile(
    r'<script type="application/ld\+json">(.*?)</script>',
    re.S,
)


@dataclass(frozen=True)
class SportsRuPlayer:
    slug: str
    name: str
    url: str


def _slug_from_person_url(url: str) -> str:
    return url.rstrip("/").split("/")[-1]


def parse_club_squad_athletes(html: str) -> list[SportsRuPlayer]:
    players: list[SportsRuPlayer] = []
    for block in _LD_JSON_RE.findall(html):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict) or data.get("@type") != "SportsTeam":
            continue
        athletes = data.get("athlete")
        if not isinstance(athletes, list):
            continue
        for row in athletes:
            if not isinstance(row, dict):
                continue
            url = str(row.get("url") or "")
            name = str(row.get("name") or "").strip()
            if "/football/person/" not in url or not name:
                continue
            players.append(
                SportsRuPlayer(
                    slug=_slug_from_person_url(url),
                    name=name,
                    url=url,
                )
            )
        break
    return players
