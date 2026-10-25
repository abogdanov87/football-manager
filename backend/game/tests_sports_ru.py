from pathlib import Path

from django.test import SimpleTestCase

from game.sports_ru.match import match_player_to_sports_ru, match_score
from game.sports_ru.parser import parse_club_squad_athletes

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "sports_ru"


class SportsRuParserTests(SimpleTestCase):
    def test_parse_arsenal_squad_fixture(self):
        html = (FIXTURES / "arsenal_squad.html").read_text(encoding="utf-8")
        roster = parse_club_squad_athletes(html)
        self.assertGreaterEqual(len(roster), 20)
        by_slug = {p.slug: p.name for p in roster}
        self.assertEqual(by_slug.get("martin-odegaard"), "Мартин Эдегор")
        self.assertEqual(by_slug.get("eberechi-eze"), "Эберечи Эзе")

    def test_slug_matching(self):
        self.assertGreaterEqual(match_score("martin-odegaard", "martin-odegaard"), 100)
        self.assertGreaterEqual(match_score("gabriel-magalhaes", "gabriel-magalyaes"), 65)
        athlete = match_player_to_sports_ru(
            "eberechi-eze",
            parse_club_squad_athletes(
                (FIXTURES / "arsenal_squad.html").read_text(encoding="utf-8")
            ),
            used_slugs=set(),
        )
        self.assertIsNotNone(athlete)
        assert athlete is not None
        self.assertEqual(athlete.name, "Эберечи Эзе")
