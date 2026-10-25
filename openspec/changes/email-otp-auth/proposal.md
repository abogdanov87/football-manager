## Why

The game currently has no player accounts: APIs are open and “my club” is a single shared slot. We need standard email-based sign-in so each person owns one club in a **shared league**, with secure sessions and branded OTP email.

## What Changes

- **Passwordless auth:** request a numeric OTP by email; verify within ~10 minutes; issue a session token valid **7 days**.
- **Email:** send OTP in an HTML template matching the FM shell visual style (no magic-link button).
- **Sessions:** Bearer token auth on API; **logout** (current device) and **logout all devices** in v1.
- **Users:** unique email only (no username/password).
- **League model:** one active season for all clubs; each registered user **claims** one unowned EPL club after first successful verify; max ~20 humans.
- **API hardening:** replace global `player_club()` lookup with **authenticated user’s owned club**; protect game endpoints with authentication where appropriate.
- **Frontend:** login flow, token storage, route guards, logout actions in shell.

## Capabilities

### New Capabilities

- `auth-otp`: OTP request/verify, token lifecycle (7d), logout and logout-all, rate limits.
- `auth-email`: OTP email content and delivery (game-styled HTML, numeric code only).
- `auth-frontend`: Login UI, API client auth headers, protected app shell.
- `league-club-claim`: Shared league ownership rules, club claim onboarding, per-user `player_club_id`.

### Modified Capabilities

- `player-profile`: Access and `player_club_id` MUST be resolved from the authenticated user’s owned club (not the first `is_player_controlled` club globally).

## Impact

- **Backend:** new auth app or `game` auth module, models (`EmailOtpChallenge`, `AuthToken`), email templates, DRF authentication, `views.py` / `seed_league` adjustments, migrations.
- **Frontend:** `/login`, auth context, 401 handling, club-claim step, header logout.
- **Ops:** SMTP or provider env vars; dev console/Mailpit backend.
- **Data:** migrate existing seed so clubs start unowned until claimed (or one-time admin assignment).

## Non-Goals (v1)

- Magic-link login in email
- Releasing a claimed club back to the pool
- Multiple saves per user or private leagues per user
