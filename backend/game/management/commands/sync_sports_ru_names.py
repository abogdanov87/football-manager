from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from game.models import Club, Player
from game.sports_ru.client import club_squad_url, fetch_url
from game.sports_ru.clubs import sports_club_slug_from_crest_url
from game.sports_ru.match import match_player_to_sports_ru
from game.sports_ru.parser import parse_club_squad_athletes

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "sports_ru"


class Command(BaseCommand):
    help = (
        "Match players to Sports.ru APL squads and set Russian names "
        "as on sports.ru (https://www.sports.ru/football/tournament/premier-league/table/)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--fixture-dir",
            type=str,
            default="",
            help="Use {sports_club_slug}_squad.html instead of live HTTP",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report matches without saving",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        fixture_dir = options["fixture_dir"].strip()
        dry_run = options["dry_run"]

        updated = 0
        matched = 0
        unmatched: list[str] = []

        for club in Club.objects.order_by("name"):
            sports_slug = sports_club_slug_from_crest_url(club.crest_url)
            if not sports_slug:
                self.stdout.write(
                    self.style.WARNING(f"Skip {club.name}: no Sports.ru club mapping")
                )
                continue

            if fixture_dir:
                path = Path(fixture_dir) / f"{sports_slug}_squad.html"
                if not path.is_file():
                    self.stdout.write(
                        self.style.WARNING(f"Skip {club.name}: no fixture {path.name}")
                    )
                    continue
                html = path.read_text(encoding="utf-8")
            else:
                url = club_squad_url(sports_slug)
                try:
                    html = fetch_url(url)
                except RuntimeError as exc:
                    fallback = FIXTURES_DIR / f"{sports_slug}_squad.html"
                    if fallback.is_file():
                        self.stdout.write(
                            self.style.WARNING(
                                f"{club.name}: live fetch failed ({exc}); using fixture"
                            )
                        )
                        html = fallback.read_text(encoding="utf-8")
                    else:
                        self.stdout.write(
                            self.style.WARNING(f"Skip {club.name}: fetch failed ({exc})")
                        )
                        continue

            roster = parse_club_squad_athletes(html)
            if not roster:
                self.stdout.write(
                    self.style.WARNING(f"Skip {club.name}: no roster in Sports.ru HTML")
                )
                continue

            used: set[str] = set()
            club_matched = 0
            for player in Player.objects.filter(club=club).exclude(
                transfermarkt_slug=""
            ):
                athlete = match_player_to_sports_ru(
                    player.transfermarkt_slug, roster, used_slugs=used
                )
                if athlete is None:
                    unmatched.append(f"{club.name}: {player.name} ({player.transfermarkt_slug})")
                    continue
                used.add(athlete.slug)
                new_name = athlete.name.strip()
                matched += 1
                club_matched += 1
                if player.name == new_name:
                    continue
                if dry_run:
                    self.stdout.write(f"  {player.name} → {new_name}")
                else:
                    player.name = new_name
                    player.save(update_fields=["name"])
                    updated += 1

            self.stdout.write(f"{club.name}: {club_matched} matched (Sports.ru roster {len(roster)})")

        self.stdout.write(
            self.style.SUCCESS(
                f"Done — matched {matched}, renamed {updated}"
                + (" (dry-run)" if dry_run else "")
            )
        )
        if unmatched and len(unmatched) <= 40:
            self.stdout.write(self.style.WARNING("Unmatched:\n" + "\n".join(unmatched[:40])))
        elif unmatched:
            self.stdout.write(
                self.style.WARNING(f"Unmatched: {len(unmatched)} players (see logs)")
            )
