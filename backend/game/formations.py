"""Tactical formations (T—Ж: https://t-j.ru/football-tactics/)."""

from __future__ import annotations

from typing import TypedDict


class FormationSpec(TypedDict):
    label: str
    gk: int
    def_: int
    mid: int
    fwd: int
    attack: float
    defense: float


# Slot lines: GK / DEF / MID / FWD (field players sum to 10).
# Attack/defense multipliers reflect article tone; ~1.0 when neutral.
FORMATION_SPECS: dict[str, FormationSpec] = {
    "4-3-3": {
        "label": "4-3-3",
        "gk": 1,
        "def_": 4,
        "mid": 3,
        "fwd": 3,
        "attack": 1.08,
        "defense": 0.96,
    },
    "4-5-1": {
        "label": "4-5-1",
        "gk": 1,
        "def_": 4,
        "mid": 5,
        "fwd": 1,
        "attack": 0.92,
        "defense": 1.10,
    },
    "4-4-2": {
        "label": "4-4-2",
        "gk": 1,
        "def_": 4,
        "mid": 4,
        "fwd": 2,
        "attack": 1.0,
        "defense": 1.02,
    },
    "4-4-2-d": {
        "label": "4-4-2 с ромбом",
        "gk": 1,
        "def_": 4,
        "mid": 4,
        "fwd": 2,
        "attack": 1.02,
        "defense": 1.0,
    },
    "4-2-3-1": {
        "label": "4-2-3-1",
        "gk": 1,
        "def_": 4,
        "mid": 5,
        "fwd": 1,
        "attack": 1.05,
        "defense": 1.0,
    },
    "3-4-3": {
        "label": "3-4-3",
        "gk": 1,
        "def_": 3,
        "mid": 4,
        "fwd": 3,
        "attack": 1.06,
        "defense": 0.98,
    },
    "3-5-2": {
        "label": "3-5-2",
        "gk": 1,
        "def_": 3,
        "mid": 5,
        "fwd": 2,
        "attack": 1.03,
        "defense": 1.0,
    },
    "2-3-5": {
        "label": "2-3-5 (устаревшая)",
        "gk": 1,
        "def_": 2,
        "mid": 3,
        "fwd": 5,
        "attack": 1.12,
        "defense": 0.88,
    },
    "4-2-4": {
        "label": "4-2-4 (устаревшая)",
        "gk": 1,
        "def_": 4,
        "mid": 2,
        "fwd": 4,
        "attack": 1.10,
        "defense": 0.90,
    },
    "3-6-1": {
        "label": "3-6-1",
        "gk": 1,
        "def_": 3,
        "mid": 6,
        "fwd": 1,
        "attack": 0.94,
        "defense": 1.06,
    },
    "2-4-3-1": {
        "label": "2-4-3-1",
        "gk": 1,
        "def_": 2,
        "mid": 7,
        "fwd": 1,
        "attack": 1.07,
        "defense": 0.93,
    },
    "4-1-4-1": {
        "label": "4-1-4-1",
        "gk": 1,
        "def_": 4,
        "mid": 5,
        "fwd": 1,
        "attack": 1.0,
        "defense": 1.04,
    },
    "4-3-2-1": {
        "label": "4-3-2-1 (ёлочка)",
        "gk": 1,
        "def_": 4,
        "mid": 5,
        "fwd": 1,
        "attack": 0.98,
        "defense": 1.03,
    },
    "3-2-4-1": {
        "label": "3-2-4-1",
        "gk": 1,
        "def_": 3,
        "mid": 6,
        "fwd": 1,
        "attack": 1.08,
        "defense": 0.95,
    },
    "4-2-2-2": {
        "label": "4-2-2-2",
        "gk": 1,
        "def_": 4,
        "mid": 4,
        "fwd": 2,
        "attack": 1.04,
        "defense": 0.98,
    },
    "4-4-1-1": {
        "label": "4-4-1-1",
        "gk": 1,
        "def_": 4,
        "mid": 5,
        "fwd": 1,
        "attack": 1.02,
        "defense": 1.01,
    },
    "3-1-3-3": {
        "label": "3-1-3-3",
        "gk": 1,
        "def_": 3,
        "mid": 4,
        "fwd": 3,
        "attack": 1.10,
        "defense": 0.92,
    },
    "3-1-4-2": {
        "label": "3-1-4-2",
        "gk": 1,
        "def_": 3,
        "mid": 5,
        "fwd": 2,
        "attack": 1.05,
        "defense": 0.98,
    },
    "5-4-1": {
        "label": "5-4-1",
        "gk": 1,
        "def_": 5,
        "mid": 4,
        "fwd": 1,
        "attack": 0.88,
        "defense": 1.12,
    },
    "4-1-3-2": {
        "label": "4-1-3-2",
        "gk": 1,
        "def_": 4,
        "mid": 4,
        "fwd": 2,
        "attack": 1.07,
        "defense": 0.97,
    },
}


FORMATION_CHOICES = [(code, spec["label"]) for code, spec in FORMATION_SPECS.items()]


def formation_position_counts(code: str) -> dict[str, int]:
    spec = FORMATION_SPECS.get(code) or FORMATION_SPECS["4-4-2"]
    return {
        "GK": spec["gk"],
        "DEF": spec["def_"],
        "MID": spec["mid"],
        "FWD": spec["fwd"],
    }
