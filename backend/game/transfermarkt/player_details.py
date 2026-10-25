"""Apply Transfermarkt player detail payloads to ORM instances."""

from __future__ import annotations

from game.models import Player

from .dates import age_from_dob
from .profile import TMPlayerDetails, resolve_contract_end


def apply_tm_details_to_player(
    player: Player,
    details: TMPlayerDetails,
    *,
    transfermarkt_id: int,
) -> None:
    if details.date_of_birth:
        player.date_of_birth = details.date_of_birth
        player.age = age_from_dob(details.date_of_birth)
    if details.nationalities:
        player.nationality_countries = details.nationalities
    player.contract_end_date = resolve_contract_end(
        details.contract_end_date, transfermarkt_id
    )
