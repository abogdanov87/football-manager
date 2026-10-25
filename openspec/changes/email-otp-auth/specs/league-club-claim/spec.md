## Purpose

Binds each authenticated user to exactly one club in the single shared active league so multiplayer shares one table and fixture list.

## ADDED Requirements

### Requirement: One club per user in shared league

Each user SHALL own at most one club in the active season’s league. That club SHALL be marked player-controlled for that user. AI clubs SHALL have no owner.

#### Scenario: User with claimed club

- **WHEN** an authenticated user has completed club claim
- **THEN** season and squad APIs resolve `player_club_id` to that club’s id

### Requirement: Claim unowned club after first login

After the first successful OTP verification for a user without a club, the system SHALL require claiming one club from the set of unowned clubs in the active league. Claim SHALL set `owner` and player-controlled flags atomically.

#### Scenario: Choose available club

- **WHEN** the user selects a club with no owner
- **THEN** that club becomes theirs and is removed from the available list for others

#### Scenario: League full

- **WHEN** no unowned clubs remain
- **THEN** new users cannot claim a club and receive a clear error

### Requirement: Club selection UI

The frontend SHALL present available clubs (name, crest) for the user to choose before entering the main game, unless the user already owns a club.

#### Scenario: Returning user skips claim

- **WHEN** a user with an owned club logs in
- **THEN** they proceed directly to the dashboard without claim UI

### Requirement: Player profile access uses owned club

Features that are limited to the user’s squad SHALL use the authenticated user’s owned club id, not a global first-controlled club.

#### Scenario: Profile of own player

- **WHEN** the user opens a player on their claimed club
- **THEN** access is allowed under existing player-profile rules
