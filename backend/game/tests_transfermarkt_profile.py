from datetime import date
from pathlib import Path

from django.test import SimpleTestCase

from game.transfermarkt.dates import fallback_contract_end, parse_tm_date
from game.transfermarkt.parser import parse_squad_page
from game.transfermarkt.profile import resolve_contract_end

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "transfermarkt"


class TransfermarktProfileTests(SimpleTestCase):
    def test_parse_bruno_guimaraes_from_arsenal_kader(self):
        html = (FIXTURES / "arsenal_kader.html").read_text(encoding="utf-8")
        players = parse_squad_page(html)
        bruno = next(p for p in players if p.transfermarkt_id == 520624)
        self.assertEqual(bruno.date_of_birth, date(1997, 11, 16))
        self.assertEqual(bruno.contract_end_date, date(2030, 6, 30))
        self.assertTrue(any(n["name"] == "Brazil" for n in bruno.nationalities or []))
        self.assertTrue(
            any("flagge" in n["flag_url"] for n in bruno.nationalities or [])
        )

    def test_fallback_contract_deterministic(self):
        self.assertEqual(fallback_contract_end(520624), fallback_contract_end(520624))
        end = fallback_contract_end(1)
        self.assertGreater(end, date(2026, 11, 1))
        self.assertLessEqual(end.year, 2031)

    def test_resolve_contract_uses_fallback(self):
        self.assertEqual(
            resolve_contract_end(None, 42),
            fallback_contract_end(42),
        )
        self.assertEqual(
            resolve_contract_end(date(2030, 6, 30), 42),
            date(2030, 6, 30),
        )

    def test_parse_tm_date(self):
        self.assertEqual(parse_tm_date("16/11/1997 (28)"), date(1997, 11, 16))
