## 1. Backend auth core

- [x] 1.1 Add `EmailOtpChallenge` and `AuthToken` models plus email-as-login user setup; verify `manage.py migrate` succeeds
- [x] 1.2 Implement OTP request/verify services (6-digit, 10 min TTL, hashed storage, rate limits); verify unit tests for expiry and invalid code
- [x] 1.3 Add DRF bearer authentication and token revocation; verify authenticated vs 401 on a sample protected view

## 2. Auth API

- [x] 2.1 Expose `POST /api/auth/otp/request/`, `POST /api/auth/otp/verify/`, `GET /api/auth/me/`; verify verify returns 7-day expiry metadata
- [x] 2.2 Expose `POST /api/auth/logout/` and `POST /api/auth/logout-all/`; verify logout-all invalidates multiple tokens in test

## 3. Email

- [x] 3.1 Create FM-styled HTML and text OTP templates (numeric code only, Russian copy); verify render test includes code and expiry
- [x] 3.2 Wire send on OTP request with configurable `EMAIL_BACKEND`; verify dev console backend prints message

## 4. League club claim

- [x] 4.1 Update `seed_league` so clubs start unowned; add data migration for existing DBs; verify no club has owner until claimed
- [x] 4.2 Implement `GET /api/clubs/available/` and `POST /api/clubs/claim/` with one-club-per-user rules; verify 409 when club taken
- [x] 4.3 Replace `player_club()` with user-scoped resolver across views/serializers; verify tests use `owner` not global flag

## 5. Protect game API

- [x] 5.1 Require authentication on season, squad, tactics, player detail, and role endpoints; verify anonymous requests get 401
- [x] 5.2 Update `player-profile` access tests for owned-club resolution; verify `manage.py test game` passes

## 6. Frontend

- [x] 6.1 Add login page (email + OTP steps) and token storage in API client; verify successful verify stores token
- [x] 6.2 Add route guards and `/claim-club` picker for users without a club; verify claim then lands on dashboard
- [x] 6.3 Add logout and logout-all actions in shell header; verify tokens cleared and user sent to login

## 7. Integration

- [x] 7.1 Document required env vars (SMTP, `DJANGO_SECRET_KEY`) in project docs; verify README or existing doc mentions Mailpit for dev
- [x] 7.2 Run `openspec validate email-otp-auth --strict`; verify validation succeeds
