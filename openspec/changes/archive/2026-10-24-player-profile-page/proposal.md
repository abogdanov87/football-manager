## Why

The squad screen and popovers expose only a slice of player data. Managers need a dedicated profile page with contract, career, season stats, positional history from matches, and editable club roles—without adding a sidebar entry. Navigation must return to the screen the user came from.

## What Changes

- Add a **player profile page** (FM shell styling) reachable only by clicking players from the user’s club (`season.player_club_id`).
- Add **GET** (and role **PATCH**) APIs for player detail, gated to the user’s club.
- Persist **match-derived** data: per-match minutes by position, rolling **top-3 favorite positions** over the last **9000** simulated minutes, with a **one-time 3000-minute bootstrap** on the player’s current position at import/first use.
- Add **season statistics** (apps, minutes, goals, assists) aggregated after matches.
- **Career history**: pre-filled from Transfermarkt on import; extended by in-game transfers and club changes; game rows are not overwritten by re-sync.
- **Contract block**: end date (TM where available), computed time-to-expiry, **renewal status**, and **weekly/yearly wage** from a game formula (market value, age, overall, form, season contribution).
- **Club roles** on the profile (captain, penalty taker, free-kick taker): editable only for the user’s club; exactly one captain per club; match engine uses these for the player’s team.
- **Back navigation** via router state (no menu link).

## Capabilities

### New Capabilities

- `player-profile`: Profile page UX, routing, access control (own club only), back navigation, and display of bio, skills, value, contract, career, season stats, favorite positions, and role toggles.
- `player-match-stats`: Recording minutes by position per match, rolling 9000-minute window, 3000-minute position bootstrap, and season aggregates (apps, minutes, goals, assists).
- `player-contract-wages`: Computed weekly/yearly wage and renewal status from game formula; TM contract end date as input where present.
- `club-player-roles`: Persisted captain / penalty / free-kick designations, API updates, single-captain invariant, match engine integration for user club.

### Modified Capabilities

- (none — no existing `openspec/specs/` capabilities yet)

## Impact

- **Backend**: `models.py` (new tables/Club fields), `match_engine.py` (structured appearances), `serializers.py`, `views.py`, `urls.py`, Transfermarkt career import extension, management commands for bootstrap.
- **Frontend**: `App.tsx` routing, new `PlayerProfile` page, clickable players in `SquadTactics` and other own-club surfaces, `api/client.ts`.
- **Data migration**: bootstrap position minutes and optional TM career rows for existing players.
