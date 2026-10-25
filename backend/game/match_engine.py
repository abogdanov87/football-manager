"""Match simulation: 6×15 min segments, per-chance xG, role-weighted scorers."""

from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass
from typing import Iterable

from .formations import FORMATION_SPECS

ENGINE_VERSION = "0.5.3"

FORMATION_ATTACK = {code: spec["attack"] for code, spec in FORMATION_SPECS.items()}
FORMATION_DEFENSE = {code: spec["defense"] for code, spec in FORMATION_SPECS.items()}
HOME_ADVANTAGE = 1.06

SEGMENTS = 6
SEGMENT_MINUTES = 15
# Average open-play chances per team per 15-minute block (scaled by strength).
BASE_CHANCES_PER_SEGMENT = 1.15
BASE_CORNERS_PER_SEGMENT = 0.82
BASE_FREE_KICKS_PER_SEGMENT = 0.32
BASE_PENALTIES_PER_SEGMENT = 0.09

# Open-play chance taker weights (sum ≈ 1).
CHANCE_WEIGHT_BY_POSITION = {
    "GK": 0.01,
    "DEF": 0.08,
    "MID": 0.34,
    "FWD": 0.57,
}

# Corner / aerial threat weights (sum ≈ 1).
CORNER_WEIGHT_BY_POSITION = {
    "GK": 0.02,
    "DEF": 0.40,
    "MID": 0.26,
    "FWD": 0.32,
}

# Player who committed the foul (defending team).
FOULER_WEIGHT_BY_POSITION = {
    "GK": 0.02,
    "DEF": 0.52,
    "MID": 0.36,
    "FWD": 0.10,
}


@dataclass(frozen=True)
class MatchPlayer:
    name: str
    position: str
    form: float
    overall: int
    sho: int
    pac: int
    dri: int
    pas: int
    defending: int
    phy: int
    aerial: int
    mentality: int
    injury_resistance: int
    player_id: int | None = None


@dataclass
class SquadSnapshot:
    club_id: int
    club_name: str
    formation: str
    players: list[MatchPlayer]
    player_names: list[str]
    attack_strength: float
    defense_strength: float
    penalty_taker: str | None = None
    free_kick_taker: str | None = None
    bench_players: list[MatchPlayer] | None = None


@dataclass
class MatchSimulationResult:
    home_score: int
    away_score: int
    events: list[str]
    seed: str
    home_scorers: dict[str, int] | None = None
    away_scorers: dict[str, int] | None = None
    home_assisters: dict[str, int] | None = None
    away_assisters: dict[str, int] | None = None
    home_yellow_cards: dict[str, int] | None = None
    away_yellow_cards: dict[str, int] | None = None
    home_red_cards: dict[str, int] | None = None
    away_red_cards: dict[str, int] | None = None
    home_injury_days: dict[str, int] | None = None
    away_injury_days: dict[str, int] | None = None


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


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _segment_chance_lambda(attack: float, opp_defense: float, is_home: bool) -> float:
    ratio = attack / max(opp_defense, 25.0)
    lam = BASE_CHANCES_PER_SEGMENT * (0.65 + 0.55 * ratio)
    if is_home:
        lam *= 1.04
    return _clamp(lam, 0.35, 3.2)


def _sample_chance_count(lam: float, rng: random.Random) -> int:
    """Poisson-ish count via Knuth for small lambda."""
    if lam <= 0:
        return 0
    l = math.exp(-lam)
    k = 0
    p = 1.0
    while p > l:
        k += 1
        p *= rng.random()
    return max(0, k - 1)


def _sample_chance_xg(attack: float, opp_defense: float, rng: random.Random) -> float:
    """Base chance quality before shooter and goalkeeper."""
    pressure = attack / max(opp_defense, 25.0)
    # Beta-like: mostly 0.08–0.35, occasional big chance.
    roll = rng.random()
    if roll < 0.12:
        base = rng.uniform(0.28, 0.55)
    elif roll < 0.45:
        base = rng.uniform(0.14, 0.28)
    else:
        base = rng.uniform(0.05, 0.16)
    return _clamp(base * (0.88 + 0.18 * pressure), 0.03, 0.72)


