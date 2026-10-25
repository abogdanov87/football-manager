from datetime import date, timedelta

from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from game.match_engine import MatchPlayer, designate_set_piece_takers, simulate_match
from game.models import (
    Club,
    Competition,
    Fixture,
    Match,
    Player,
    PlayerCareerEntry,
    PlayerPositionMinuteLedger,
    PlayerSeasonStat,
    Season,
)
from game.player_contract import compute_contract_meta
from game.player_stats import (
    BOOTSTRAP_MINUTES,
    POSITION_WINDOW_MINUTES,
    bootstrap_position_minutes,
    favorite_positions_top3,
)
from game.services import simulate_fixture
from game.transfermarkt.career import parse_transfer_history


class ContractWageTests(SimpleTestCase):
    def test_yearly_is_weekly_times_52(self):
        p = Player(
            market_value_usd=10_000_000,
            overall=80,
            form=1.0,
            age=27,
            contract_end_date=date(2030, 6, 30),
        )
        meta = compute_contract_meta(p, today=date(2026, 11, 1))
        self.assertEqual(meta["yearly_wage_usd"], meta["weekly_wage_usd"] * 52)

    def test_short_contract_urgent(self):
        p = Player(
            market_value_usd=1_000_000,
            overall=70,
            contract_end_date=date(2027, 3, 1),
        )
        meta = compute_contract_meta(p, today=date(2026, 11, 1))
        self.assertEqual(meta["renewal_status"], "urgent")


class CareerParserTests(SimpleTestCase):
    def test_parse_transfer_history_ordered(self):
        html = """
        <h2>Transfer history</h2>
        <table>
        <tr class="bg_Weiß">
          <td class="zentriert">01/07/2021</td>
          <td class="zentriert">-</td>
          <td><a href="/arsenal-fc/startseite/verein/11" title="Arsenal FC">Arsenal</a></td>
        </tr>
        </table>
        """
        rows = parse_transfer_history(html)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].club_name, "Arsenal FC")
        self.assertEqual(rows[0].from_date, date(2021, 7, 1))


class PositionMinutesTests(TestCase):
    def setUp(self):
        comp = Competition.objects.create(name="EPL", slug="epl")
        self.season = Season.objects.create(name="2026/27", competition=comp)
        self.club = Club.objects.create(name="Test FC", short_name="TFC", is_player_controlled=True)
        self.player = Player.objects.create(
            club=self.club, name="Hero", position="MID", overall=80
        )

    def test_bootstrap_once(self):
        self.assertTrue(bootstrap_position_minutes(self.player))
        self.player.refresh_from_db()
        self.assertTrue(self.player.position_minutes_bootstrapped)
        self.assertFalse(bootstrap_position_minutes(self.player))
        self.assertEqual(
            PlayerPositionMinuteLedger.objects.filter(player=self.player).count(), 1
        )
        row = PlayerPositionMinuteLedger.objects.get(player=self.player)
        self.assertEqual(row.minutes, BOOTSTRAP_MINUTES)

    def test_rolling_window_trims_old_minutes(self):
        away = Club.objects.create(name="Away", short_name="AWY")
        fix = Fixture.objects.create(
            season=self.season,
            matchday=1,
            home_club=self.club,
            away_club=away,
        )
        match = Match.objects.create(fixture=fix, home_score=0, away_score=0)
        chunks = POSITION_WINDOW_MINUTES // 90 + 5
        for i in range(chunks):
            PlayerPositionMinuteLedger.objects.create(
                player=self.player,
                position_code="MID",
                minutes=90,
                source=PlayerPositionMinuteLedger.Source.MATCH,
                match=match,
            )
        tops = favorite_positions_top3(self.player.id)
        self.assertTrue(tops)
        self.assertLessEqual(sum(t["minutes"] for t in tops), POSITION_WINDOW_MINUTES)


class MatchStatsPersistenceTests(TestCase):
    def setUp(self):
        comp = Competition.objects.create(name="EPL", slug="epl2")
        self.season = Season.objects.create(name="2026/27", competition=comp)
        self.home = Club.objects.create(name="Home", short_name="HOM")
        self.away = Club.objects.create(name="Away", short_name="AWY")
        self.p = Player.objects.create(club=self.home, name="Striker", position="FWD", overall=85)
        for i in range(11):
            Player.objects.create(
                club=self.home, name=f"H{i}", position="MID" if i else "GK", overall=70
            )
        for i in range(11):
            Player.objects.create(club=self.away, name=f"A{i}", position="MID" if i else "GK", overall=70)

    def test_simulate_fixture_creates_appearances(self):
        fix = Fixture.objects.create(
            season=self.season, matchday=1, home_club=self.home, away_club=self.away
        )
        simulate_fixture(fix)
        self.assertTrue(
            PlayerSeasonStat.objects.filter(season=self.season, player=self.p).exists()
            or PlayerSeasonStat.objects.filter(season=self.season).exists()
        )


class SetPieceDesignationTests(SimpleTestCase):
    def test_designated_penalty_taker(self):
        players = [
            MatchPlayer("A", "FWD", 1.0, 70, 60, 50, 50, 50, 50, 50, 50, 50, 50),
            MatchPlayer("B", "FWD", 1.0, 70, 99, 50, 50, 50, 50, 50, 50, 50, 50),
        ]
        pen, _ = designate_set_piece_takers(players, penalty_name="A")
        self.assertEqual(pen, "A")


class PlayerApiTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        from rest_framework.test import APIClient

        from game.authentication import hash_token_key
        from game.models import AuthToken

        User = get_user_model()
        comp = Competition.objects.create(name="EPL", slug="epl-api")
        self.season = Season.objects.create(name="2026/27", competition=comp, is_active=True)
        self.user = User.objects.create_user(username="me@test.com", email="me@test.com")
        self.club = Club.objects.create(
            name="My Club",
            short_name="MYC",
            is_player_controlled=True,
            owner=self.user,
        )
        self.other = Club.objects.create(name="Other", short_name="OTH")
        self.mine = Player.objects.create(club=self.club, name="Mine", position="MID", overall=80)
        self.theirs = Player.objects.create(club=self.other, name="Theirs", position="MID", overall=80)
        self.raw = "profile-test-token"
        AuthToken.objects.create(
            user=self.user,
            key_hash=hash_token_key(self.raw),
            expires_at=timezone.now() + timedelta(days=1),
        )
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.raw}")

    def test_own_player_detail_ok(self):
        res = self.client.get(f"/api/players/{self.mine.id}/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("contract", res.json())

    def test_other_club_forbidden(self):
        res = self.client.get(f"/api/players/{self.theirs.id}/")
        self.assertIn(res.status_code, (403, 404))

    def test_anonymous_unauthorized(self):
        anon = APIClient()
        res = anon.get(f"/api/players/{self.mine.id}/")
        self.assertEqual(res.status_code, 401)
