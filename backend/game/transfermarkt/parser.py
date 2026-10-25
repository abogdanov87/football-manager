"""Parse Transfermarkt competition and squad HTML (stdlib only)."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import date
from typing import Iterable

from .profile import parse_squad_row_details

_PORTRAIT_RE = re.compile(
    r'data-src="(https://img\.a\.transfermarkt\.technology/portrait/[^"]+)"'
)

_ROW_RE = re.compile(
    r'<tr class="(?:odd|even)">\s*'
    r'<td class="zentriert rueckennummer[^"]*"[^>]*>.*?'
    r'<a href="(?P<path>/[^"]+/profil/spieler/(?P<tm_id>\d+))">\s*(?P<name_inner>.*?)\s*</a>.*?'
    r'<tr>\s*<td>\s*(?P<tm_position>[^<]+?)\s*</td>.*?'
    r'<td class="zentriert">(?P<dob_age>[^<]+)</td>.*?'
    r'<td class="rechts[^"]*">(?:<a[^>]*>)?(?P<market_value>[^<]+)',
    re.S,
)


def _player_name_from_anchor_inner(inner_html: str) -> str:
    text = re.sub(r"<[^>]+>", "", inner_html)
    return html.unescape(text).strip()


def _portrait_url_for_player(row_html: str, transfermarkt_id: int) -> str:
    """Pick the portrait whose CDN path matches this player's TM id."""
    needle = f"/{transfermarkt_id}-"
    for m in _PORTRAIT_RE.finditer(row_html):
        url = m.group(1).strip()
        if needle in url:
            return url
    portrait_m = _PORTRAIT_RE.search(row_html)
    return portrait_m.group(1).strip() if portrait_m else ""

_CLUB_KADER_RE = re.compile(
    r'href="/(?P<slug>[^/]+)/kader/verein/(?P<verein_id>\d+)/saison_id/(?P<season>\d+)"',
)

_DOB_AGE_RE = re.compile(r"\((\d+)\)")


@dataclass(frozen=True)
class TMClubRef:
    slug: str
    verein_id: int
    season_id: int


@dataclass(frozen=True)
class TMPlayerRow:
    transfermarkt_id: int
    transfermarkt_slug: str
    name_latin: str
    tm_position: str
    age: int
    market_value_raw: str
    portrait_url: str = ""
    date_of_birth: date | None = None
    nationalities: list[dict[str, str]] | None = None
    contract_end_date: date | None = None

    @property
    def market_value_eur(self) -> int:
        from .attributes import parse_market_value_eur

        return parse_market_value_eur(self.market_value_raw)


def _extract_items_table(html_text: str) -> str:
    start = html_text.find('<table class="items">')
    if start < 0:
        return ""
    # The squad table contains nested <table class="inline-table">; walk outer <table> tags.
    depth = 0
    i = start
    while i < len(html_text):
        open_idx = html_text.find("<table", i)
        close_idx = html_text.find("</table>", i)
        if close_idx < 0:
            break
        if open_idx != -1 and open_idx < close_idx:
            depth += 1
            i = open_idx + 6
            continue
        depth -= 1
        i = close_idx + len("</table>")
        if depth == 0:
            return html_text[start:i]
    return html_text[start:]


def parse_squad_page(html_text: str) -> list[TMPlayerRow]:
    table = _extract_items_table(html_text)
    players: list[TMPlayerRow] = []
    for m in _ROW_RE.finditer(table):
        slug = m.group("path").split("/")[1]
        age_m = _DOB_AGE_RE.search(m.group("dob_age"))
        age = int(age_m.group(1)) if age_m else 25
        row_html = m.group(0)
        portrait = _portrait_url_for_player(row_html, int(m.group("tm_id")))
        details = parse_squad_row_details(
            row_html, dob_age_cell=m.group("dob_age")
        )
        players.append(
            TMPlayerRow(
                transfermarkt_id=int(m.group("tm_id")),
                transfermarkt_slug=slug,
                name_latin=_player_name_from_anchor_inner(m.group("name_inner")),
                tm_position=html.unescape(m.group("tm_position").strip()),
                age=age,
                market_value_raw=html.unescape(m.group("market_value").strip()),
                portrait_url=portrait,
                date_of_birth=details.date_of_birth,
                nationalities=details.nationalities,
                contract_end_date=details.contract_end_date,
            )
        )
    return players


def parse_competition_clubs(html_text: str) -> list[TMClubRef]:
    seen: set[tuple[str, int]] = set()
    clubs: list[TMClubRef] = []
    for m in _CLUB_KADER_RE.finditer(html_text):
        key = (m.group("slug"), int(m.group("verein_id")))
        if key in seen:
            continue
        seen.add(key)
        clubs.append(
            TMClubRef(
                slug=m.group("slug"),
                verein_id=int(m.group("verein_id")),
                season_id=int(m.group("season")),
            )
        )
    return clubs


# TM URL slug → crest file slug (frontend/public/crests/clubs/{slug}.png)
TM_SLUG_TO_CREST: dict[str, str] = {
    "manchester-city": "manchester-city",
    "arsenal-fc": "arsenal",
    "fc-arsenal": "arsenal",
    "chelsea-fc": "chelsea",
    "fc-chelsea": "chelsea",
    "liverpool-fc": "liverpool",
    "fc-liverpool": "liverpool",
    "manchester-united": "manchester-united",
    "tottenham-hotspur": "tottenham-hotspur",
    "newcastle-united": "newcastle-united",
    "brighton-amp-hove-albion": "brighton",
    "brighton-hove-albion": "brighton",
    "brentford-fc": "brentford",
    "fc-brentford": "brentford",
    "aston-villa": "aston-villa",
    "afc-bournemouth": "afc-bournemouth",
    "crystal-palace": "crystal-palace",
    "nottingham-forest": "nottingham-forest",
    "everton-fc": "everton",
    "fc-everton": "everton",
    "fulham-fc": "fulham",
    "fc-fulham": "fulham",
    "ipswich-town": "ipswich-town",
    "leicester-city": "leicester-city",
    "southampton-fc": "southampton",
    "fc-southampton": "southampton",
    "west-ham-united": "west-ham-united",
    "wolverhampton-wanderers": "wolverhampton-wanderers",
    "afc-sunderland": "sunderland",
    "sunderland-afc": "sunderland",
    "leeds-united": "leeds-united",
    "coventry-city": "coventry-city",
    "hull-city": "hull-city",
    "burnley-fc": "burnley",
    "luton-town": "luton-town",
}


def crest_slug_from_tm(tm_slug: str) -> str | None:
    if tm_slug in TM_SLUG_TO_CREST:
        return TM_SLUG_TO_CREST[tm_slug]
    normalized = tm_slug.replace("fc-", "").replace("-fc", "")
    if normalized in TM_SLUG_TO_CREST.values():
        return normalized
    return None


def crest_slug_from_crest_url(crest_url: str) -> str | None:
    m = re.search(r"/crests/clubs/([^./]+)\.png", crest_url)
    return m.group(1) if m else None


def match_club_by_crest_slug(
    crest_slug: str, clubs: Iterable
) -> object | None:
    for club in clubs:
        slug = crest_slug_from_crest_url(club.crest_url)
        if slug == crest_slug:
            return club
    return None
