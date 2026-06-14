# Phase 1 Data Model — Members, Magic-Link Auth & Profiles

Postgres schema for slice 001, installed by alembic migration `0001_initial`.
`place` is intentionally general (reused by trips/overlaps in 002+).

## Entities

### `member`

The joined classmate and their profile. Created on first successful sign-in.

| Field | Type | Notes |
|---|---|---|
| `id` | uuid PK | server-generated |
| `email` | citext, unique, not null | identity; matches the roster invite |
| `display_name` | text, null | shown in directory; falls back to email local-part if unset |
| `photo_url` | text, null | URL into object storage; null ⇒ placeholder avatar |
| `home_place_id` | uuid FK → `place.id`, null | structured home location |
| `job_title` | text, null | |
| `company` | text, null | |
| `whatsapp_e164` | text, null | E.164 (`+<country><number>`); validated on write |
| `note` | text, null | short free-text |
| `created_at` | timestamptz, not null, default now | first sign-in |
| `last_login_at` | timestamptz, null | updated each successful verify |

Rules: `email` immutable after creation. `whatsapp_e164` must pass `phonenumbers`
validation. Membership in the directory = existence of this row (FR-016).

### `place`

Normalized geographic place from the geocoder; deduplicated and shared.

| Field | Type | Notes |
|---|---|---|
| `id` | uuid PK | |
| `city` | text, not null | |
| `country_code` | char(2), not null | ISO 3166-1 alpha-2 |
| `country_name` | text, not null | |
| `lat` | double precision, not null | for the later map |
| `lng` | double precision, not null | |
| `created_at` | timestamptz, not null, default now | |

Rules: dedupe on `(round(lat,4), round(lng,4))` (or geocoder place identity) so the
same city is one row. Created on demand when a member saves a home location.

### `roster_invite`

Emails permitted to sign in. Owner-managed via the `catchup-roster` CLI.

| Field | Type | Notes |
|---|---|---|
| `email` | citext PK | allowed sign-in address |
| `added_at` | timestamptz, not null, default now | |
| `note` | text, null | e.g. "Class of 2009" |

Rules: presence here is the access gate (FR-001). Removing an email blocks future
sign-ins but does not delete an existing member (sessions can still be revoked).

### `signin_token`

Single-use, time-limited magic-link credential.

| Field | Type | Notes |
|---|---|---|
| `id` | uuid PK | |
| `email` | citext, not null | roster email the link was issued for |
| `token_hash` | text, not null, unique | hash of the raw token in the link |
| `expires_at` | timestamptz, not null | now + 15 min |
| `used_at` | timestamptz, null | set on first successful verify |
| `created_at` | timestamptz, not null, default now | |

Rules: valid iff `used_at IS NULL AND now() < expires_at` (FR-003). Raw token never
stored. Expired/used rows may be pruned.

### `session`

Server-side session backing the auth cookie.

| Field | Type | Notes |
|---|---|---|
| `id` | uuid PK | |
| `member_id` | uuid FK → `member.id`, not null | |
| `token_hash` | text, not null, unique | hash of the opaque cookie token |
| `expires_at` | timestamptz, not null | now + 30 days (sliding) |
| `created_at` | timestamptz, not null, default now | |
| `revoked_at` | timestamptz, null | set on sign-out (FR-014) |

Rules: a request is authenticated iff a matching row exists with
`revoked_at IS NULL AND now() < expires_at`.

## Relationships

```
roster_invite (email) ──first sign-in──▶ member
member.home_place_id ──▶ place
session.member_id ──▶ member
signin_token.email ──(matches)──▶ roster_invite.email
```

## State transitions

**Sign-in**: roster email → `request-link` creates `signin_token` (15 min) →
emailed → `callback` verifies + stamps `used_at` → upserts `member` (first time) →
creates `session` + sets cookie. **Sign-out**: `session.revoked_at = now()`.

**Profile**: empty on creation → member edits own fields → persisted. Home location
edit upserts/links a `place`. Photo upload sets/clears `photo_url`.

## Indexes

- `member(email)` unique; `roster_invite(email)` PK.
- `signin_token(token_hash)` unique; partial index on `expires_at` for pruning.
- `session(token_hash)` unique; `session(member_id)`.
