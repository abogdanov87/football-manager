from pathlib import Path

from django.core.management.base import BaseCommand

from game.models import Player, PlayerCareerEntry
from game.transfermarkt.career import parse_transfer_history


class Command(BaseCommand):
    help = "Import Transfermarkt career rows from profile HTML fixtures."

    def add_arguments(self, parser):
        parser.add_argument(
            "--fixture-dir",
            type=str,
            default="game/fixtures/transfermarkt/profiles",
        )

    def handle(self, *args, **options):
        base = Path(options["fixture_dir"])
        if not base.is_dir():
            self.stderr.write(f"Missing fixture dir: {base}")
            return
        imported = 0
        for player in Player.objects.exclude(transfermarkt_id=None):
            path = base / f"{player.transfermarkt_id}.html"
            if not path.is_file():
                continue
            html_text = path.read_text(encoding="utf-8", errors="replace")
            rows = parse_transfer_history(html_text)
            if not rows:
                continue
            if PlayerCareerEntry.objects.filter(
                player=player, source=PlayerCareerEntry.Source.TRANSFERMARKT
            ).exists():
                continue
            for row in rows:
                PlayerCareerEntry.objects.create(
                    player=player,
                    club_name=row.club_name,
                    from_date=row.from_date,
                    to_date=row.to_date,
                    source=PlayerCareerEntry.Source.TRANSFERMARKT,
                )
                imported += 1
        self.stdout.write(self.style.SUCCESS(f"Imported {imported} career rows."))