def designate_set_piece_takers(
    players: list[MatchPlayer],
    *,
    penalty_name: str | None = None,
    free_kick_name: str | None = None,
) -> tuple[str | None, str | None]:
    outfield = [p for p in players if p.position != "GK"]
    if not outfield:
        return None, None
    by_name = {p.name: p for p in outfield}
    if penalty_name and penalty_name in by_name:
        pen = penalty_name
    else:
        pen = max(outfield, key=lambda p: p.sho * 0.65 + p.mentality * 0.35).name
    if free_kick_name and free_kick_name in by_name:
        fk = free_kick_name
    else:
        fk = max(
            outfield, key=lambda p: p.sho * 0.45 + p.pas * 0.45 + p.mentality * 0.1
        ).name
    return pen, fk


def _position_weights(players: list[MatchPlayer], table: dict[str, float]) -> list[float]:
    weights = [table.get(p.position, 0.1) for p in players]
    total = sum(weights)
    if total <= 0:
        return [1.0 / len(players)] * len(players)
    return [w / total for w in weights]


def _pick_player(players: list[MatchPlayer], weights: list[float], rng: random.Random) -> MatchPlayer:
    return rng.choices(players, weights=weights, k=1)[0]


def _pick_assister(
    players: list[MatchPlayer], scorer: MatchPlayer, rng: random.Random
) -> str | None:
    pool = [p for p in players if p.name != scorer.name and p.position != "GK"]
    if not pool or rng.random() > 0.55:
        return None
    weights = [max(p.pas, 1) for p in pool]
    return rng.choices(pool, weights=weights, k=1)[0].name


def _finishing_skill(player: MatchPlayer) -> float:
    form = _clamp(player.form, 0.75, 1.2)
    if player.position == "FWD":
        raw = 0.55 * player.sho + 0.25 * player.dri + 0.12 * player.pac + 0.08 * player.phy
    elif player.position == "MID":
        raw = 0.35 * player.sho + 0.30 * player.dri + 0.25 * player.pas + 0.10 * player.phy
    elif player.position == "DEF":
        raw = 0.25 * player.sho + 0.20 * player.aerial + 0.35 * player.defending + 0.20 * player.phy
    else:
        raw = 0.40 * player.defending + 0.35 * player.dri + 0.25 * player.phy
    mentality = 0.92 + player.mentality / 250.0
    return (raw / 80.0) * form * mentality


def _goalkeeper_save_factor(gk: MatchPlayer | None) -> float:
    """Multiplier applied to goal probability (lower = better GK)."""
    if gk is None or gk.position != "GK":
        return 1.0
    # GK attrs mapped to DIV/HAN/REF in defending/phy/dri.
    shot_stopping = (gk.defending * 0.4 + gk.dri * 0.35 + gk.phy * 0.25) / 100.0
    return _clamp(1.0 - shot_stopping * 0.42, 0.55, 1.0)


def _resolve_designated_taker(
    players: list[MatchPlayer],
    designated_name: str | None,
    rng: random.Random,
) -> MatchPlayer:
    if designated_name:
        for p in players:
            if p.name == designated_name:
                return p
    return rng.choice(players)


def _set_piece_xg(kind: str, attack: float, opp_defense: float, rng: random.Random) -> float:
    pressure = attack / max(opp_defense, 25.0)
    if kind == "pen":
        return _clamp(0.74 * (0.96 + 0.06 * pressure), 0.68, 0.84)
    if kind == "fk":
        base = rng.uniform(0.06, 0.14) if rng.random() < 0.7 else rng.uniform(0.14, 0.26)
        return _clamp(base * (0.9 + 0.15 * pressure), 0.04, 0.32)
    # corner
    base = rng.uniform(0.06, 0.14) if rng.random() < 0.65 else rng.uniform(0.14, 0.22)
    return _clamp(base * (0.88 + 0.12 * pressure), 0.04, 0.28)


