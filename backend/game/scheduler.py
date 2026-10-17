from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import MatchdayRun, Season
from .services import simulate_matchday


@dataclass
class ScheduledRunResult:
    status: str
    message: str
    matchday: int | None = None
    matches_played: int = 0


def simulation_time_today(reference: datetime | None = None) -> datetime:
    ref = reference or timezone.now()
    hour = int(getattr(settings, "LEAGUE_SIMULATION_HOUR", 12))
    minute = int(getattr(settings, "LEAGUE_SIMULATION_MINUTE", 0))
    local_date = timezone.localdate(ref)
    naive = datetime.combine(local_date, time(hour=hour, minute=minute))
    return timezone.make_aware(naive, timezone.get_current_timezone())


def compute_next_simulation_at(from_moment: datetime | None = None) -> datetime:
    moment = from_moment or timezone.now()
    slot_today = simulation_time_today(moment)
    if moment < slot_today:
        return slot_today
    return simulation_time_today(moment + timedelta(days=1))


def ensure_season_schedule(season: Season) -> None:
    if season.next_simulation_at is None:
        season.next_simulation_at = compute_next_simulation_at()
        season.save(update_fields=["next_simulation_at"])


@transaction.atomic
def run_scheduled_matchday(season: Season, force: bool = False) -> ScheduledRunResult:
    ensure_season_schedule(season)
    now = timezone.now()
    today = timezone.localdate(now)

    if season.is_complete:
        return ScheduledRunResult(
            status="season_complete",
            message="Сезон завершён",
            matchday=season.current_matchday,
        )

    if MatchdayRun.objects.filter(season=season, run_date=today).exists() and not force:
        return ScheduledRunResult(
            status="skipped",
            message="Тур за сегодня уже сыгран (идемпотентный пропуск)",
            matchday=season.current_matchday,
        )

    if not force and season.next_simulation_at and now < season.next_simulation_at:
        return ScheduledRunResult(
            status="not_due",
            message="Ещё не время симуляции тура",
            matchday=season.current_matchday,
        )

    matchday_before = season.current_matchday
    matches = simulate_matchday(season)
    season.refresh_from_db()

    MatchdayRun.objects.get_or_create(
        season=season,
        run_date=today,
        defaults={"matchday": matchday_before},
    )

    season.last_simulation_at = now
    season.next_simulation_at = compute_next_simulation_at(now)
    season.save(update_fields=["last_simulation_at", "next_simulation_at"])

    return ScheduledRunResult(
        status="simulated",
        message=f"Симулирован тур {matchday_before}",
        matchday=matchday_before,
        matches_played=len(matches),
    )
