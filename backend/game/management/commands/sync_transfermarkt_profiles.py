from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from game.models import Club, Player
from game.transfermarkt.client import (
    DEFAULT_BASE_URL,
    competition_url,
    fetch_url,
    player_profile_url,
    squad_url,
)
from game.transfermarkt.parser import (
    crest_slug_from_tm,
    match_club_by_crest_slug,
    parse_competition_clubs,
    parse_squad_page,
)
from game.transfermarkt.player_details import apply_tm_details_to_player
from game.transfermarkt.profile import (
    TMPlayerDetails,
    parse_player_profile,
    resolve_contract_end,
)

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "transfermarkt"
PROFILE_FIXTURES = FIXTURES_DIR / "profiles"


class Command(BaseCommand):
    help = (
        "Sync date of birth, nationality (with flags) and contract end from "
        "Transfermarkt squad/profile pages."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--fixture-dir",
            type=str,
            default="",
            help="Use epl.html + {crest}_kader.html (and optional profiles/{tm_id}.html)",
        )
        parser.add_argument(
            "--base-url",
            default=DEFAULT_BASE_URL,
            help="Transfermarkt base URL",
        )
        parser.add_argument(
            "--fetch-profiles",
            action="store_true",
            help="Also fetch individual profile pages when squad row lacks data",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        fixture_dir = options["fixture_dir"].strip()
        base_url = options["base_url"].rstrip("/")
        fetch_profiles = options["fetch_profiles"]

        if fixture_dir:
            comp_html = (Path(fixture_dir) / "epl.html").read_text(encoding="utf-8")
        else:
            comp_html = fetch_url(competition_url(base=base_url))

        tm_clubs = parse_competition_clubs(comp_html)
        db_clubs = list(Club.objects.all())
        if not db_clubs:
            raise CommandError("No clubs in DB")

        updated = 0
        by_tm_id: dict[int, TMPlayerDetails] = {}

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
                except RuntimeError:
                    kader_path = FIXTURES_DIR / f"{crest_slug}_kader.html"
                    if kader_path.is_file():
                        squad_html = kader_path.read_text(encoding="utf-8")
                    else:
                        continue

            for row in parse_squad_page(squad_html):
                by_tm_id[row.transfermarkt_id] = TMPlayerDetails(
                    date_of_birth=row.date_of_birth,
                    nationalities=row.nationalities or [],
                    contract_end_date=row.contract_end_date,
                )

        for player in Player.objects.filter(transfermarkt_id__isnull=False):
            tm_id = player.transfermarkt_id
            assert tm_id is not None
            details = by_tm_id.get(tm_id)

            if details is None or (
                fetch_profiles
                and (not details.nationalities or not details.date_of_birth)
            ):
                details = self._load_profile_details(
                    player, base_url, fixture_dir, details
                )

            if details is None:
                details = TMPlayerDetails(
                    date_of_birth=player.date_of_birth,
                    nationalities=list(player.nationality_countries or []),
                    contract_end_date=player.contract_end_date,
                )

            apply_tm_details_to_player(player, details, transfermarkt_id=tm_id)
            player.save(
                update_fields=[
                    "date_of_birth",
                    "age",
                    "nationality_countries",
                    "contract_end_date",
                ]
            )
            updated += 1

        self.stdout.write(self.style.SUCCESS(f"Updated {updated} players"))

    def _load_profile_details(
        self,
        player: Player,
        base_url: str,
        fixture_dir: str,
        fallback: TMPlayerDetails | None,
    ) -> TMPlayerDetails | None:
        tm_id = player.transfermarkt_id
        slug = player.transfermarkt_slug
        if not tm_id or not slug:
            return fallback

        html = ""
        if fixture_dir:
            path = Path(fixture_dir) / "profiles" / f"{tm_id}.html"
            if path.is_file():
                html = path.read_text(encoding="utf-8")
        else:
            prof_path = PROFILE_FIXTURES / f"{tm_id}.html"
            if prof_path.is_file():
                html = prof_path.read_text(encoding="utf-8")
            else:
                url = player_profile_url(slug, tm_id, base=base_url)
                try:
                    html = fetch_url(url)
                except RuntimeError:
                    html = ""

        if not html or len(html) < 800:
            if fallback and not fallback.contract_end_date:
                fallback = TMPlayerDetails(
                    date_of_birth=fallback.date_of_birth,
                    nationalities=fallback.nationalities,
                    contract_end_date=resolve_contract_end(None, tm_id),
                )
            return fallback

        profile = parse_player_profile(html)
        if fallback:
            return TMPlayerDetails(
                date_of_birth=profile.date_of_birth or fallback.date_of_birth,
                nationalities=profile.nationalities or fallback.nationalities,
                contract_end_date=profile.contract_end_date
                or fallback.contract_end_date,
            )
        return profile
