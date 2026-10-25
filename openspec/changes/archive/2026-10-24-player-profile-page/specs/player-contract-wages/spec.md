## Purpose

Presents contract timing and wage figures on the player profile using game rules grounded in player value, age, and performance, while using Transfermarkt-sourced contract end dates when available.

## ADDED Requirements

### Requirement: Contract end display

The profile SHALL show the player's contract end date. When Transfermarkt import provides `contract_end_date`, that date SHALL be used unless superseded by an in-game extension event.

#### Scenario: TM contract on file

- **WHEN** the player has a stored contract end date from import
- **THEN** the profile shows that date and years/months remaining until it

### Requirement: Wage from game formula

Weekly and yearly wages SHALL be computed by a game formula that considers market value, age, overall rating, form, and current-season contribution (goals and assists). Transfermarkt SHALL NOT be required to supply wage numbers.

#### Scenario: Wage shown on profile

- **WHEN** the user views contract details
- **THEN** weekly and yearly wage values are shown as game-calculated amounts

### Requirement: Renewal status

The system SHALL expose a renewal status derived from time to contract end and game rules (e.g. secure, monitor, urgent). TM data MAY inform contract end but renewal state SHALL follow game logic.

#### Scenario: Short contract flagged

- **WHEN** fewer than twelve months remain on the contract
- **THEN** renewal status reflects an urgent or equivalent state defined by product rules