def _free_kick_skill(player: MatchPlayer) -> float:
    form = _clamp(player.form, 0.75, 1.2)
    raw = player.sho * 0.45 + player.pas * 0.42 + player.mentality * 0.13
    return (raw / 80.0) * form


def _penalty_skill(player: MatchPlayer) -> float:
    form = _clamp(player.form, 0.75, 1.2)
    raw = player.sho * 0.68 + player.mentality * 0.32
    return (raw / 80.0) * form


def _aerial_finish_skill(player: MatchPlayer) -> float:
    form = _clamp(player.form, 0.75, 1.2)
    raw = player.aerial * 0.45 + player.sho * 0.25 + player.phy * 0.20 + player.defending * 0.10
    return (raw / 80.0) * form


def _goal_probability(
    xg: float,
    shooter: MatchPlayer,
    opp_gk: MatchPlayer | None,
    rng: random.Random,
    *,
    kind: str = "open",
) -> float:
    if kind == "pen":
        finish = _penalty_skill(shooter)
        p = xg * (0.82 + 0.35 * finish)
    elif kind == "fk":
        finish = _free_kick_skill(shooter)
        p = xg * (0.78 + 0.48 * finish)
    elif kind == "corner":
        finish = _aerial_finish_skill(shooter)
        p = xg * (0.75 + 0.50 * finish)
    else:
        finish = _finishing_skill(shooter)
        p = xg * (0.72 + 0.55 * finish)
    p *= _goalkeeper_save_factor(opp_gk)
    # Small noise so identical xG does not always repeat.
    p *= rng.uniform(0.94, 1.06)
    return _clamp(p, 0.02, 0.88)


def _goalkeeper(players: list[MatchPlayer]) -> MatchPlayer | None:
    for p in players:
        if p.position == "GK":
            return p
    return players[0] if players else None


def _format_report_line(event: _ChanceEvent) -> str | None:
    """Public match log: no segment markers; emoji by event kind."""
    if "Отрезок" in event.text:
        return None
    text = event.text
    if event.is_goal:
        return f"⚽ {text}"
    if event.kind == "corner":
        return f"🚩 {text}"
    if event.kind == "fk":
        return f"🎯 {text}"
    if event.kind == "pen":
        return f"🥅 {text}"
    if event.kind == "injury":
        return f"🤕 {text}"
    if event.kind == "sub":
        return f"🔄 {text}"
    if event.kind == "card":
        if "Красная" in text or "удаление" in text:
            return f"🟥 {text}"
        return f"🟨 {text}"
    return text


def _minute_in_segment(segment_index: int, rng: random.Random) -> int:
    start = segment_index * SEGMENT_MINUTES
    return start + rng.randint(1, SEGMENT_MINUTES)


@dataclass
class _ChanceEvent:
    minute: int
    text: str
    is_goal: bool
    sort_key: int
    kind: str = "open"
    seq: int = 0
    scorer_name: str | None = None
    assister_name: str | None = None
    club_name: str | None = None
    subject_name: str | None = None
    card_type: str | None = None
    injury_days: int | None = None


@dataclass
class _DisciplineState:
    yellow_cards: dict[str, int]


def _foul_card_probabilities(foul_kind: str) -> tuple[float, float, float]:
    """Returns (p_yellow, p_straight_red, p_second_yellow) for the fouler."""
    if foul_kind == "pen":
        return 0.58, 0.12, 0.85
    return 0.38, 0.04, 0.72


def _pick_substitute(injured: MatchPlayer, bench: list[MatchPlayer]) -> MatchPlayer | None:
    if not bench:
        return None
    same_pos = [p for p in bench if p.position == injured.position]
    pool = same_pos if same_pos else bench
    return max(pool, key=lambda p: p.overall)


