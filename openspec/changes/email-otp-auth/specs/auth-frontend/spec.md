## Purpose

Lets users sign in via email OTP in the React app and keeps the game shell behind authentication with working logout actions.

## ADDED Requirements

### Requirement: Login route and two-step flow

The application SHALL provide a login route with steps for email entry and OTP code entry. Successful verification SHALL store the session token and redirect into the game.

#### Scenario: New user completes login

- **WHEN** a user enters email, receives a code, and verifies successfully
- **THEN** they are taken to club claim or the main app as appropriate

### Requirement: Protect game routes

Routes that show league, squad, and club management SHALL require a valid session. Unauthenticated visitors SHALL be redirected to login.

#### Scenario: Anonymous visit to squad

- **WHEN** a user without a token opens the squad page
- **THEN** they are redirected to login

### Requirement: Attach token to API calls

The API client SHALL send the session token on authenticated requests and SHALL clear local session state on 401 responses.

#### Scenario: Token attached

- **WHEN** the user is logged in and the app calls a protected endpoint
- **THEN** the request includes the bearer token header

### Requirement: Logout in UI

The shell SHALL offer logout (current session) and logout on all devices, calling the corresponding backend endpoints and returning the user to login.

#### Scenario: Logout all devices

- **WHEN** the user chooses logout on all devices
- **THEN** local token is cleared and subsequent API calls require login again
