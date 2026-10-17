import random

from django.core.management.base import BaseCommand
from django.db import transaction

from game.models import Club, Competition, Player, Season, Standing
from game.scheduler import compute_next_simulation_at, ensure_season_schedule
from game.services import default_lineup, generate_round_robin

# English Premier League — 20 clubs for season 2026/27.
# Lineup matches the 2025/26 PL composition as a proxy until the official
# start-of-season list is published (promotion/relegation from Championship).
# Slugs align with frontend/public/crests/clubs/<slug>.png (see crests README).
CLUB_DATA: list[tuple[str, str, str]] = [
    ("Arsenal", "ARS", "arsenal"),
    ("Aston Villa", "AVL", "aston-villa"),
    ("AFC Bournemouth", "BOU", "afc-bournemouth"),
    ("Brentford", "BRE", "brentford"),
    ("Brighton & Hove Albion", "BHA", "brighton"),
    ("Chelsea", "CHE", "chelsea"),
    ("Crystal Palace", "CRY", "crystal-palace"),
    ("Everton", "EVE", "everton"),
    ("Fulham", "FUL", "fulham"),
    ("Ipswich Town", "IPS", "ipswich-town"),
    ("Leicester City", "LEI", "leicester-city"),
    ("Liverpool", "LIV", "liverpool"),
    ("Manchester City", "MCI", "manchester-city"),
    ("Manchester United", "MUN", "manchester-united"),
    ("Newcastle United", "NEW", "newcastle-united"),
    ("Nottingham Forest", "NFO", "nottingham-forest"),
    ("Southampton", "SOU", "southampton"),
    ("Tottenham Hotspur", "TOT", "tottenham-hotspur"),
    ("West Ham United", "WHU", "west-ham-united"),
    ("Wolverhampton Wanderers", "WOL", "wolverhampton-wanderers"),
]

COMPETITION_NAME = "Premier League"
COMPETITION_SLUG = "premier-league"
COMPETITION_LOGO_URL = "/crests/competitions/premier-league.png"
SEASON_DISPLAY_NAME = "Премьер-лига 2026/27"

FIRST_NAMES = [
    "James",
    "Jack",
    "Harry",
    "George",
    "Charlie",
    "Thomas",
    "William",
    "Oliver",
    "Jacob",
    "Daniel",
    "Michael",
    "Benjamin",
    "Lucas",
    "Henry",
    "Alexander",
]
LAST_NAMES = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Taylor",
    "Davies",
    "Wilson",
    "Evans",
    "Thomas",
    "Roberts",
    "Walker",
    "Wright",
    "Thompson",
    "White",
    "Hughes",
]


def club_crest_url(slug: str) -> str:
    return f"/crests/clubs/{slug}.png"


class Command(BaseCommand):
    help = (
        "Создать соревнование Premier League, 20 клубов АПЛ, игроков и сезон 2026/27 "
        "с расписанием (v0.1)"
    )

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
            Competition.objects.all().delete()
            self.stdout.write("Данные очищены")

        if Season.objects.filter(is_active=True).exists():
            self.stdout.write(self.style.WARNING("Активный сезон уже есть — пропуск"))
            return

        competition, _ = Competition.objects.get_or_create(
            slug=COMPETITION_SLUG,
            defaults={
                "name": COMPETITION_NAME,
                "logo_url": COMPETITION_LOGO_URL,
            },
        )
        if not competition.logo_url:
            competition.logo_url = COMPETITION_LOGO_URL
            competition.save(update_fields=["logo_url"])

        rng = random.Random(42)
        clubs: list[Club] = []
        for i, (name, short, slug) in enumerate(CLUB_DATA):
            club = Club.objects.create(
                name=name,
                short_name=short,
                crest_url=club_crest_url(slug),
                is_player_controlled=(i == 0),
                formation="4-4-2",
                budget=rng.randint(3_000_000, 12_000_000),
            )
            clubs.append(club)
            self._create_squad(club, rng)
            club.lineup_player_ids = default_lineup(club)
            club.save(update_fields=["lineup_player_ids"])

        season = Season.objects.create(
            name=SEASON_DISPLAY_NAME,
            competition=competition,
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
                f"Сид готов: {competition.name} — {len(clubs)} клубов, сезон «{season.name}», "
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