def _apply_injury_substitution(
    *,
    on_pitch: list[MatchPlayer],
    bench: list[MatchPlayer],
    injured: MatchPlayer,
    club_name: str,
    minute: int,
    rng: random.Random,
) -> list[_ChanceEvent]:
    injury_days = rng.randint(5, 28)
    events: list[_ChanceEvent] = [
        _ChanceEvent(
            minute=minute,
            text=f"{minute}' — Травма: {injured.name} ({club_name}), игрок не может продолжить.",
            is_goal=False,
            sort_key=minute,
            kind="injury",
            club_name=club_name,
            subject_name=injured.name,
            injury_days=injury_days,
        )
    ]
    idx = next((i for i, p in enumerate(on_pitch) if p.name == injured.name), None)
    if idx is None:
        return events

    on_pitch.pop(idx)
    sub = _pick_substitute(injured, bench)
    if sub is None:
        events.append(
            _ChanceEvent(
                minute=minute,
                text=f"{minute}' — Запас {club_name} исчерпан, команда продолжает в меньшинстве.",
                is_goal=False,
                sort_key=minute,
                kind="sub",
            )
        )
        return events

    bench.remove(sub)
    on_pitch.insert(idx, sub)
    events.append(
        _ChanceEvent(
            minute=minute,
            text=f"{minute}' — Замена ({club_name}): {injured.name} → {sub.name}.",
            is_goal=False,
            sort_key=minute,
            kind="sub",
        )
    )
    return events


def _foul_injury_probability(foul_kind: str, victim: MatchPlayer) -> float:
    resist = _clamp(victim.injury_resistance, 1, 99) / 100.0
    base = 0.14 if foul_kind == "pen" else 0.07
    return _clamp(base * (1.15 - resist * 0.65), 0.01, 0.22)


def _simulate_foul_discipline(
    *,
    minute: int,
    foul_kind: str,
    attacking: list[MatchPlayer],
    defending: list[MatchPlayer],
    attacking_club: str,
    defending_club: str,
    fouled_player: MatchPlayer,
    attacking_bench: list[MatchPlayer],
    discipline: _DisciplineState,
    rng: random.Random,
) -> list[_ChanceEvent]:
    if not defending:
        return []

    fouler_weights = _position_weights(defending, FOULER_WEIGHT_BY_POSITION)
    fouler = _pick_player(defending, fouler_weights, rng)
    p_yellow, p_red, p_second_yellow = _foul_card_probabilities(foul_kind)
    out: list[_ChanceEvent] = []

    roll = rng.random()
    if roll < p_red:
        out.append(
            _ChanceEvent(
                minute=minute,
                text=f"{minute}' — Красная карточка: {fouler.name} ({defending_club}) — грубый фол.",
                is_goal=False,
                sort_key=minute,
                kind="card",
                club_name=defending_club,
                subject_name=fouler.name,
                card_type="red",
            )
        )
        discipline.yellow_cards.pop(fouler.name, None)
    elif discipline.yellow_cards.get(fouler.name, 0) >= 1 and rng.random() < p_second_yellow:
        out.append(
            _ChanceEvent(
                minute=minute,
                text=f"{minute}' — Вторая жёлтая — удаление: {fouler.name} ({defending_club}).",
                is_goal=False,
                sort_key=minute,
                kind="card",
                club_name=defending_club,
                subject_name=fouler.name,
                card_type="red",
            )
        )
        discipline.yellow_cards.pop(fouler.name, None)
    elif roll < p_yellow + p_red:
        discipline.yellow_cards[fouler.name] = discipline.yellow_cards.get(fouler.name, 0) + 1
        foul_label = "пенальти" if foul_kind == "pen" else "штрафной"
        out.append(
            _ChanceEvent(
                minute=minute,
                text=f"{minute}' — Жёлтая карточка: {fouler.name} ({defending_club}) — фол ({foul_label}).",
                is_goal=False,
                sort_key=minute,
                kind="card",
                club_name=defending_club,
                subject_name=fouler.name,
                card_type="yellow",
            )
        )

    victim = fouled_player if any(p.name == fouled_player.name for p in attacking) else rng.choice(attacking)
    if rng.random() < _foul_injury_probability(foul_kind, victim):
        out.extend(
            _apply_injury_substitution(
                on_pitch=attacking,
                bench=attacking_bench,
                injured=victim,
                club_name=attacking_club,
                minute=minute,
                rng=rng,
            )
        )

    return out


