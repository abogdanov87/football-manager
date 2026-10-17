from django.core.management.base import BaseCommand

from game.models import Season
from game.scheduler import run_scheduled_matchday


class Command(BaseCommand):
    help = (
        "Ежедневная симуляция тура лиги (для cron). "
        "Идемпотентна в пределах календарного дня."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Игнорировать next_simulation_at и повторный запуск в тот же день",
        )
        parser.add_argument(
            "--season-id",
            type=int,
            default=None,
            help="ID сезона (по умолчанию — активный)",
        )

    def handle(self, *args, **options):
        season = self._get_season(options["season_id"])
        result = run_scheduled_matchday(season, force=options["force"])
        style = self.style.SUCCESS if result.status == "simulated" else self.style.WARNING
        self.stdout.write(
            style(f"[{result.status}] {result.message} (матчей: {result.matches_played})")
        )

    def _get_season(self, season_id: int | None) -> Season:
        if season_id:
            return Season.objects.get(pk=season_id)
        season = Season.objects.filter(is_active=True).order_by("-id").first()
        if not season:
            raise Season.DoesNotExist("Нет активного сезона")
        return season
