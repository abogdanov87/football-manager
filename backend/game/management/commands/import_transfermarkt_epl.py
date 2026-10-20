from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from game.models import Club, Player
from game.services import default_lineup
from game.transfermarkt.attributes import (
    EUR_TO_USD_RATE,
    compute_player_attributes,
    market_value_to_usd,
    tm_position_to_game_position,
)
from game.transfermarkt.client import (
    DEFAULT_BASE_URL,
    competition_url,
    fetch_url,
    squad_url,
)
from game.transfermarkt.parser import (
    crest_slug_from_tm,
    match_club_by_crest_slug,
    parse_competition_clubs,
    parse_squad_page,
)
from game.transfermarkt.transliterate import transliterate_name

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "transfermarkt"


class Command(BaseCommand):
    help = (
        "Import Premier League squads from Transfermarkt (GB1): Russian names, "
        f"USD market values (EUR×{EUR_TO_USD_RATE}), FIFA-style attributes."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--fixture-dir",
            type=str,
            default="",
            help="Use saved HTML fixtures instead of live HTTP (epl.html + {crest_slug}_kader.html)",
        )
        parser.add_argument(
            "--base-url",
            default=DEFAULT_BASE_URL,
            help="Transfermarkt base URL (default: transfermarkt.co.uk)",
        )
        parser.add_argument(
            "--eur-usd",
            type=float,
            default=EUR_TO_USD_RATE,
            help=f"Fixed EUR→USD rate (default {EUR_TO_USD_RATE})",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and report without writing players",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        fixture_dir = options["fixture_dir"].strip()
        base_url = options["base_url"].rstrip("/")
        eur_usd = float(options["eur_usd"])
        dry_run = options["dry_run"]

        if fixture_dir:
            comp_html = self._read_fixture(Path(fixture_dir) / "epl.html")
        else:
            try:
                comp_html = fetch_url(competition_url(base=base_url))
                if len(comp_html) < 500:
                    raise RuntimeError("empty or blocked response")
            except RuntimeError as exc:
                fallback = FIXTURES_DIR / "epl.html"
                if fallback.is_file():
                    self.stdout.write(
                        self.style.WARNING(
                            f"Live competition fetch failed ({exc}); using {fallback}"
                        )
                    )
                    comp_html = fallback.read_text(encoding="utf-8")
                else:
                    raise CommandError(
                        f"Live fetch failed ({exc}). "
                        f"Save fixtures under {FIXTURES_DIR} and pass --fixture-dir."
                    ) from exc

        tm_clubs = parse_competition_clubs(comp_html)
        if len(tm_clubs) < 18:
            raise CommandError(f"Expected ~20 TM clubs, got {len(tm_clubs)}")

        db_clubs = list(Club.objects.all())
        if not db_clubs:
            raise CommandError("No clubs in DB — run seed_league first")

        imported_clubs = 0
        total_players = 0
        skipped: list[str] = []

        for tm in tm_clubs:
            crest_slug = crest_slug_from_tm(tm.slug)
            if not crest_slug:
                skipped.append(tm.slug)
                continue
            club = match_club_by_crest_slug(crest_slug, db_clubs)
            if club is None:
                skipped.append(f"{tm.slug}→{crest_slug} (no DB club)")
                continue

            if fixture_dir:
                kader_path = Path(fixture_dir) / f"{crest_slug}_kader.html"
                if not kader_path.is_file():
                    self.stdout.write(
                        self.style.WARNING(
                            f"Skipping {club.name}: no fixture {kader_path.name}"
                        )
                    )
                    continue
                squad_html = self._read_fixture(kader_path)
            else:
                url = squad_url(tm.slug, tm.verein_id, tm.season_id, base=base_url)
                try:
                    squad_html = fetch_url(url)
                    if len(squad_html) < 500:
                        raise RuntimeError("empty or blocked response")
                except RuntimeError as exc:
                    kader_path = FIXTURES_DIR / f"{crest_slug}_kader.html"
                    if kader_path.is_file():
                        self.stdout.write(
                            self.style.WARNING(
                                f"{club.name}: live squad failed ({exc}); using fixture"
                            )
                        )
                        squad_html = kader_path.read_text(encoding="utf-8")
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Skipping {club.name}: squad fetch failed ({exc})"
                            )
                        )
                        continue

            rows = parse_squad_page(squad_html)
            if not rows:
                self.stdout.write(
                    self.style.WARNING(f"No players parsed for {club.name} ({tm.slug})")
                )
                continue

            if dry_run:
                imported_clubs += 1
                total_players += len(rows)
                continue

            Player.objects.filter(club=club).delete()
            for row in rows:
                mv_eur = row.market_value_eur
                mv_usd = market_value_to_usd(mv_eur, rate=eur_usd)
                attrs = compute_player_attributes(
                    row.tm_position,
                    row.age,
                    mv_eur,
                    seed=row.transfermarkt_id,
                )
                player = Player(
                    club=club,
                    name=transliterate_name(row.name_latin),
                    position=tm_position_to_game_position(row.tm_position),
                    age=row.age,
                    form=1.0,
                    transfermarkt_id=row.transfermarkt_id,
                    transfermarkt_slug=row.transfermarkt_slug,
                    tm_position=row.tm_position,
                    market_value_usd=mv_usd,
                    pac=attrs["pac"],
                    sho=attrs["sho"],
                    pas=attrs["pas"],
                    dri=attrs["dri"],
                    defending=attrs["defending"],
                    phy=attrs["phy"],
                    aerial=attrs["aerial"],
                    mentality=attrs["mentality"],
                    injury_resistance=attrs["injury_resistance"],
                    overall=attrs["overall"],
                )
                player.save()

            club.lineup_player_ids = default_lineup(club)
            club.save(update_fields=["lineup_player_ids"])
            imported_clubs += 1
            total_players += len(rows)
            self.stdout.write(f"{club.name}: {len(rows)} players")

        if skipped:
            self.stdout.write(self.style.WARNING("Unmapped TM clubs: " + ", ".join(skipped)))

        self.stdout.write(
            self.style.SUCCESS(
                f"Import complete — clubs: {imported_clubs}, players: {total_players}, "
                f"EUR/USD={eur_usd}"
            )
        )

    def _read_fixture(self, path: Path) -> str:
        if not path.is_file():
            raise CommandError(f"Fixture not found: {path}")
        return path.read_text(encoding="utf-8")
