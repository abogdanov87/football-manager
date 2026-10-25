from __future__ import annotations

from pathlib import Path
import urllib.error

from django.core.management.base import BaseCommand, CommandError
from game.fcratings.client import SEARCH_INDEX_URL, fetch_url
from game.fcratings.parser import FcFaceStats
from game.fcratings.parser import (
    derived_secondary_stats,
    parse_player_page,
    parse_search_index,
)
from game.models import Player

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "fcratings"


class Command(BaseCommand):
    help = "Update player FIFA face stats from fcratings.com (FC 27 ratings)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--fixture-index",
            type=str,
            default="",
            help="Use local search-index.json instead of live fetch",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report matches without writing to DB",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Max players to process (0 = all)",
        )
        parser.add_argument(
            "--index-only",
            action="store_true",
            help="Use search-index OVR only; estimate face stats (no per-player page fetch)",
        )

    def handle(self, *args, **options):
        fixture = options["fixture_index"].strip()
        dry_run = options["dry_run"]
        limit = int(options["limit"] or 0)
        index_only = options["index_only"]

        if fixture:
            index_raw = Path(fixture).read_text(encoding="utf-8")
        else:
            cache_path = FIXTURES / "search-index.json"
            try:
                self.stdout.write("Fetching FC Ratings search index…")
                index_raw = fetch_url(SEARCH_INDEX_URL)
                FIXTURES.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(index_raw, encoding="utf-8")
            except urllib.error.URLError as exc:
                if cache_path.is_file():
                    self.stdout.write(
                        self.style.WARNING(
                            f"Index fetch failed ({exc}); using {cache_path}"
                        )
                    )
                    index_raw = cache_path.read_text(encoding="utf-8")
                else:
                    raise CommandError(f"FC Ratings index fetch failed: {exc}") from exc

        by_slug = parse_search_index(index_raw)
        players = list(Player.objects.select_related("club").order_by("id"))
        if limit > 0:
            players = players[:limit]

        updated = 0
        skipped_no_index = 0
        failed = 0

        for player in players:
            slug = (player.transfermarkt_slug or "").strip()
            entry = by_slug.get(slug) if slug else None
            if entry is None:
                skipped_no_index += 1
                continue

            try:
                if index_only:
                    ovr = entry.overall
                    # Rough spread when page fetch is skipped (same OVR, generic shape).
                    stats = _estimate_from_overall(ovr, player.position)
                else:
                    html = fetch_url(entry.url)
                    stats = parse_player_page(
                        html,
                        game_position=player.position,
                        fallback_overall=entry.overall,
                    )
            except Exception as exc:
                if entry.overall and "chart data" in str(exc).lower():
                    stats = _estimate_from_overall(entry.overall, player.position)
                    self.stdout.write(
                        self.style.WARNING(
                            f"{player.name}: page blocked, estimated from OVR {entry.overall}"
                        )
                    )
                else:
                    failed += 1
                    self.stdout.write(self.style.WARNING(f"{player.name}: {exc}"))
                    continue

            mentality, injury = derived_secondary_stats(
                stats.overall, stats.pas, stats.dri, stats.phy
            )

            if dry_run:
                self.stdout.write(
                    f"{player.name}: OVR {stats.overall} "
                    f"PAC {stats.pac} SHO {stats.sho} PAS {stats.pas} "
                    f"DRI {stats.dri} DEF {stats.defending} PHY {stats.phy}"
                )
                updated += 1
                continue

            player.overall = stats.overall
            player.pac = stats.pac
            player.sho = stats.sho
            player.pas = stats.pas
            player.dri = stats.dri
            player.defending = stats.defending
            player.phy = stats.phy
            player.aerial = stats.aerial
            player.mentality = mentality
            player.injury_resistance = injury
            player.save(
                update_fields=[
                    "overall",
                    "pac",
                    "sho",
                    "pas",
                    "dri",
                    "defending",
                    "phy",
                    "aerial",
                    "mentality",
                    "injury_resistance",
                ]
            )
            updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"FC Ratings sync: updated={updated}, "
                f"not_in_index={skipped_no_index}, failed={failed}"
                + (" (dry-run)" if dry_run else "")
            )
        )


def _estimate_from_overall(ovr: int, position: str) -> FcFaceStats:
    base = ovr
    if position == "GK":
        return FcFaceStats(
            pac=base - 5,
            sho=base - 2,
            pas=base - 8,
            dri=base + 2,
            defending=base - 10,
            phy=base,
            aerial=base,
            overall=ovr,
        )
    if position == "DEF":
        return FcFaceStats(
            pac=base - 4,
            sho=base - 12,
            pas=base - 4,
            dri=base - 6,
            defending=base + 4,
            phy=base + 2,
            aerial=base + 2,
            overall=ovr,
        )
    if position == "FWD":
        return FcFaceStats(
            pac=base + 2,
            sho=base + 4,
            pas=base - 2,
            dri=base + 2,
            defending=base - 14,
            phy=base,
            aerial=base - 4,
            overall=ovr,
        )
    return FcFaceStats(
        pac=base,
        sho=base,
        pas=base + 2,
        dri=base + 2,
        defending=base - 6,
        phy=base,
        aerial=base - 6,
        overall=ovr,
    )
