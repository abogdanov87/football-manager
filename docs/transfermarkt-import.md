# Transfermarkt Premier League import

Command: `python manage.py import_transfermarkt_epl`

## Source

- Competition: [Premier League GB1](https://www.transfermarkt.co.uk/premier-league/startseite/wettbewerb/GB1)
- Default host: `transfermarkt.co.uk` (`.world` often blocks automated clients in cloud VMs)
- Squad pages: `/…/kader/verein/{id}/saison_id/{year}/plus/1`

## Behaviour

1. Loads the 20 clubs from the competition page (kader links).
2. Maps each TM slug → local crest slug (see `game/transfermarkt/parser.py`).
3. Replaces all `Player` rows for matched `Club` records.
4. Sets Russian `name` via deterministic transliteration (`transfermarkt_slug` + `transfermarkt_id` kept for updates).
5. Stores `market_value_usd` as integer dollars using a **fixed EUR→USD rate** (default **1.08**). Override with `--eur-usd`.
6. Derives FIFA-style attributes with `compute_player_attributes()` in `game/transfermarkt/attributes.py`.

## Attribute heuristic

Inputs: TM detailed position, age, market value (EUR).

- Base rating: `32 + ln(max(eur, 50k)) × 3.35`, clamped to ~40–91.
- Age tweaks: younger → higher PAC; peak years → slightly higher PHY.
- Position templates shift PAC/SHO/PAS/DRI/DEF/PHY/aerial/mentality/injury_resistance.
- Small jitter is **deterministic** from `transfermarkt_id` (reproducible imports).
- `overall` for the match engine: weighted mean of PAC, SHO, PAS, DRI, defending, PHY (position-specific weights on `Player.recompute_overall_from_attributes()`).

## Options

| Flag | Description |
|------|-------------|
| `--dry-run` | Parse only, no DB writes |
| `--fixture-dir PATH` | Read `epl.html` and `{crest_slug}_kader.html` (offline / CI) |
| `--base-url` | TM mirror |
| `--eur-usd` | Conversion rate |

## Offline / Reg.ru

If live HTTP is blocked, save HTML under `backend/game/fixtures/transfermarkt/` and run:

```bash
python manage.py import_transfermarkt_epl --fixture-dir game/fixtures/transfermarkt
```

Unit tests use `epl.html` + `arsenal_kader.html` only (no network).

## After import

```bash
python manage.py migrate
python manage.py seed_league --reset   # if starting fresh
python manage.py import_transfermarkt_epl
python manage.py test game
```
