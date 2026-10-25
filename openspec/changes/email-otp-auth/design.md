## Context

See `proposal.md`. Django + DRF + React SPA; `Club.owner` exists but unused; `player_club()` picks first `is_player_controlled`. No frontend auth. Existing player-profile specs assume `player_club_id` from season overview.

## Goals / Non-Goals

**Goals:**

- Email-only users; 6-digit OTP (~10 min); bearer token 7 days; logout + logout-all.
- FM-styled HTML email (no magic link).
- Shared active `Season`; each human claims one unowned `Club`; APIs scoped to `request.user`’s club.
- Route guard + login UI; club claim step after first verify.

**Non-Goals:**

- OAuth, passwords, magic links, per-user private leagues, releasing clubs.

## Decisions

### Auth module

- Add `game/auth/` (or small `accounts` app): models `EmailOtpChallenge`, `AuthToken`; services for hash/compare OTP, mint/revoke tokens.
- User model: extend via `AbstractUser` **or** use default `User` with `USERNAME_FIELD = "email"` and custom manager — prefer **email as username** stored in `email` + `username=email` for Django admin compatibility.
- OTP: 6 digits, `secrets`; store `code_hash` + `salt`; max attempts (e.g. 5); invalidate previous open challenges on new request for same email.

### Token

- Opaque random token (32+ bytes), store hash in DB; `Authorization: Bearer <token>`.
- DRF `TokenAuthentication` subclass reading `AuthToken` with `expires_at` and `revoked_at`.
- Alternative considered: JWT — rejected for simpler revocation (logout-all).

### Email

- Django templates: `templates/emails/otp.html`, `otp.txt`.
- Colors from `fm-shell`: bg `#101113`, text `#e7f2eb`, accent `#ee1b2e`, secondary green `#3dd68c`.
- Settings: `EMAIL_*` env; dev `console` or Mailpit.

### Rate limits

- Simple DB or cache counters: 3 requests / 15 min / email; 10 / 15 min / IP on `otp/request`.

### League + claim

- `seed_league`: all 20 clubs `owner=None`, `is_player_controlled=False` until claimed.
- On claim: `club.owner = user`, `is_player_controlled = True`; unique constraint one club per user (partial index or app check).
- `GET /api/clubs/available/` — unowned clubs in active season standings.
- `POST /api/clubs/claim/` `{ club_id }` — transactional; 409 if taken.
- Replace `player_club()` → `get_player_club(user)` raising if unauthenticated or unclaimed.

### Season overview

- `player_club_id` from authenticated user’s club; 403 or null + frontend redirect to claim if missing.

### Frontend

- Routes: `/login`, `/claim-club` (guard if authed but no club).
- `AuthProvider`: token in `localStorage`, refresh `me` on load.
- `api/client.ts`: inject header; on 401 clear and redirect.
- Header menu: logout, logout all.

### Migration

- One-time data migration: clear `is_player_controlled` on all clubs without owner; document re-seed for dev.

### Protecting endpoints

- Phase: default `IsAuthenticated` on game views except `otp/*`, `season/current` may need split (public health vs authed) — season requires auth post-change.
- Manual matchday simulate remains staff/debug gated.

## Risks / Trade-offs

- **[Risk] League full at 20 users** → Mitigation: clear error on claim; waitlist later.
- **[Risk] Email deliverability** → Mitigation: SPF/DKIM in prod docs; dev Mailpit.
- **[Risk] Token in localStorage** → Mitigation: HTTPS only prod; XSS hygiene; acceptable for v1 SPA.

## Migration Plan

1. Ship models + auth endpoints behind feature flag optional.
2. Migrate clubs; deploy email config.
3. Enable frontend guard; existing anonymous users must register.

## Open Questions

- Exact club picker UX (grid with crests vs dropdown) — implement as grid matching league table visuals.
- Whether OTP email language is always Russian — assume yes (`LANGUAGE_CODE`).