def _simulate_team_chances(
    *,
    segment: int,
    attack: float,
    defense_opp: float,
    is_home: bool,
    attackers: list[MatchPlayer],
    opp_gk: MatchPlayer | None,
    club_name: str,
    rng: random.Random,
) -> list[_ChanceEvent]:
    if not attackers:
        return []

    lam = _segment_chance_lambda(attack, defense_opp, is_home)
    count = _sample_chance_count(lam, rng)
    weights = _position_weights(attackers, CHANCE_WEIGHT_BY_POSITION)
    out: list[_ChanceEvent] = []

    for _ in range(count):
        xg = _sample_chance_xg(attack, defense_opp, rng)
        shooter = _pick_player(attackers, weights, rng)
        minute = _minute_in_segment(segment, rng)
        p_goal = _goal_probability(xg, shooter, opp_gk, rng, kind="open")

        if rng.random() < p_goal:
            assister = _pick_assister(attackers, shooter, rng)
            out.append(
                _ChanceEvent(
                    minute=minute,
                    text=f"{minute}' — ГОЛ! {shooter.name} ({club_name}).",
                    is_goal=True,
                    sort_key=minute,
                    kind="open",
                    scorer_name=shooter.name,
                    assister_name=assister,
                    club_name=club_name,
                )
            )
        elif xg >= 0.22 and rng.random() < 0.35:
            out.append(
                _ChanceEvent(
                    minute=minute,
                    text=f"{minute}' — Опасный момент: {shooter.name} ({club_name}), мимо.",
                    is_goal=False,
                    sort_key=minute,
                    kind="open",
                )
            )

    return out


def _scaled_set_piece_lambda(base: float, attack: float, opp_defense: float) -> float:
    ratio = attack / max(opp_defense, 25.0)
    return _clamp(base * (0.7 + 0.45 * ratio), 0.08, 2.5)


def _simulate_corners(
    *,
    segment: int,
    attack: float,
    defense_opp: float,
    attackers: list[MatchPlayer],
    opp_gk: MatchPlayer | None,
    club_name: str,
    rng: random.Random,
) -> list[_ChanceEvent]:
    if not attackers:
        return []
    count = _sample_chance_count(_scaled_set_piece_lambda(BASE_CORNERS_PER_SEGMENT, attack, defense_opp), rng)
    weights = _position_weights(attackers, CORNER_WEIGHT_BY_POSITION)
    out: list[_ChanceEvent] = []

    for _ in range(count):
        minute = _minute_in_segment(segment, rng)
        out.append(
            _ChanceEvent(
                minute=minute,
                text=f"{minute}' — Угловой ({club_name}).",
                is_goal=False,
                sort_key=minute,
                kind="corner",
            )
        )
        if rng.random() < 0.55:
            continue
        xg = _set_piece_xg("corner", attack, defense_opp, rng)
        shooter = _pick_player(attackers, weights, rng)
        p_goal = _goal_probability(xg, shooter, opp_gk, rng, kind="corner")
        if rng.random() < p_goal:
            out.append(
                _ChanceEvent(
                    minute=minute,
                    text=f"{minute}' — ГОЛ! {shooter.name} ({club_name}) с углового.",
                    is_goal=True,
                    sort_key=minute,
                    kind="corner",
                    scorer_name=shooter.name,
                    club_name=club_name,
                )
            )
        elif xg >= 0.12:
            out.append(
                _ChanceEvent(
                    minute=minute,
                    text=f"{minute}' — После углового: {shooter.name} ({club_name}), мимо.",
                    is_goal=False,
                    sort_key=minute,
                    kind="corner",
                )
            )
    return out


