from django.test import SimpleTestCase

from game.fcratings.parser import (
    face_stats_from_chart,
    parse_chart_values,
    parse_overall_from_html,
    parse_player_page,
    parse_search_index,
    slug_from_fc_url,
)

MBAPPE_SNIPPET = """
<meta name="description" content="Kylian Mbappé is rated 91 overall in FC 27." />
labels: ["PAC","SHO","PAS","DRI","DEF","PHY"],
data: [96,91,80,92,29,76]
"""

COURTOIS_SNIPPET = """
<meta name="description" content="Thibaut Courtois is rated 90 overall in FC 27." />
labels: ["PAC","SHO","PAS","DRI","DEF","PHY","GK"],
data: [87,89,78,90,46,90,87]
"""


class FcRatingsParserTests(SimpleTestCase):
    def test_slug_from_url(self):
        self.assertEqual(
            slug_from_fc_url("https://www.fcratings.com/bart-verbruggen-258498"),
            "bart-verbruggen",
        )

    def test_parse_index_entry(self):
        raw = """[
          {"t":"player","n":"Bart Verbruggen","s":"Brighton",
           "u":"https://www.fcratings.com/bart-verbruggen-258498","r":81}
        ]"""
        by_slug = parse_search_index(raw)
        self.assertIn("bart-verbruggen", by_slug)
        self.assertEqual(by_slug["bart-verbruggen"].overall, 81)

    def test_parse_outfield_page(self):
        self.assertEqual(parse_overall_from_html(MBAPPE_SNIPPET), 91)
        self.assertEqual(parse_chart_values(MBAPPE_SNIPPET), [96, 91, 80, 92, 29, 76])
        stats = parse_player_page(MBAPPE_SNIPPET, game_position="FWD", fallback_overall=90)
        self.assertEqual(stats.overall, 91)
        self.assertEqual(stats.pac, 96)
        self.assertEqual(stats.sho, 91)

    def test_parse_gk_page(self):
        stats = parse_player_page(COURTOIS_SNIPPET, game_position="GK", fallback_overall=89)
        self.assertEqual(stats.overall, 90)
        self.assertEqual(stats.aerial, 87)

    def test_face_stats_from_chart_six(self):
        stats = face_stats_from_chart(
            [70, 71, 72, 73, 74, 75], overall=74, game_position="MID"
        )
        self.assertEqual(stats.defending, 74)
        self.assertEqual(stats.aerial, 74)
