from pathlib import Path

from django.test import SimpleTestCase

from game.transfermarkt.attributes import (
    EUR_TO_USD_RATE,
    compute_player_attributes,
    market_value_to_usd,
    parse_market_value_eur,
    tm_position_to_game_position,
)
from game.transfermarkt.parser import parse_competition_clubs, parse_squad_page
from game.transfermarkt.transliterate import transliterate_name

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "transfermarkt"


class TransfermarktParserTests(SimpleTestCase):
    def test_parse_epl_clubs_fixture(self):
        html = (FIXTURES / "epl.html").read_text(encoding="utf-8")
        clubs = parse_competition_clubs(html)
        self.assertEqual(len(clubs), 20)
        slugs = {c.slug for c in clubs}
        self.assertIn("manchester-city", slugs)
        self.assertIn("arsenal-fc", slugs)

    def test_parse_arsenal_squad_fixture(self):
        html = (FIXTURES / "arsenal_kader.html").read_text(encoding="utf-8")
        players = parse_squad_page(html)
        self.assertGreaterEqual(len(players), 20)
        raya = next(p for p in players if p.transfermarkt_id == 262749)
        self.assertEqual(raya.name_latin, "David Raya")
        self.assertEqual(raya.tm_position, "Goalkeeper")
        self.assertEqual(raya.market_value_eur, 30_000_000)


class TransfermarktAttributeTests(SimpleTestCase):
    def test_market_value_parsing(self):
        self.assertEqual(parse_market_value_eur("€30.00m"), 30_000_000)
        self.assertEqual(parse_market_value_eur("€500k"), 500_000)
        self.assertEqual(parse_market_value_eur("-"), 0)

    def test_usd_conversion(self):
        self.assertEqual(
            market_value_to_usd(1_000_000, rate=EUR_TO_USD_RATE),
            1_080_000,
        )

    def test_attribute_heuristic_deterministic(self):
        attrs = compute_player_attributes("Centre-Forward", 27, 50_000_000, seed=42)
        again = compute_player_attributes("Centre-Forward", 27, 50_000_000, seed=42)
        self.assertEqual(attrs, again)
        self.assertGreater(attrs["sho"], attrs["defending"])
        self.assertTrue(1 <= attrs["overall"] <= 99)

    def test_position_mapping(self):
        self.assertEqual(tm_position_to_game_position("Goalkeeper"), "GK")
        self.assertEqual(tm_position_to_game_position("Centre-Back"), "DEF")
        self.assertEqual(tm_position_to_game_position("Central Midfield"), "MID")
        self.assertEqual(tm_position_to_game_position("Left Winger"), "FWD")


class TransliterationTests(SimpleTestCase):
    def test_known_names(self):
        self.assertIn("д", transliterate_name("David Raya").lower())
        self.assertTrue(transliterate_name("Erling Haaland"))