def _simulate_free_kicks(
    *,
    segment: int,
    attack: float,
    defense_opp: float,
    attackers: list[MatchPlayer],
    defenders: list[MatchPlayer],
    opp_gk: MatchPlayer | None,
    club_name: str,
    defending_club: str,
    designated: str | None,
    attacking_bench: list[MatchPlayer],
    discipline: _DisciplineState,
    rng: random.Random,
) -> list[_ChanceEvent]:
    if not attackers:
        return []
    count = _sample_chance_count(
        _scaled_set_piece_lambda(BASE_FREE_KICKS_PER_SEGMENT, attack, defense_opp), rng
    )
    out: list[_ChanceEvent] = []

    for _ in range(count):
        minute = _minute_in_segment(segment, rng)
        taker = _resolve_designated_taker(attackers, designated, rng)
        out.extend(
            _simulate_foul_discipline(
                minute=minute,
                foul_kind="fk",
                attacking=attackers,
                defending=defenders,
                attacking_club=club_name,
                defending_club=defending_club,
                fouled_player=taker,
                attacking_bench=attacking_bench,
                discipline=discipline,
                rng=rng,
            )
        )
        xg = _set_piece_xg("fk", attack, defense_opp, rng)
        p_goal = _goal_probability(xg, taker, opp_gk, rng, kind="fk")
        if rng.random() < p_goal:
            out.append(
                _ChanceEvent(
                    minute=minute,
                    text=f"{minute}' — ГОЛ! {taker.name} ({club_name}) со штрафного.",
                    is_goal=True,
                    sort_key=minute,
                    kind="fk",
                    scorer_name=taker.name,
                    club_name=club_name,
                )
            )
        else:
            out.append(
                _ChanceEvent(
                    minute=minute,
                    text=f"{minute}' — Штрафной: {taker.name} ({club_name}), мимо.",
                    is_goal=False,
                    sort_key=minute,
                    kind="fk",
                )
            )
    return out


def _simulate_penalties(
    *,
    segment: int,
    attack: float,
    defense_opp: float,
    attackers: list[MatchPlayer],
    defenders: list[MatchPlayer],
    opp_gk: MatchPlayer | None,
    club_name: str,
    defending_club: str,
    designated: str | None,
    attacking_bench: list[MatchPlayer],
    discipline: _DisciplineState,
    rng: random.Random,
) -> list[_ChanceEvent]:
    if not attackers:
        return []
    count = _sample_chance_count(
        _scaled_set_piece_lambda(BASE_PENALTIES_PER_SEGMENT, attack, defense_opp), rng
    )
    out: list[_ChanceEvent] = []

    for _ in range(count):
        minute = _minute_in_segment(segment, rng)
        taker = _resolve_designated_taker(attackers, designated, rng)
        out.extend(
            _simulate_foul_discipline(
                minute=minute,
                foul_kind="pen",
                attacking=attackers,
                defending=defenders,
                attacking_club=club_name,
                defending_club=defending_club,
                fouled_player=taker,
                attacking_bench=attacking_bench,
                discipline=discipline,
                rng=rng,
            )
        )
        xg = _set_piece_xg("pen", attack, defense_opp, rng)
        p_goal = _goal_probability(xg, taker, opp_gk, rng, kind="pen")
        out.append(
            _ChanceEvent(
                minute=minute,
                text=f"{minute}' — Пенальти ({club_name}) — {taker.name}.",
                is_goal=False,
                sort_key=minute,
                kind="pen",
            )
        )
        if rng.random() < p_goal:
            out.append(
                _ChanceEvent(
                    minute=minute,
                    text=f"{minute}' — ГОЛ! {taker.name} ({club_name}) с пенальти.",
                    is_goal=True,
                    sort_key=minute,
                    kind="pen",
                    scorer_name=taker.name,
                    club_name=club_name,
                )
            )
        else:
            out.append(
                _ChanceEvent(
                    minute=minute,
                    text=f"{minute}' — Пенальти не забит: {taker.name} ({club_name}).",
                    is_goal=False,
                    sort_key=minute,
                    kind="pen",
                )
            )
    return out


