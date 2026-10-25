"""Parse Transfermarkt player profile and squad-row details."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import date

from .dates import fallback_contract_end, parse_tm_date

_FLAG_IMG_RE = re.compile(
    r'<img[^>]+flagge/[^>]+title="([^"]+)"[^>]*src="([^"]+)"',
    re.I,
)
_FLAG_IMG_ALT_RE = re.compile(
    r'<img[^>]+src="([^"]+flagge[^"]+)"[^>]+title="([^"]+)"',
    re.I,
)
_ZENTRIERT_CELL_RE = re.compile(r'<td class="zentriert">([^<]*)</td>', re.S)


@dataclass(frozen=True)
class TMPlayerDetails:
    date_of_birth: date | None
    nationalities: list[dict[str, str]]
    contract_end_date: date | None


def _nationalities_from_html(fragment: str) -> list[dict[str, str]]:
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for pattern in (_FLAG_IMG_RE, _FLAG_IMG_ALT_RE):
        for m in pattern.finditer(fragment):
            if pattern is _FLAG_IMG_RE:
                name, url = m.group(1).strip(), m.group(2).strip()
            else:
                url, name = m.group(1).strip(), m.group(2).strip()
            if not name or name in seen:
                continue
            seen.add(name)
            out.append({"name": html.unescape(name), "flag_url": url})
    return out


def _contract_from_row(row_html: str) -> date | None:
    pure_dates: list[str] = []
    for m in _ZENTRIERT_CELL_RE.finditer(row_html):
        text = html.unescape(m.group(1)).strip()
        if re.fullmatch(r"\d{2}/\d{2}/\d{4}", text):
            pure_dates.append(text)
    if not pure_dates:
        return None
    return parse_tm_date(pure_dates[-1])


def parse_squad_row_details(row_html: str, *, dob_age_cell: str) -> TMPlayerDetails:
    dob = parse_tm_date(dob_age_cell)
    flag_cell_m = re.search(
        r'<td class="zentriert">\d{2}/\d{2}/\d{4}[^<]*</td>\s*'
        r'<td class="zentriert">(.*?)</td>',
        row_html,
        re.S,
    )
    nationalities = (
        _nationalities_from_html(flag_cell_m.group(1)) if flag_cell_m else []
    )
    contract = _contract_from_row(row_html)
    return TMPlayerDetails(
        date_of_birth=dob,
        nationalities=nationalities,
        contract_end_date=contract,
    )


def parse_player_profile(html_text: str) -> TMPlayerDetails:
    """Parse /profil/spieler/{id} page (info table)."""
    dob: date | None = None
    dob_block = re.search(
        r"Date of birth(?:/Age)?.*?</span>\s*"
        r'<span class="info-table__content info-table__content--bold">(.*?)</span>',
        html_text,
        re.S | re.I,
    )
    if dob_block:
        dob = parse_tm_date(dob_block.group(1))

    nat_block = re.search(
        r"Citizenship:.*?</span>\s*"
        r'<span class="info-table__content info-table__content--bold">(.*?)</span>',
        html_text,
        re.S | re.I,
    )
    nationalities = (
        _nationalities_from_html(nat_block.group(1)) if nat_block else []
    )

    contract: date | None = None
    contract_block = re.search(
        r"Contract expires:?\s*</span>\s*"
        r'<span class="info-table__content info-table__content--bold">\s*([^<]+)',
        html_text,
        re.S | re.I,
    )
    if contract_block:
        raw = html.unescape(contract_block.group(1)).strip()
        if raw and raw != "-":
            contract = parse_tm_date(raw)
    if contract is None:
        inline = re.search(
            r"Contract expires:\s*(\d{2}/\d{2}/\d{4})",
            html_text,
            re.I,
        )
        if inline:
            contract = parse_tm_date(inline.group(1))

    return TMPlayerDetails(
        date_of_birth=dob,
        nationalities=nationalities,
        contract_end_date=contract,
    )


def resolve_contract_end(
    contract: date | None, transfermarkt_id: int
) -> date:
    if contract is not None:
        return contract
    return fallback_contract_end(transfermarkt_id)
