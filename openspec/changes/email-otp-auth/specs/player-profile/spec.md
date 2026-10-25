## MODIFIED Requirements

### Requirement: Own-club access only

The profile page and its detail API SHALL be available only for players whose club is the authenticated user’s owned club in the shared league. Opponent players in match reports SHALL NOT be linked to this profile in the initial release. The system SHALL NOT resolve the user’s club by selecting the first globally player-controlled club.

#### Scenario: Own-club player allowed

- **WHEN** the user requests detail for a player on their owned club
- **THEN** the system returns full profile data

#### Scenario: Other club player denied

- **WHEN** the user requests detail for a player on another club
- **THEN** the system refuses access (e.g. 404 or 403)