def _simulate_team_set_pieces(
    *,
    segment: int,
    attack: float,
    defense_opp: float,
    attackers: list[MatchPlayer],
    defenders: list[MatchPlayer],
    opp_gk: MatchPlayer | None,
    club_name: str,
    defending_club: str,
    penalty_taker: str | None,
    free_kick_taker: str | None,
    attacking_bench: list[MatchPlayer],
    discipline: _DisciplineState,
    rng: random.Random,
) -> list[_ChanceEvent]:
    events: list[_ChanceEvent] = []
    events.extend(
        _simulate_corners(
            segment=segment,
            attack=attack,
            defense_opp=defense_opp,
            attackers=attackers,
            opp_gk=opp_gk,
            club_name=club_name,
            rng=rng,
        )
    )
    events.extend(
        _simulate_free_kicks(
            segment=segment,
            attack=attack,
            defense_opp=defense_opp,
            attackers=attackers,
            defenders=defenders,
            opp_gk=opp_gk,
            club_name=club_name,
            defending_club=defending_club,
            designated=free_kick_taker,
            attacking_bench=attacking_bench,
            discipline=discipline,
            rng=rng,
        )
    )
    events.extend(
        _simulate_penalties(
            segment=segment,
            attack=attack,
            defense_opp=defense_opp,
            attackers=attackers,
            defenders=defenders,
            opp_gk=opp_gk,
            club_name=club_name,
            defending_club=defending_club,
            designated=penalty_taker,
            attacking_bench=attacking_bench,
            discipline=discipline,
            rng=rng,
        )
    )
    return events


