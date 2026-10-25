## Purpose

Provides passwordless email OTP authentication and seven-day API session tokens, including single-device and all-device logout.

## ADDED Requirements

### Requirement: Request OTP by email

The system SHALL accept a valid email address and create a one-time numeric OTP challenge with an expiry of approximately ten minutes. The system SHALL send the OTP via email and SHALL apply rate limiting per email and per client IP.

#### Scenario: OTP requested for new email

- **WHEN** a client requests an OTP for an email that is not yet registered
- **THEN** the system creates a challenge, sends the code, and responds without revealing whether the account already exists beyond a generic success message

#### Scenario: OTP requested for existing email

- **WHEN** a client requests an OTP for a registered email
- **THEN** the system creates a new challenge and sends a fresh code using the same flow as registration

### Requirement: Verify OTP and issue session token

The system SHALL verify the submitted email and numeric code against the active challenge. On success it SHALL create or load the user by unique email and SHALL issue an API session token valid for seven days from issuance.

#### Scenario: Valid code within TTL

- **WHEN** the user submits the correct code before the challenge expires
- **THEN** the system returns a bearer token with expiry metadata and marks the challenge used

#### Scenario: Invalid or expired code

- **WHEN** the code is wrong, expired, or the challenge is already used
- **THEN** the system rejects verification without issuing a token

### Requirement: Authenticated API access

Protected game endpoints SHALL require a valid non-revoked session token. Invalid or missing tokens SHALL result in unauthorized responses.

#### Scenario: Request with valid token

- **WHEN** the client sends a valid Authorization bearer token
- **THEN** the request is attributed to the corresponding user

### Requirement: Logout current session

The system SHALL provide an endpoint that revokes the session token presented on the request.

#### Scenario: User logs out

- **WHEN** an authenticated user calls logout with their current token
- **THEN** that token no longer authorizes API calls

### Requirement: Logout all sessions

The system SHALL provide an endpoint that revokes all session tokens for the authenticated user.

#### Scenario: Logout everywhere

- **WHEN** an authenticated user calls logout-all
- **THEN** all of that user’s tokens are revoked including the current one
