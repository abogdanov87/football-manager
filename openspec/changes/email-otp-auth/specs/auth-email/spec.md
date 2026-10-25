## Purpose

Delivers one-time login codes by email using HTML that matches the Football Manager shell branding.

## ADDED Requirements

### Requirement: Numeric OTP only in email

Login emails SHALL contain a numeric one-time code for manual entry. They SHALL NOT include a magic-link or one-click login URL as the primary mechanism.

#### Scenario: Email content

- **WHEN** an OTP is sent
- **THEN** the message body includes a clearly visible numeric code and the code expiry time in minutes

### Requirement: Game-styled HTML template

OTP emails SHALL use an HTML layout consistent with the in-game FM shell: dark background, high-contrast text, and primary accent colors used in the web app (red accent and supporting neutrals/greens).

#### Scenario: Visual consistency

- **WHEN** a user opens the OTP email on a typical client
- **THEN** the message visually aligns with the product’s dark FM aesthetic

### Requirement: Plain-text fallback

The system SHALL include a plain-text part with the same code and expiry for clients without HTML.

#### Scenario: Text-only client

- **WHEN** the email is shown as plain text
- **THEN** the user can still read the code and expiry

### Requirement: Security copy

Emails SHALL state that the code is single-use, must not be shared, and should be ignored if the user did not request login.

#### Scenario: Safety notice present

- **WHEN** any OTP email is sent
- **THEN** it includes brief security guidance in the user’s locale (Russian for this product)