def simulate_match(
    fixture_id: int,
    season_id: int,
    home: SquadSnapshot,
    away: SquadSnapshot,
) -> MatchSimulationResult:
    rng = _seed_rng(fixture_id, season_id)
    seed = f"{fixture_id}-{season_id}"

    home_players = home.players or [
        MatchPlayer(n, "MID", 1.0, 70, 50, 50, 50, 50, 50, 50, 50, 50, 50)
        for n in home.player_names
    ]
    away_players = away.players or [
        MatchPlayer(n, "MID", 1.0, 70, 50, 50, 50, 50, 50, 50, 50, 50, 50)
        for n in away.player_names
    ]

    home_discipline = _DisciplineState(yellow_cards={})
    away_discipline = _DisciplineState(yellow_cards={})
    home_bench: list[MatchPlayer] = list(home.bench_players or [])
    away_bench: list[MatchPlayer] = list(away.bench_players or [])

    home_gk = _goalkeeper(home_players)
    away_gk = _goalkeeper(away_players)

    all_events: list[_ChanceEvent] = [
        _ChanceEvent(
            0,
        f"0' — Начало матча: {home.club_name} — {away.club_name}.",
            False,
            0,
        ),
        _ChanceEvent(
            0,
        f"Схемы: {home.formation} против {away.formation}.",
            False,
            0,
        ),
    ]

    for seg in range(SEGMENTS):
        seg_start = seg * SEGMENT_MINUTES + 1
        seg_end = (seg + 1) * SEGMENT_MINUTES
        all_events.append(
            _ChanceEvent(
                seg_start,
                f"{seg_start}' — Отрезок {seg + 1}/6 ({seg_start}–{seg_end} мин).",
                False,
                seg_start,
            )
        )

        fatigue = 1.0 - seg * 0.015
        home_atk = home.attack_strength * fatigue
        away_atk = away.attack_strength * fatigue

        all_events.extend(
            _simulate_team_chances(
                segment=seg,
                attack=home_atk,
                defense_opp=away.defense_strength,
                is_home=True,
                attackers=home_players,
                opp_gk=away_gk,
                club_name=home.club_name,
                rng=rng,
            )
        )
        all_events.extend(
            _simulate_team_set_pieces(
                segment=seg,
                attack=home_atk,
                defense_opp=away.defense_strength,
                attackers=home_players,
                defenders=away_players,
                opp_gk=away_gk,
                club_name=home.club_name,
                defending_club=away.club_name,
                penalty_taker=home.penalty_taker,
                free_kick_taker=home.free_kick_taker,
                attacking_bench=home_bench,
                discipline=away_discipline,
                rng=rng,
            )
        )
        all_events.extend(
            _simulate_team_chances(
                segment=seg,
                attack=away_atk,
                defense_opp=home.defense_strength,
                is_home=False,
                attackers=away_players,
                opp_gk=home_gk,
                club_name=away.club_name,
                rng=rng,
            )
        )
        all_events.extend(
            _simulate_team_set_pieces(
                segment=seg,
                attack=away_atk,
                defense_opp=home.defense_strength,
                attackers=away_players,
                defenders=home_players,
                opp_gk=home_gk,
                club_name=away.club_name,
                defending_club=home.club_name,
                penalty_taker=away.penalty_taker,
                free_kick_taker=away.free_kick_taker,
                attacking_bench=away_bench,
                discipline=home_discipline,
                rng=rng,
            )
        )

    goals = [e for e in all_events if e.is_goal]
    home_score = sum(1 for e in goals if f"({home.club_name})" in e.text)
    away_score = sum(1 for e in goals if f"({away.club_name})" in e.text)

    all_events.append(
        _ChanceEvent(
            90,
            f"90+ — Финальный свисток: {home_score}:{away_score}.",
            False,
            999,
        )
    )

    for seq, event in enumerate(all_events):
        event.seq = seq
    all_events.sort(
        key=lambda e: (
            1 if "Финальный" in e.text else 0,
            e.sort_key,
            e.seq,
        )
    )

    text_events: list[str] = []
    open_miss_budget = 3
    for e in all_events:
        include = (
            e.text.startswith("0'")
            or e.is_goal
            or "Финальный" in e.text
            or e.kind in ("corner", "fk", "pen", "card", "injury", "sub")
            or ("мимо" in e.text and open_miss_budget > 0)
        )
        if not include:
            continue
        if "мимо" in e.text and e.kind == "open":
            open_miss_budget -= 1
        line = _format_report_line(e)
        if line:
            text_events.append(line)

    def _agg(club: str) -> tuple[dict[str, int], dict[str, int]]:
        scorers: dict[str, int] = {}
        assisters: dict[str, int] = {}
        for e in all_events:
            if not e.is_goal or e.club_name != club or not e.scorer_name:
                continue
            scorers[e.scorer_name] = scorers.get(e.scorer_name, 0) + 1
            if e.assister_name:
                assisters[e.assister_name] = assisters.get(e.assister_name, 0) + 1
        return scorers, assisters

    home_s, home_a = _agg(home.club_name)
    away_s, away_a = _agg(away.club_name)

    def _agg_discipline(club: str) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
        yellow: dict[str, int] = {}
        red: dict[str, int] = {}
        injury_days: dict[str, int] = {}
        for e in all_events:
            if e.club_name != club or not e.subject_name:
                continue
            if e.kind == "card" and e.card_type == "yellow":
                yellow[e.subject_name] = yellow.get(e.subject_name, 0) + 1
            elif e.kind == "card" and e.card_type == "red":
                red[e.subject_name] = red.get(e.subject_name, 0) + 1
            elif e.kind == "injury" and e.injury_days:
                injury_days[e.subject_name] = injury_days.get(e.subject_name, 0) + e.injury_days
        return yellow, red, injury_days

    home_y, home_r, home_inj = _agg_discipline(home.club_name)
    away_y, away_r, away_inj = _agg_discipline(away.club_name)

    return MatchSimulationResult(
        home_score=home_score,
        away_score=away_score,
        events=text_events[:55],
        seed=seed,
        home_scorers=home_s,
        away_scorers=away_s,
        home_assisters=home_a,
        away_assisters=away_a,
        home_yellow_cards=home_y,
        away_yellow_cards=away_y,
        home_red_cards=home_r,
        away_red_cards=away_r,
        home_injury_days=home_inj,
        away_injury_days=away_inj,
    )
