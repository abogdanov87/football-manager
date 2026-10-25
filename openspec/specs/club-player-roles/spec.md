# club-player-roles Specification

## Purpose

Lets the user assign captaincy and set-piece takers for their club from the player profile, with one captain per club and match simulation respecting those choices.

## Requirements

### Requirement: Persisted club roles

The system SHALL store at club level which player is captain, penalty taker, and free-kick taker. Exactly one player MAY be captain at a time for a given club.

#### Scenario: Assign captain

- **WHEN** the user sets a player as captain from their profile
- **THEN** that player becomes captain and any previous captain for the club is cleared

### Requirement: Edit only user club

Role assignment controls SHALL be available only when the player belongs to the season's `player_club_id`. The API SHALL reject role changes for other clubs.

#### Scenario: Opponent club player

- **WHEN** the user somehow requests a role change for a non-own-club player
- **THEN** the request is rejected

### Requirement: Match engine uses user designations

For matches involving the user's club, simulated penalty and free-kick taking and captaincy SHALL prefer the stored club role assignments when set; otherwise existing heuristics MAY apply for unset roles.

#### Scenario: User penalty taker takes penalty

- **WHEN** a penalty is awarded in the user's match and a penalty taker is designated
- **THEN** that designated player is chosen as taker when on the pitch
