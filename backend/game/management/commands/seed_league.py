import random

from django.core.management.base import BaseCommand
from django.db import transaction

from game.models import Club, Player, Season, Standing
from game.scheduler import compute_next_simulation_at, ensure_season_schedule
from game.services import default_lineup, generate_round_robin


CLUB_DATA = [
    ("Спартак Москва", "SPA"),
    ("Динамо", "DIN"),
    ("Локомотив", "LOK"),
    ("ЦСКА", "CSK"),
    ("Краснодар", "KRA"),
    ("Рубин", "RUB"),
    ("Ростов", "ROS"),
    ("Сочи", "SOC"),
    ("Ахмат", "AKH"),
    ("Урал", "URA"),
]

FIRST_NAMES = [
    "Иван",
    "Алексей",
    "Дмитрий",
    "Сергей",
    "Андрей",
    "Михаил",
    "Никита",
    "Павел",
    "Артём",
    "Максим",
    "Кирилл",
    "Егор",
    "Олег",
    "Виктор",
    "Роман",
]
LAST_NAMES = [
    "Петров",
    "Сидоров",
    "Козлов",
    "Новиков",
    "Морозов",
    "Волков",
    "Соколов",
    "Лебедев",
    "Кузнецов",
    "Попов",
    "Васильев",
    "Смирнов",
    "Иванов",
    "Фёдоров",
    "Медведев",
]


class Command(BaseCommand):
    help = "Создать 10 клубов, игроков и сезон с расписанием (v0.1)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Удалить существующие игровые данные перед сидом",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            from game.models import Fixture, Match, MatchdayRun

            MatchdayRun.objects.all().delete()
            Match.objects.all().delete()
            Fixture.objects.all().delete()
            Standing.objects.all().delete()
            Season.objects.all().delete()
            Player.objects.all().delete()
            Club.objects.all().delete()
            self.stdout.write("Данные очищены")

        if Season.objects.filter(is_active=True).exists():
            self.stdout.write(self.style.WARNING("Активный сезон уже есть — пропуск"))
            return

        rng = random.Random(42)
        clubs: list[Club] = []
        for i, (name, short) in enumerate(CLUB_DATA):
            club = Club.objects.create(
                name=name,
                short_name=short,
                is_player_controlled=(i == 0),
                formation="4-4-2",
                budget=rng.randint(3_000_000, 12_000_000),
            )
            clubs.append(club)
            self._create_squad(club, rng)
            club.lineup_player_ids = default_lineup(club)
            club.save(update_fields=["lineup_player_ids"])

        season = Season.objects.create(
            name="Премьер-лига 2025/26",
            is_active=True,
            current_matchday=1,
            next_simulation_at=compute_next_simulation_at(),
        )
        for club in clubs:
            Standing.objects.create(season=season, club=club)

        generate_round_robin(clubs, season)
        ensure_season_schedule(season)

        self.stdout.write(
            self.style.SUCCESS(
                f"Сид готов: {len(clubs)} клубов, сезон «{season.name}», "
                f"туров {season.total_matchdays}, следующий матч-день: {season.next_simulation_at}"
            )
        )

    def _create_squad(self, club: Club, rng: random.Random) -> None:
        positions = (
            ["GK"] * 2
            + ["DEF"] * 6
            + ["MID"] * 6
            + ["FWD"] * 4
        )
        for pos in positions:
            overall = max(55, min(88, rng.gauss(72, 6)))
            Player.objects.create(
                club=club,
                name=f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}",
                position=pos,
                age=rng.randint(19, 32),
                overall=int(overall),
            )
