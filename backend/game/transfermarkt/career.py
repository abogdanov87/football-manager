"""Parse Transfermarkt player transfer history from profile HTML."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import date

from .dates import parse_tm_date

_ROW_RE = re.compile(
    r'<tr[^>]*class="[^"]*(?:bg_Weiß|bg_Grau)[^"]*"[^>]*>(.*?)</tr>',
    re.S | re.I,
)
_CLUB_LINK_RE = re.compile(
    r'href="/[^"]+/startseite/verein/\d+"[^>]*title="([^"]+)"',
    re.I,
)
_DATE_CELL_RE = re.compile(
    r'<td[^>]*class="zentriert"[^>]*>\s*(\d{2}/\d{2}/\d{4}|-)\s*</td>',
    re.I,
)


@dataclass(frozen=True)
class TMCareerRow:
    club_name: str
    from_date: date | None
    to_date: date | None


def parse_transfer_history(html_text: str) -> list[TMCareerRow]:
    """Best-effort parse of TM transfers table on profile page."""
    block_m = re.search(
        r"(?:Transfer history|Transfers)</h2>(.*?)(?:<h2|$)",
        html_text,
        re.S | re.I,
    )
    if not block_m:
        return []
    block = block_m.group(1)
    rows: list[TMCareerRow] = []
    for row_html in _ROW_RE.findall(block):
        club_m = _CLUB_LINK_RE.search(row_html)
        if not club_m:
            continue
        club_name = html.unescape(club_m.group(1)).strip()
        dates = []
        for dm in _DATE_CELL_RE.finditer(row_html):
            raw = dm.group(1).strip()
            if raw == "-":
                dates.append(None)
            else:
                dates.append(parse_tm_date(raw))
        from_d = dates[0] if dates else None
        to_d = dates[1] if len(dates) > 1 else None
        rows.append(TMCareerRow(club_name=club_name, from_date=from_d, to_date=to_d))
    return rows
