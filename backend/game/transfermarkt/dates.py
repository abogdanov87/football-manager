"""Transfermarkt date parsing and contract fallbacks."""

from __future__ import annotations

import random
import re
from datetime import date, datetime

_TM_DATE_RE = re.compile(r"(\d{2})/(\d{2})/(\d{4})")
_CONTRACT_FALLBACK_BASE = date(2026, 11, 1)


def parse_tm_date(text: str) -> date | None:
    m = _TM_DATE_RE.search((text or "").strip())
    if not m:
        return None
    day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
    try:
        return date(year, month, day)
    except ValueError:
        return None


def age_from_dob(dob: date, *, on: date | None = None) -> int:
    today = on or date.today()
    years = today.year - dob.year
    if (today.month, today.day) < (dob.month, dob.day):
        years -= 1
    return max(15, years)


def fallback_contract_end(transfermarkt_id: int) -> date:
    """Deterministic random 1–5 years after 01.11.2026."""
    rng = random.Random(transfermarkt_id)
    years = rng.randint(1, 5)
    return date(_CONTRACT_FALLBACK_BASE.year + years, 11, 1)
