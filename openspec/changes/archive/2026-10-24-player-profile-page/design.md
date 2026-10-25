## Context

See `proposal.md`. Today `Player` holds bio, skills, value, and contract end; matches store text events without structured per-player minutes. `Season.player_club_id` identifies the user's club. Set-piece and captain choices exist only inside `match_engine` heuristics.

## Goals / Non-Goals

**Goals:**

- End-to-end profile for own-club players with data backed by simulation where required.
- Canon: favorite positions use a **9000-minute** rolling window; **3000-minute one-time bootstrap** on current position only (does not inflate season apps).
- TM career pre-fill; game-authored career rows afterward.
- Wages and renewal status from formula; TM for contract end when present.
- Club role IDs + profile toggles + engine reads them for user club.

**Non-Goals:**

- Clickable opponent players in match reports.
- Sidebar menu entry for profile.
- Real-world salary scraping from TM.
- Full transfer negotiation mini-game (renewal status is computed/display first).

## Decisions

### Data model

- `PlayerMatchAppearance`: `player_id`, `match_id`, `minutes`, `position_code`, `goals`, `assists`, `started`.
- `PlayerPositionMinuteLedger` or FIFO queue of `(match_id, position_code, minutes)` for rolling 9000 window; alternatively recompute from appearances ordered by match date (simpler, acceptable at EPL scale).
- `PlayerSeasonStat`: `season_id`, `player_id`, apps, minutes, goals, assists.
- `PlayerCareerEntry`: `player_id`, club label (FK or text), `from_date`, `to_date`, `source` (`transfermarkt` | `game`).
- `Player.position_minutes_bootstrapped` boolean (or equivalent) to enforce one-time 3000 credit on `position` / primary slot code at bootstrap.
- `Club`: `captain_player_id`, `penalty_taker_player_id`, `free_kick_taker_player_id` (nullable FKs to `Player`).

### Position bootstrap (canon)

On first need (import command or lazy on profile/stats read): if not bootstrapped, add **3000** minutes to ledger for player's current `position` (or `tm_position` mapping table). Mark bootstrapped. Never repeat. These minutes participate in top-3 ranking within the **9000** rolling total only.

### Favorite positions API

Aggregate last 9000 minutes by `position_code`, sort desc, return top 3 with minutes and percentage of the 9000 window (or of sum within window if under 9000).

### Career merge

TM import writes `PlayerCareerEntry` rows with `source=transfermarkt`. Re-sync skips overwriting or deleting `source=game` rows. In-game transfer closes open TM/game row `to_date` and appends new `source=game` row.

### Wage formula (sketch)

```
base = market_value_usd * weekly_wage_rate_by_league  # tunable constant
age_factor = piecewise peak 24-28
perf = 1 + k1 * normalized(form) + k2 * season_goals_assists
weekly = base * age_factor * perf * overall_scale(overall)
yearly = weekly * 52
```

Renewal status from months to `contract_end_date`: e.g. >24 secure, 12-24 monitor, <12 urgent. Constants in one module for tuning.

### API

- `GET /api/seasons/current/players/{id}/` — detail serializer; checks `player.club_id == season.player_club_id`.
- `PATCH /api/clubs/{id}/player-roles/` or nested on player — only `player_club_id`; validates FKs belong to club; captain uniqueness.
- Frontend: route `/players/:playerId`, `navigate(path, { state: { from } })`, back uses `from`.

### UI

New page component reusing `PlayerAvatar`, `PlayerNationality`, skill bars from `PlayerFifaStats` patterns, Ant Design cards like Dashboard/Squad. Role switches disabled when `player.club_id !== playerClubId`.

### Match engine

After simulate: write appearances and update season stats from structured events (extend event generation to emit player_id on goals/assists if not already). For user club snapshot, read club role FKs into snapshot before `designate_set_piece_takers`.

## Risks / Trade-offs

- **[Risk] Parsing goals/assists from text events** → Mitigation: emit structured stats during simulation in same pass as events.
- **[Risk] TM career parser + WAF** → Mitigation: fixtures + optional skip; show current club only until parsed.
- **[Risk] 3000 bootstrap skews early top-3** → Mitigation: fades as real minutes enter 9000 window; document in UI as "предпочтения по минутам".

## Migration Plan

1. Deploy models + migrations.
2. Run bootstrap command for existing players (`position_minutes_bootstrapped`).
3. Optional TM career backfill command.
4. Ship frontend route; enable links on squad first.

Rollback: new tables are additive; disable links if API not ready.

## Open Questions

- Exact renewal status labels and Russian copy for UI.
- Whether in-game contract extension updates `contract_end_date` manually or via future feature (display-only status for v1 is enough).
