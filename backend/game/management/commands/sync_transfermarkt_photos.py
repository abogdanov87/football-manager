from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from game.models import Player
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
from game.transfermarkt.photos import save_portrait

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "transfermarkt"


class Command(BaseCommand):
    help = (
        "Download player portraits from Transfermarkt squad pages for existing DB players "
        "(does not re-import stats)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--fixture-dir",
            type=str,
            default="",
            help="Use saved HTML fixtures (epl.html + {crest_slug}_kader.html)",
        )
        parser.add_argument(
            "--base-url",
            default=DEFAULT_BASE_URL,
            help="Transfermarkt base URL",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Re-download even if file already exists",
        )

    def handle(self, *args, **options):
        fixture_dir = options["fixture_dir"].strip()
        base_url = options["base_url"].rstrip("/")
        force = options["force"]

        if not Player.objects.filter(transfermarkt_id__isnull=False).exists():
            raise CommandError("No players with transfermarkt_id — run import_transfermarkt_epl first")

        if fixture_dir:
            comp_html = (Path(fixture_dir) / "epl.html").read_text(encoding="utf-8")
        else:
            comp_html = fetch_url(competition_url(base=base_url))

        from game.models import Club

        tm_clubs = parse_competition_clubs(comp_html)
        db_clubs = list(Club.objects.all())
        downloaded = 0
        updated = 0

        for tm in tm_clubs:
            crest_slug = crest_slug_from_tm(tm.slug)
            if not crest_slug:
                continue
            club = match_club_by_crest_slug(crest_slug, db_clubs)
            if club is None:
                continue

            if fixture_dir:
                kader_path = Path(fixture_dir) / f"{crest_slug}_kader.html"
                if not kader_path.is_file():
                    continue
                squad_html = kader_path.read_text(encoding="utf-8")
            else:
                url = squad_url(tm.slug, tm.verein_id, tm.season_id, base=base_url)
                try:
                    squad_html = fetch_url(url)
                except RuntimeError as exc:
                    self.stdout.write(self.style.WARNING(f"{club.name}: skip ({exc})"))
                    continue

            for row in parse_squad_page(squad_html):
                if not row.portrait_url:
                    continue
                player = Player.objects.filter(transfermarkt_id=row.transfermarkt_id).first()
                if player is None:
                    continue
                path = save_portrait(row.transfermarkt_id, row.portrait_url, force=force)
                if not path:
                    continue
                downloaded += 1
                if player.photo_url != path:
                    player.photo_url = path
                    player.save(update_fields=["photo_url"])
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Photos: {downloaded} files on disk, {updated} players updated in DB"
            )
        )
