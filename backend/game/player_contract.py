"""Contract display: wages and renewal status."""

from __future__ import annotations

from datetime import date
from typing import TypedDict

from .models import Player


class ContractMeta(TypedDict):
    contract_end_date: date | None
    years_remaining: int
    months_remaining: int
    renewal_status: str
    weekly_wage_usd: int
    yearly_wage_usd: int


def _age_years(player: Player, today: date) -> int:
    if player.date_of_birth:
        return (
            today.year
            - player.date_of_birth.year
            - (
                (today.month, today.day)
                < (player.date_of_birth.month, player.date_of_birth.day)
            )
        )
    return int(player.age)


def _age_factor(age: int) -> float:
    if age <= 21:
        return 0.75
    if age <= 23:
        return 0.88
    if age <= 28:
        return 1.0
    if age <= 32:
        return 0.92
    if age <= 35:
        return 0.78
    return 0.65


def _renewal_status(months_left: int) -> str:
    if months_left > 24:
        return "secure"
    if months_left >= 12:
        return "monitor"
    return "urgent"


def compute_contract_meta(
    player: Player,
    *,
    today: date | None = None,
    season_goals: int = 0,
    season_assists: int = 0,
) -> ContractMeta:
    today = today or date.today()
    end = player.contract_end_date
    years = months = 0
    if end:
        if end >= today:
            months = (end.year - today.year) * 12 + (end.month - today.month)
            if end.day < today.day:
                months -= 1
            months = max(0, months)
            years = months // 12
            months = months % 12
    months_total = years * 12 + months if end and end >= today else 0

    age = _age_years(player, today)
    mv = max(player.market_value_usd, 50_000)
    overall_scale = 0.65 + player.overall / 200.0
    form_scale = 0.85 + min(max(player.form, 0.75), 1.2) * 0.12
    contrib = season_goals + season_assists * 0.6
    perf_scale = 1.0 + min(contrib, 20) * 0.012

    weekly = int(
        (mv / 52.0) * 0.00045 * _age_factor(age) * overall_scale * form_scale * perf_scale
    )
    weekly = max(weekly, 1_000)

    return ContractMeta(
        contract_end_date=end,
        years_remaining=years,
        months_remaining=months,
        renewal_status=_renewal_status(months_total),
        weekly_wage_usd=weekly,
        yearly_wage_usd=weekly * 52,
    )
