# player-profile Specification

## Purpose

Provides a dedicated player profile screen for the user's club with full bio, contract, stats, and role controls, reachable from in-app player links without a main-menu entry.

## Requirements

### Requirement: Profile route and back navigation

The application SHALL expose a player profile route that is not listed in the main navigation menu. When the user opens a profile from another screen, the profile SHALL offer a way to return to that same screen (path and query preserved).

#### Scenario: Open from squad and return

- **WHEN** the user clicks an own-club player on the squad page
- **THEN** the profile page opens and back returns to the squad page

### Requirement: Own-club access only

The profile page and its detail API SHALL be available only for players whose club matches the current season's `player_club_id`. Opponent players in match reports SHALL NOT be linked to this profile in the initial release.

#### Scenario: Own-club player allowed

- **WHEN** the user requests detail for a player on their club
- **THEN** the system returns full profile data

#### Scenario: Other club player denied

- **WHEN** the user requests detail for a player not on their club
- **THEN** the system refuses access (e.g. 404 or 403)

### Requirement: Profile content sections

The profile page SHALL display, for an allowed player: photo; full name; date of birth and age in full years as of the current game date; nationality with flags; top three favorite positions by minutes; contract end and time remaining in years and months; renewal status; weekly and yearly wage; career history in calendar order; per-season apps, minutes, goals, and assists; market value; skill attributes; and individual status for captain, penalty taker, and free-kick taker.

#### Scenario: All sections present

- **WHEN** the user views a valid own-club player profile
- **THEN** each listed section is visible or explicitly empty with a neutral empty state

### Requirement: Career history sources

Career history SHALL list clubs and date ranges in calendar order. Initial rows MAY be imported from Transfermarkt. After in-game club changes, new rows SHALL be recorded from the game and SHALL NOT be removed or overwritten by subsequent Transfermarkt sync.

#### Scenario: TM then transfer in game

- **WHEN** a player has TM career rows and later transfers within the game
- **THEN** the profile shows TM history plus a new game-sourced period for the new club

### Requirement: Visual consistency

The profile page SHALL use the same FM shell styling patterns as existing pages (cards, typography, player avatar, skill presentation).

#### Scenario: Matches squad styling

- **WHEN** the user navigates from squad to profile
- **THEN** the profile visually belongs to the same application shell
