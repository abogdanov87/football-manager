## 1. Data model and migrations

- [x] 1.1 Add `PlayerMatchAppearance`, `PlayerSeasonStat`, `PlayerCareerEntry`, club role FKs, and `position_minutes_bootstrapped` via migrations; verify `manage.py migrate` succeeds
- [x] 1.2 Implement position-minute bootstrap (3000 one-time on current position) in a management command; verify running it sets flag and ledger entries for a sample player
- [x] 1.3 Add TM career import path (parser + command) writing `source=transfermarkt` rows; verify fixture profile yields ordered career entries

## 2. Match engine and stats

- [x] 2.1 Persist structured appearances (minutes, position_code, goals, assists) after each match simulation; verify unit test on a fixed seed match
- [x] 2.2 Update season stat aggregates from appearances; verify totals after two simulated matches for one player
- [x] 2.3 Implement rolling 9000-minute top-3 position aggregation including bootstrap minutes; verify test with synthetic ledger exceeds and trims window
- [x] 2.4 Load club captain/penalty/FK IDs into user-club match snapshot and prefer them in set-piece logic; verify designated penalty taker is selected in engine test

## 3. Contract and wages

- [x] 3.1 Implement wage and renewal-status computation module; verify unit tests for age peak, short contract urgent state, and yearly = weekly × 52
- [x] 3.2 Expose computed fields on player detail serializer; verify API JSON includes wages, renewal status, and months/years remaining

## 4. API

- [x] 4.1 Add `GET` player detail endpoint gated by `player_club_id`; verify 403/404 for other club and 200 for own player
- [x] 4.2 Add `PATCH` club player-roles endpoint with single-captain invariant; verify assigning new captain clears previous

## 5. Frontend

- [x] 5.1 Add `/players/:playerId` route with `state.from` back navigation; verify back returns to squad URL with query intact
- [x] 5.2 Build `PlayerProfile` page (fm-shell) with all sections from spec; verify manual walkthrough on dev server
- [x] 5.3 Link own-club players from `SquadTactics` (and other own-club surfaces); verify opponent names in match report are not links
- [x] 5.4 Wire role toggles and contract/stats API types in `api/client.ts`; verify toggling captain updates squad captain badge after refresh

## 6. Integration

- [x] 6.1 Run backend test suite for new modules; verify `manage.py test game` passes
- [x] 6.2 Run `openspec validate player-profile-page --strict`; verify validation succeeds
