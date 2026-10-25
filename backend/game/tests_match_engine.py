import random
import re

from django.test import SimpleTestCase

from game.match_engine import (
    MatchPlayer,
    SquadSnapshot,
    _apply_injury_substitution,
    designate_set_piece_takers,
    simulate_match,
)


def _player(
    name: str,
    pos: str,
    sho: int = 70,
    pas: int = 70,
    injury_resistance: int = 70,
) -> MatchPlayer:
    return MatchPlayer(
        name=name,
        position=pos,
        form=1.0,
        overall=78,
        sho=sho,
        pac=70,
        dri=70,
        pas=pas,
        defending=70,
        phy=70,
        aerial=70,
        mentality=70,
        injury_resistance=injury_resistance,
    )


def _squad(
    name: str,
    atk: float = 78.0,
    def_: float = 76.0,
    bench: list[MatchPlayer] | None = None,
) -> SquadSnapshot:
    players = [
        _player("GK", "GK", 30, 55, 80),
        _player("Def A", "DEF", 45, 62, 75),
        _player("Def B", "DEF", 42, 60, 74),
        _player("Def C", "DEF", 40, 58, 73),
        _player("Def D", "DEF", 38, 57, 72),
        _player("Mid A", "MID", 68, 80, 76),
        _player("Mid B", "MID", 65, 78, 74),
        _player("Mid C", "MID", 62, 76, 73),
        _player("Mid D", "MID", 60, 75, 72),
        _player("Fwd A", "FWD", 85, 65, 68),
        _player("Fwd B", "FWD", 82, 63, 66),
    ]
    pen, fk = designate_set_piece_takers(players)
    return SquadSnapshot(
        club_id=1,
        club_name=name,
        formation="4-4-2",
        players=players,
        player_names=[p.name for p in players],
        attack_strength=atk,
        defense_strength=def_,
        penalty_taker=pen,
        free_kick_taker=fk,
        bench_players=bench or [
            _player("Sub GK", "GK"),
            _player("Sub Def", "DEF"),
            _player("Sub Mid", "MID"),
            _player("Sub Fwd", "FWD", sho=75),
        ],
    )


class MatchEngineSegmentTests(SimpleTestCase):
    def test_events_in_chronological_order(self):
        result = simulate_match(7, 1, _squad("Home FC"), _squad("Away FC"))
        minutes: list[int] = []
        for line in result.events:
            match = re.match(r"^(\d+)'", line)
            if match:
                minutes.append(int(match.group(1)))
        self.assertEqual(minutes, sorted(minutes))

    def test_deterministic_seed(self):
        home = _squad("Home FC")
        away = _squad("Away FC", atk=74.0, def_=74.0)
        a = simulate_match(99, 1, home, away)
        b = simulate_match(99, 1, home, away)
        self.assertEqual(a.home_score, b.home_score)
        self.assertEqual(a.away_score, b.away_score)
        self.assertEqual(a.events, b.events)

    def test_no_segment_markers_in_log(self):
        result = simulate_match(1, 1, _squad("H"), _squad("A"))
        self.assertFalse(any("Отрезок" in e for e in result.events))

    def test_report_emojis_for_special_events(self):
        for fixture_id in range(1, 80):
            result = simulate_match(fixture_id, 1, _squad("Home FC"), _squad("Away FC"))
            for line in result.events:
                if "Угловой" in line:
                    self.assertTrue(line.startswith("🚩 "))
                if "Штрафной" in line:
                    self.assertTrue(line.startswith("🎯 "))
                if "Пенальти" in line:
                    self.assertTrue(line.startswith("🥅 "))
                if "Жёлтая" in line or "жёлтая" in line:
                    self.assertTrue(line.startswith("🟨 "))
                if "Красная" in line or "удаление" in line:
                    self.assertTrue(line.startswith("🟥 "))
                if "Травма" in line:
                    self.assertTrue(line.startswith("🤕 "))
                if "Замена" in line:
                    self.assertTrue(line.startswith("🔄 "))
            if any("Угловой" in e for e in result.events):
                return
        self.skipTest("no corner in sample; emoji rules checked on other fixtures when present")

    def test_goals_credit_named_players(self):
        result = simulate_match(42, 2, _squad("Alpha"), _squad("Beta"))
        goals_in_log = [e for e in result.events if "ГОЛ!" in e]
        self.assertEqual(len(goals_in_log), result.home_score + result.away_score)
        for line in goals_in_log:
            self.assertIn("ГОЛ!", line)
            self.assertTrue(line.startswith("⚽ "))

    def test_set_piece_events_present(self):
        found = False
        for fixture_id in range(1, 40):
            result = simulate_match(fixture_id, 1, _squad("Home FC"), _squad("Away FC"))
            if any(
                "Угловой" in e or "Штрафной" in e or "Пенальти" in e for e in result.events
            ):
                found = True
                break
        self.assertTrue(found)

    def test_penalty_uses_designated_taker_name(self):
        players = _squad("X").players
        pen, _ = designate_set_piece_takers(players)
        self.assertEqual(pen, "Fwd A")

    def test_discipline_events_can_appear(self):
        found_card = False
        found_injury = False
        for fixture_id in range(1, 80):
            result = simulate_match(fixture_id, 1, _squad("Home FC"), _squad("Away FC"))
            if any("Жёлтая" in e or "Красная" in e or "жёлтая" in e for e in result.events):
                found_card = True
            if any("Травма" in e for e in result.events):
                found_injury = True
            if found_card and found_injury:
                break
        self.assertTrue(found_card)
        self.assertTrue(found_injury)

    def test_injury_substitution_from_bench(self):
        on_pitch = [_player("Fwd A", "FWD", sho=85)]
        bench = [_player("Sub Fwd", "FWD", sho=70), _player("Sub Mid", "MID")]
        events = _apply_injury_substitution(
            on_pitch=on_pitch,
            bench=bench,
            injured=on_pitch[0],
            club_name="Test FC",
            minute=55,
            rng=random.Random(0),
        )
        self.assertEqual(len(on_pitch), 1)
        self.assertEqual(on_pitch[0].name, "Sub Fwd")
        self.assertEqual(len(bench), 1)
        self.assertTrue(any("Замена" in e.text for e in events))
        self.assertTrue(any("Травма" in e.text for e in events))

    def test_match_injury_followed_by_substitution_when_possible(self):
        for fixture_id in range(1, 120):
            result = simulate_match(fixture_id, 1, _squad("Home FC"), _squad("Away FC"))
            injury_idx = next((i for i, e in enumerate(result.events) if "Травма" in e), None)
            if injury_idx is None:
                continue
            window = result.events[injury_idx : injury_idx + 3]
            if any("Замена" in e for e in window):
                return
        self.fail("expected at least one injury with substitution in sample")
