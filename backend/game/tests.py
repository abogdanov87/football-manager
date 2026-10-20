from django.test import TestCase

from game.formations import FORMATION_SPECS, formation_position_counts
from game.models import Club, Player
from game.serializers import TacticsUpdateSerializer
from game.services import default_lineup


class FormationCatalogTests(TestCase):
    def test_each_formation_has_eleven_slots(self):
        for code, spec in FORMATION_SPECS.items():
            counts = formation_position_counts(code)
            self.assertEqual(10, counts["DEF"] + counts["MID"] + counts["FWD"])
            self.assertEqual(1, counts["GK"])
            self.assertEqual(spec["def_"], counts["DEF"])
            self.assertEqual(spec["mid"], counts["MID"])
            self.assertEqual(spec["fwd"], counts["FWD"])
            self.assertEqual(11, sum(counts.values()))

    def test_tactics_serializer_accepts_all_formations(self):
        for code in FORMATION_SPECS:
            ser = TacticsUpdateSerializer(data={"formation": code, "lineup_player_ids": list(range(1, 12))})
            self.assertTrue(ser.is_valid(), f"{code}: {ser.errors}")

    def test_tactics_serializer_rejects_unknown_formation(self):
        ser = TacticsUpdateSerializer(
            data={"formation": "9-9-9", "lineup_player_ids": list(range(1, 12))}
        )
        self.assertFalse(ser.is_valid())


class DefaultLineupTests(TestCase):
    def test_default_lineup_respects_3_5_2(self):
        club = Club.objects.create(name="Test FC", short_name="TFC", formation="3-5-2")
        for i, pos in enumerate(
            ["GK"] * 2
            + ["DEF"] * 5
            + ["MID"] * 8
            + ["FWD"] * 5
        ):
            Player.objects.create(club=club, name=f"P{i}", position=pos, overall=80 - i)
        ids = default_lineup(club)
        players = {p.id: p for p in Player.objects.filter(id__in=ids)}
        by_pos = {"GK": 0, "DEF": 0, "MID": 0, "FWD": 0}
        for pid in ids:
            by_pos[players[pid].position] += 1
        self.assertEqual({"GK": 1, "DEF": 3, "MID": 5, "FWD": 2}, by_pos)
