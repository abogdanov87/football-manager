"""Player minutes, favorite positions, match stat persistence."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone

from django.db import transaction

from .models import (
    Match,
    Player,
    PlayerMatchAppearance,
    PlayerPositionMinuteLedger,
    PlayerSeasonStat,
    Season,
)

POSITION_WINDOW_MINUTES = 9000
BOOTSTRAP_MINUTES = 3000


def position_code_for_player(player: Player) -> str:
    if player.tm_position:
        return player.tm_position[:32]
    return player.position


def bootstrap_position_minutes(player: Player) -> bool:
    """One-time 3000 minutes on current position. Returns True if applied."""
    if player.position_minutes_bootstrapped:
        return False
    code = position_code_for_player(player)
    with transaction.atomic():
        PlayerPositionMinuteLedger.objects.create(
            player=player,
            position_code=code,
            minutes=BOOTSTRAP_MINUTES,
            source=PlayerPositionMinuteLedger.Source.BOOTSTRAP,
            match=None,
        )
        player.position_minutes_bootstrapped = True
        player.save(update_fields=["position_minutes_bootstrapped"])
    return True


def bootstrap_all_players(players: list[Player] | None = None) -> int:
    qs = players if players is not None else Player.objects.all()
    count = 0
    for p in qs:
        if bootstrap_position_minutes(p):
            count += 1
    return count


def _ledger_chronological(player_id: int) -> list[tuple[datetime, str, int]]:
    rows = list(
        PlayerPositionMinuteLedger.objects.filter(player_id=player_id)
        .select_related("match__fixture")
        .order_by("recorded_at", "id")
    )
    out: list[tuple[datetime, str, int]] = []
    for row in rows:
        if row.source == PlayerPositionMinuteLedger.Source.BOOTSTRAP:
            ts = datetime(1970, 1, 1, tzinfo=timezone.utc)
        elif row.match_id:
            fix = row.match.fixture
            ts = datetime(2026, 8, 1, tzinfo=timezone.utc)
            ts = ts.replace(month=min(12, 7 + (fix.matchday % 10)))
            ts = ts.replace(day=min(28, 1 + fix.matchday % 27))
        else:
            ts = row.recorded_at
        out.append((ts, row.position_code, row.minutes))
    return out


def favorite_positions_top3(player_id: int, limit: int = 3) -> list[dict]:
    """Top positions by minutes within rolling 9000-minute window."""
    entries = _ledger_chronological(player_id)
    if not entries:
        return []

    # Newest-first consumption for window trim
    chunks: list[tuple[str, int]] = []
    for _ts, code, mins in reversed(entries):
        chunks.append((code, mins))

    kept: list[tuple[str, int]] = []
    total = 0
    for code, mins in chunks:
        if total >= POSITION_WINDOW_MINUTES:
            break
        take = min(mins, POSITION_WINDOW_MINUTES - total)
        if take > 0:
            kept.append((code, take))
            total += take

    by_pos: dict[str, int] = defaultdict(int)
    for code, mins in kept:
        by_pos[code] += mins

    window_total = sum(by_pos.values()) or 1
    ranked = sorted(by_pos.items(), key=lambda x: -x[1])[:limit]
    return [
        {
            "position_code": code,
            "minutes": mins,
            "percent": round(100.0 * mins / window_total, 1),
        }
        for code, mins in ranked
    ]


@transaction.atomic
def record_club_match_stats(
    *,
    season: Season,
    match: Match,
    club_id: int,
    lineup: list[tuple[Player, str]],
    goals_by_player_id: dict[int, int],
    assists_by_player_id: dict[int, int],
    yellow_cards_by_player_id: dict[int, int] | None = None,
    red_cards_by_player_id: dict[int, int] | None = None,
    injury_days_by_player_id: dict[int, int] | None = None,
) -> None:
    yellow_cards_by_player_id = yellow_cards_by_player_id or {}
    red_cards_by_player_id = red_cards_by_player_id or {}
    injury_days_by_player_id = injury_days_by_player_id or {}
    for player, position_code in lineup:
        if player.club_id != club_id:
            continue
        goals = goals_by_player_id.get(player.id, 0)
        assists = assists_by_player_id.get(player.id, 0)
        yellow_cards = yellow_cards_by_player_id.get(player.id, 0)
        red_cards = red_cards_by_player_id.get(player.id, 0)
        injury_days = injury_days_by_player_id.get(player.id, 0)
        PlayerMatchAppearance.objects.update_or_create(
            player=player,
            match=match,
            defaults={
                "minutes": 90,
                "position_code": position_code,
                "goals": goals,
                "assists": assists,
                "yellow_cards": yellow_cards,
                "red_cards": red_cards,
                "injury_days": injury_days,
                "started": True,
            },
        )
        PlayerPositionMinuteLedger.objects.create(
            player=player,
            position_code=position_code,
            minutes=90,
            source=PlayerPositionMinuteLedger.Source.MATCH,
            match=match,
        )
        stat, _ = PlayerSeasonStat.objects.get_or_create(season=season, player=player)
        stat.appearances += 1
        stat.minutes += 90
        stat.goals += goals
        stat.assists += assists
        stat.yellow_cards += yellow_cards
        stat.red_cards += red_cards
        stat.injury_days += injury_days
        stat.save()
