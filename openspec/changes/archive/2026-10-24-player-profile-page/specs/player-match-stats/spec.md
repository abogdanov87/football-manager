## Purpose

Tracks simulated playing time by position and season box-score stats so the player profile can show favorite roles and seasonal performance from match simulation, not external guesses.

## ADDED Requirements

### Requirement: Record minutes by position per match

After each simulated match, the system SHALL persist each participating player's minutes played attributed to a position code used in the match (starting slot and substitution positions as applicable).

#### Scenario: Starter minutes

- **WHEN** a player starts a match in a given pitch slot
- **THEN** their appearance minutes for that match count toward that slot's position code

### Requirement: Rolling window for favorite positions

Favorite positions for display SHALL be derived from simulated minutes in a rolling window of the last **9000** minutes per player. The UI SHALL show up to the top three position codes by minute share within that window.

#### Scenario: Top three after many matches

- **WHEN** a player has more than 9000 cumulative simulated minutes across several positions
- **THEN** only the most recent 9000 minutes contribute to ranking and the profile shows the three highest-minute positions

### Requirement: One-time position bootstrap

Before sufficient simulated history exists, the system SHALL apply a **one-time** credit of **3000** minutes to the player's **current** position (primary squad position at bootstrap time). This bootstrap SHALL count only toward the favorite-position rolling window and season stats aggregation rules, not as fake match appearances in season apps.

#### Scenario: New save before first match

- **WHEN** the player has no simulated minutes yet and bootstrap has not run
- **THEN** favorite positions reflect 3000 minutes on the current position until real minutes accrue

#### Scenario: Bootstrap runs once

- **WHEN** position bootstrap has already been applied for a player
- **THEN** a second bootstrap is not applied on re-import or profile revisit

### Requirement: Season aggregates

The system SHALL maintain per-player, per-season totals for appearances, minutes, goals, and assists, updated from simulated match results.

#### Scenario: After league match

- **WHEN** the user's club completes a simulated match in the active season
- **THEN** each participating squad player's season row includes updated apps, minutes, goals, and assists
