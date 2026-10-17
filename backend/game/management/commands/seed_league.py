import random

from django.core.management.base import BaseCommand
from django.db import transaction

from game.models import Club, Competition, Player, Season, Standing
from game.scheduler import compute_next_simulation_at, ensure_season_schedule
from game.services import default_lineup, generate_round_robin

# АПЛ — 20 клубов, сезон 2026/27. Состав как прокси 2025/26 до официального списка.
# `name` — русское отображаемое имя (API/UI); slug только для crest_url (английский).
# slug → name: arsenal→Арсенал, aston-villa→Астон Вилла, afc-bournemouth→Борнмут,
# brentford→Брентфорд, brighton→Брайтон, chelsea→Челси, crystal-palace→Кристал Пэлас,
# everton→Эвертон, fulham→Фулхэм, ipswich-town→Ипсвич, leicester-city→Лестер,
# liverpool→Ливерпуль, manchester-city→Манчестер Сити, manchester-united→Манчестер Юнайтед,
# newcastle-united→Ньюкасл Юнайтед, nottingham-forest→Ноттингем Форест,
# southampton→Саутгемптон, tottenham-hotspur→Тоттенхэм, west-ham-united→Вест Хэм,
# wolverhampton-wanderers→Вулверхэмптон
CLUB_DATA: list[tuple[str, str, str]] = [
    ("Арсенал", "ARS", "arsenal"),
    ("Астон Вилла", "AVL", "aston-villa"),
    ("Борнмут", "BOU", "afc-bournemouth"),
    ("Брентфорд", "BRE", "brentford"),
    ("Брайтон", "BHA", "brighton"),
    ("Челси", "CHE", "chelsea"),
    ("Кристал Пэлас", "CRY", "crystal-palace"),
    ("Эвертон", "EVE", "everton"),
    ("Фулхэм", "FUL", "fulham"),
    ("Ипсвич", "IPS", "ipswich-town"),
    ("Лестер", "LEI", "leicester-city"),
    ("Ливерпуль", "LIV", "liverpool"),
    ("Манчестер Сити", "MCI", "manchester-city"),
    ("Манчестер Юнайтед", "MUN", "manchester-united"),
    ("Ньюкасл Юнайтед", "NEW", "newcastle-united"),
    ("Ноттингем Форест", "NFO", "nottingham-forest"),
    ("Саутгемптон", "SOU", "southampton"),
    ("Тоттенхэм", "TOT", "tottenham-hotspur"),
    ("Вест Хэм", "WHU", "west-ham-united"),
    ("Вулверхэмптон", "WOL", "wolverhampton-wanderers"),
]

COMPETITION_NAME = "Премьер-лига"
COMPETITION_SLUG = "premier-league"
COMPETITION_LOGO_URL = "/crests/competitions/premier-league.png"
SEASON_DISPLAY_NAME = "Премьер-лига 2026/27"

FIRST_NAMES = [
    "Иван",
    "Дмитрий",
    "Александр",
    "Максим",
    "Сергей",
    "Андрей",
    "Алексей",
    "Михаил",
    "Артём",
    "Николай",
    "Павел",
    "Роман",
    "Егор",
    "Владимир",
    "Константин",
    "Илья",
    "Кирилл",
    "Денис",
    "Виктор",
    "Глеб",
]
LAST_NAMES = [
    "Иванов",
    "Смирнов",
    "Кузнецов",
    "Попов",
    "Васильев",
    "Петров",
    "Соколов",
    "Михайлов",
    "Новиков",
    "Фёдоров",
    "Морозов",
    "Волков",
    "Алексеев",
    "Лебедев",
    "Семёнов",
    "Егоров",
    "Павлов",
    "Козлов",
    "Степанов",
    "Николаев",
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
