"""Transfermarkt default lineup (FinalFormation ceapi + slot assignment)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Iterable

from game.formations import FORMATION_SPECS
from game.models import Club, Player

_FORMATION_RE = re.compile(r"([0-9]+(?:-[0-9]+)+)")

# Slot order matches frontend FORMATION_PITCH_SLOTS (GK → DEF → MID lines → FWD).
_SLOT_HINTS: dict[str, list[str]] = {
    "4-2-3-1": ["GK", "LB", "CB", "CB", "RB", "DM", "DM", "LW", "AM", "RW", "CF"],
    "4-3-3": ["GK", "LB", "CB", "CB", "RB", "CM", "CM", "CM", "LW", "CF", "RW"],
    "4-4-2": ["GK", "LB", "CB", "CB", "RB", "LM", "CM", "CM", "RM", "CF", "CF"],
    "4-4-2-d": ["GK", "LB", "CB", "CB", "RB", "DM", "LM", "RM", "AM", "CF", "CF"],
    "4-5-1": ["GK", "LB", "CB", "CB", "RB", "LM", "CM", "CM", "CM", "RM", "CF"],
    "3-4-3": ["GK", "CB", "CB", "CB", "LM", "CM", "CM", "RM", "LW", "CF", "RW"],
    "3-5-2": ["GK", "CB", "CB", "CB", "LWB", "CM", "CM", "CM", "RWB", "CF", "CF"],
    "3-4-2-1": ["GK", "CB", "CB", "CB", "LM", "CM", "CM", "RM", "AM", "AM", "CF"],
    "4-1-4-1": ["GK", "LB", "CB", "CB", "RB", "DM", "LM", "CM", "CM", "RM", "CF"],
    "4-3-2-1": ["GK", "LB", "CB", "CB", "RB", "CM", "CM", "CM", "AM", "AM", "CF"],
    "4-2-4": ["GK", "LB", "CB", "CB", "RB", "DM", "DM", "LW", "CF", "CF", "RW"],
    "3-6-1": ["GK", "CB", "CB", "CB", "LM", "CM", "CM", "CM", "CM", "RM", "CF"],
    "2-3-5": ["GK", "CB", "CB", "CM", "CM", "CM", "LW", "CF", "CF", "CF", "RW"],
    "2-4-3-1": ["GK", "CB", "CB", "LM", "CM", "CM", "RM", "LW", "AM", "RW", "CF"],
}

_HINT_ALIASES: dict[str, tuple[str, ...]] = {
    "GK": ("GK",),
    "LB": ("LB", "LWB"),
    "RB": ("RB", "RWB"),
    "CB": ("CB",),
    "DM": ("DM", "CDM"),
    "CM": ("CM",),
    "AM": ("AM", "CAM"),
    "LM": ("LM", "LW"),
    "RM": ("RM", "RW"),
    "LW": ("LW", "LM"),
    "RW": ("RW", "RM"),
    "LWB": ("LWB", "LB"),
    "RWB": ("RWB", "RB"),
    "CF": ("CF", "ST"),
    "ST": ("ST", "CF"),
}


@dataclass(frozen=True)
class TmLineup:
    formation: str
    player_tm_ids: list[int]


# TM tactics not in FORMATION_CHOICES → closest supported code for match engine / UI.
_FORMATION_MODEL_MAP: dict[str, str] = {
    "3-4-2-1": "2-4-3-1",
}


def normalize_tm_formation(raw: str) -> str:
    text = (raw or "").strip()
    m = _FORMATION_RE.search(text)
    if not m:
        return "4-4-2"
    code = m.group(1)
    if code in FORMATION_SPECS:
        return code
    if code in _SLOT_HINTS:
        return _FORMATION_MODEL_MAP.get(code, "4-4-2")
    return "4-4-2"


def formation_for_db(tm_tactic: str) -> tuple[str, str]:
    """Return (formation stored on Club, slot key for ordering starters)."""
    m = _FORMATION_RE.search((tm_tactic or "").strip())
    code = m.group(1) if m else "4-4-2"
    if code in FORMATION_SPECS:
        return code, code
    if code in _FORMATION_MODEL_MAP:
        return _FORMATION_MODEL_MAP[code], code
    if code in _SLOT_HINTS:
        return "4-4-2", code
    return "4-4-2", "4-4-2"


def parse_final_formation_payload(data: dict[str, Any]) -> TmLineup | None:
    match_info = data.get("matchInfo") or {}
    tactic = match_info.get("tactic") or data.get("formation") or ""
    formation, _slot_key = formation_for_db(str(tactic))

    players_raw = (data.get("list") or {}).get("players") or []
    if not isinstance(players_raw, list) or len(players_raw) < 11:
        return None

    tm_ids: list[int] = []
    for row in players_raw[:11]:
        if not isinstance(row, dict):
            return None
        pid = row.get("id")
        if pid is None:
            return None
        tm_ids.append(int(pid))

    return TmLineup(formation=formation, player_tm_ids=tm_ids)


def parse_final_formation_json(text: str) -> TmLineup | None:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    return parse_final_formation_payload(data)


def _slot_hints(formation: str) -> list[str]:
    if formation in _SLOT_HINTS:
        return _SLOT_HINTS[formation]
    spec = FORMATION_SPECS.get(formation) or FORMATION_SPECS["4-4-2"]
    hints: list[str] = ["GK"]
    hints.extend(["CB"] * spec["def_"])
    hints.extend(["CM"] * spec["mid"])
    hints.extend(["CF"] * spec["fwd"])
    return hints[:11]


def _position_short(row: dict[str, Any]) -> str:
    return str(row.get("positionShort") or row.get("positionMain") or "").upper()


def _score_hint(hint: str, row: dict[str, Any]) -> int:
    short = _position_short(row)
    if not short:
        return 0
    aliases = _HINT_ALIASES.get(hint, (hint,))
    if short in aliases:
        return 100
    # DM playing full-back etc.
    if hint in ("LB", "RB") and short in ("DM", "CM", "AM"):
        return 40
    if hint == "DM" and short in ("CM", "AM"):
        return 35
    if hint in ("LW", "RW", "AM") and short in ("LW", "RW", "AM", "LM", "RM"):
        return 50
    if hint == "CF" and short in ("CF", "ST", "RW", "LW"):
        return 45
    return 0


def order_starters_for_formation(
    formation: str, starter_rows: list[dict[str, Any]]
) -> list[int]:
    """Map TM starter JSON rows to slot order used by the tactics UI."""
    if len(starter_rows) < 11:
        return [int(r["id"]) for r in starter_rows if r.get("id")]

    hints = _slot_hints(formation)
    pool = list(starter_rows[:11])
    used: set[int] = set()
    ordered_ids: list[int] = []

    for hint in hints:
        best_idx = -1
        best_score = -1
        for i, row in enumerate(pool):
            if i in used:
                continue
            score = _score_hint(hint, row)
            if score > best_score:
                best_score = score
                best_idx = i
        if best_idx < 0:
            for i, row in enumerate(pool):
                if i not in used:
                    best_idx = i
                    break
        used.add(best_idx)
        ordered_ids.append(int(pool[best_idx]["id"]))

    return ordered_ids


def apply_tm_lineup_to_club(
    club: Club,
    lineup: TmLineup,
    starter_rows: Iterable[dict[str, Any]] | None = None,
    *,
    slot_formation: str | None = None,
) -> list[int]:
    """Resolve TM ids to DB player ids; set club.formation and return lineup_player_ids."""
    formation = lineup.formation
    slot_key = slot_formation or formation
    if formation not in FORMATION_SPECS:
        formation = "4-4-2"

    by_tm = {
        p.transfermarkt_id: p
        for p in Player.objects.filter(club=club, transfermarkt_id__in=lineup.player_tm_ids)
    }

    if starter_rows:
        ordered_tm = order_starters_for_formation(
            slot_key, list(starter_rows)[:11]
        )
    else:
        ordered_tm = lineup.player_tm_ids

    db_ids: list[int] = []
    for tm_id in ordered_tm:
        player = by_tm.get(tm_id)
        if player is not None:
            db_ids.append(player.id)

    if len(db_ids) < 11:
        from game.services import default_lineup

        club.formation = formation
        club.save(update_fields=["formation"])
        return default_lineup(club)

    club.formation = formation
    club.lineup_player_ids = db_ids
    club.save(update_fields=["formation", "lineup_player_ids"])
    return db_ids
