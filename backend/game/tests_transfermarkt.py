from pathlib import Path

from django.test import SimpleTestCase

from game.transfermarkt.attributes import (
    EUR_TO_USD_RATE,
    compute_player_attributes,
    market_value_to_usd,
    parse_market_value_eur,
    tm_position_to_game_position,
)
from game.transfermarkt.photos import portrait_url_matches_player
from game.transfermarkt.lineup import (
    normalize_tm_formation,
    parse_final_formation_json,
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
        self.assertIn("portrait/medium/262749", raya.portrait_url)
        odegaard = next(p for p in players if p.transfermarkt_id == 316264)
        self.assertEqual(odegaard.name_latin, "Martin Ødegaard")
        self.assertEqual(odegaard.tm_position, "Attacking Midfield")

    def test_parse_arsenal_final_formation_fixture(self):
        raw = (FIXTURES / "arsenal_formation.json").read_text(encoding="utf-8")
        lineup = parse_final_formation_json(raw)
        self.assertIsNotNone(lineup)
        assert lineup is not None
        self.assertEqual(lineup.formation, "4-2-3-1")
        self.assertEqual(len(lineup.player_tm_ids), 11)
        self.assertIn(316264, lineup.player_tm_ids)

    def test_normalize_tm_formation(self):
        self.assertEqual(normalize_tm_formation("4-3-3 Attacking"), "4-3-3")
        self.assertEqual(normalize_tm_formation("garbage"), "4-4-2")

    def test_portrait_url_matches_player(self):
        self.assertTrue(
            portrait_url_matches_player(
                479999,
                "https://img.a.transfermarkt.technology/portrait/medium/479999-1761083931.jpg?lm=4711",
            )
        )
        self.assertFalse(
            portrait_url_matches_player(
                479999,
                "https://img.a.transfermarkt.technology/portrait/medium/316264-1782847069.jpg?lm=4711",
            )
        )


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

    def test_goalkeeper_fifa_style_attributes(self):
        attrs = compute_player_attributes("Goalkeeper", 32, 40_000_000, seed=7)
        self.assertGreater(attrs["defending"], attrs["sho"])
        self.assertGreater(attrs["phy"], attrs["sho"])
        self.assertGreater(attrs["dri"], attrs["pas"])
        self.assertGreater(attrs["overall"], 75)

    def test_position_mapping(self):
        self.assertEqual(tm_position_to_game_position("Goalkeeper"), "GK")
        self.assertEqual(tm_position_to_game_position("Centre-Back"), "DEF")
        self.assertEqual(tm_position_to_game_position("Central Midfield"), "MID")
        self.assertEqual(tm_position_to_game_position("Left Winger"), "FWD")


class TransliterationTests(SimpleTestCase):
    def test_known_names(self):
        self.assertIn("д", transliterate_name("David Raya").lower())
        self.assertTrue(transliterate_name("Erling Haaland"))
