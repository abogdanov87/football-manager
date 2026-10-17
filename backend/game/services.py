from __future__ import annotations

from typing import Iterable

from django.db import transaction

from .match_engine import ENGINE_VERSION, MatchSimulationResult, simulate_match, squad_strength
from .models import Club, Fixture, Match, Player, Season, Standing


def default_lineup(club: Club) -> list[int]:
    if club.lineup_player_ids:
        return club.lineup_player_ids
    by_pos = {"GK": [], "DEF": [], "MID": [], "FWD": []}
    for p in club.players.all():
        by_pos.setdefault(p.position, []).append(p.id)
    for key in by_pos:
        by_pos[key].sort(key=lambda pid: -Player.objects.get(pk=pid).overall)

    formation = club.formation
    if formation == "4-3-3":
        counts = {"GK": 1, "DEF": 4, "MID": 3, "FWD": 3}
    else:
        counts = {"GK": 1, "DEF": 4, "MID": 4, "FWD": 2}

    ids: list[int] = []
    for pos, count in counts.items():
        ids.extend(by_pos.get(pos, [])[:count])
    return ids


def lineup_players(club: Club) -> list[Player]:
    ids = default_lineup(club)
    players = list(Player.objects.filter(club=club, id__in=ids))
    order = {pid: i for i, pid in enumerate(ids)}
    players.sort(key=lambda p: order.get(p.id, 999))
    return players


def _snapshot(club: Club, is_home: bool):
    from .match_engine import SquadSnapshot

    players = lineup_players(club)
    overalls = [p.overall * p.form for p in players]
    attack, defense = squad_strength(overalls, club.formation, is_home)
    return SquadSnapshot(
        club_id=club.id,
        club_name=club.name,
        formation=club.formation,
        player_names=[p.name for p in players],
        attack_strength=attack,
        defense_strength=defense,
    )


def apply_match_to_standings(
    season: Season, home: Club, away: Club, home_score: int, away_score: int
) -> None:
    for club, gf, ga, result in (
        (home, home_score, away_score, _result(home_score, away_score)),
        (away, away_score, home_score, _result(away_score, home_score)),
    ):
        standing, _ = Standing.objects.get_or_create(season=season, club=club)
        standing.played += 1
        standing.goals_for += gf
        standing.goals_against += ga
        if result == "W":
            standing.won += 1
            standing.points += 3
        elif result == "D":
            standing.drawn += 1
            standing.points += 1
        else:
            standing.lost += 1
        standing.save()


def _result(gf: int, ga: int) -> str:
    if gf > ga:
        return "W"
    if gf == ga:
        return "D"
    return "L"


@transaction.atomic
def simulate_fixture(fixture: Fixture) -> Match:
    if fixture.is_played and hasattr(fixture, "match_result"):
        return fixture.match_result

    home_snap = _snapshot(fixture.home_club, True)
    away_snap = _snapshot(fixture.away_club, False)
    result: MatchSimulationResult = simulate_match(
        fixture.id, fixture.season_id, home_snap, away_snap
    )

    match, _ = Match.objects.update_or_create(
        fixture=fixture,
        defaults={
            "home_score": result.home_score,
            "away_score": result.away_score,
            "events": result.events,
            "engine_version": ENGINE_VERSION,
            "seed": result.seed,
        },
    )
    if not fixture.is_played:
        fixture.is_played = True
        fixture.save(update_fields=["is_played"])
        apply_match_to_standings(
            fixture.season,
            fixture.home_club,
            fixture.away_club,
            result.home_score,
            result.away_score,
        )
    return match


def simulate_matchday(season: Season, matchday: int | None = None) -> list[Match]:
    md = matchday or season.current_matchday
    fixtures = list(
        Fixture.objects.filter(season=season, matchday=md, is_played=False).select_related(
            "home_club", "away_club"
        )
    )
    matches = [simulate_fixture(f) for f in fixtures]
    if fixtures and all(f.is_played for f in fixtures):
        _maybe_advance_matchday(season, md)
    return matches


def _maybe_advance_matchday(season: Season, completed_md: int) -> None:
    if season.current_matchday != completed_md:
        return
    if completed_md >= season.total_matchdays:
        return
    season.current_matchday = completed_md + 1
    season.save(update_fields=["current_matchday"])


def generate_round_robin(clubs: Iterable[Club], season: Season) -> None:
    club_list = list(clubs)
    n = len(club_list)
    if n % 2:
        club_list.append(None)
        n += 1
    rounds = n - 1
    half = n // 2
    rotated = club_list[:]

    matchday = 1
    for _ in range(rounds):
        for i in range(half):
            home = rotated[i]
            away = rotated[n - 1 - i]
            if home is None or away is None:
                continue
            Fixture.objects.create(
                season=season,
                matchday=matchday,
                home_club=home,
                away_club=away,
            )
        rotated = [rotated[0]] + [rotated[-1]] + rotated[1:-1]
        matchday += 1

    # Second leg (reverse home/away)
    first_leg = list(Fixture.objects.filter(season=season).order_by("matchday", "id"))
    max_md = max(f.matchday for f in first_leg)
    for f in first_leg:
        Fixture.objects.create(
            season=season,
            matchday=f.matchday + max_md,
            home_club=f.away_club,
            away_club=f.home_club,
        )
    season.total_matchdays = max_md * 2
    season.save(update_fields=["total_matchdays"])
