"""Pure Python match simulation for Football Manager v0.1."""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from typing import Iterable

from .formations import FORMATION_SPECS

ENGINE_VERSION = "0.1"

# Per-formation modifiers from T—Ж tactical profiles (see formations.py).
FORMATION_ATTACK = {code: spec["attack"] for code, spec in FORMATION_SPECS.items()}
FORMATION_DEFENSE = {code: spec["defense"] for code, spec in FORMATION_SPECS.items()}
HOME_ADVANTAGE = 1.06


@dataclass
class SquadSnapshot:
    club_id: int
    club_name: str
    formation: str
    player_names: list[str]
    attack_strength: float
    defense_strength: float


@dataclass
class MatchSimulationResult:
    home_score: int
    away_score: int
    events: list[str]
    seed: str


def _seed_rng(fixture_id: int, season_id: int) -> random.Random:
    raw = f"{fixture_id}:{season_id}:{ENGINE_VERSION}"
    digest = hashlib.sha256(raw.encode()).hexdigest()
    return random.Random(int(digest[:16], 16))


def squad_strength(overalls: Iterable[float], formation: str, is_home: bool) -> tuple[float, float]:
    ratings = list(overalls)
    if not ratings:
        return 50.0, 50.0
    base = sum(ratings) / len(ratings)
    attack = base * FORMATION_ATTACK.get(formation, 1.0)
    defense = base * FORMATION_DEFENSE.get(formation, 1.0)
    if is_home:
        attack *= HOME_ADVANTAGE
        defense *= HOME_ADVANTAGE * 0.98
    return attack, defense


def _pick_scorer(names: list[str], rng: random.Random) -> str:
    if not names:
        return "Игрок"
    return rng.choice(names)


def simulate_match(
    fixture_id: int,
    season_id: int,
    home: SquadSnapshot,
    away: SquadSnapshot,
) -> MatchSimulationResult:
    rng = _seed_rng(fixture_id, season_id)
    seed = f"{fixture_id}-{season_id}"

    home_xg = max(0.4, (home.attack_strength / max(away.defense_strength, 1)) * 1.35)
    away_xg = max(0.4, (away.attack_strength / max(home.defense_strength, 1)) * 1.2)

    home_score = _goals_from_xg(home_xg, rng)
    away_score = _goals_from_xg(away_xg, rng)

    # Slight bias toward competitive scorelines
    if rng.random() < 0.15:
        home_score = max(home_score, away_score)
    elif rng.random() < 0.15:
        away_score = max(away_score, home_score)

    events: list[str] = [
        f"0' — Начало матча: {home.club_name} — {away.club_name}.",
        f"Схемы: {home.formation} против {away.formation}.",
    ]

    minute_pool = list(range(8, 88, 7))
    rng.shuffle(minute_pool)

    for i in range(home_score):
        m = minute_pool.pop() if minute_pool else rng.randint(10, 85)
        scorer = _pick_scorer(home.player_names, rng)
        events.append(f"{m}' — ГОЛ! {scorer} ({home.club_name}).")

    for i in range(away_score):
        m = minute_pool.pop() if minute_pool else rng.randint(10, 85)
        scorer = _pick_scorer(away.player_names, rng)
        events.append(f"{m}' — ГОЛ! {scorer} ({away.club_name}).")

    if len(events) < 5 and rng.random() < 0.6:
        m = rng.randint(20, 80)
        events.append(f"{m}' — Опасный момент, но мяч мимо ворот.")

    events.append(f"90+ — Финальный свисток: {home_score}:{away_score}.")

    return MatchSimulationResult(
        home_score=home_score,
        away_score=away_score,
        events=events[:8],
        seed=seed,
    )


def _goals_from_xg(xg: float, rng: random.Random) -> int:
    lam = max(0.3, min(xg, 3.5))
    goals = 0
    for _ in range(12):
        if rng.random() < lam / 12:
            goals += 1
    return min(goals, 6)
