# catch-up — Design Spec

**Date:** 2026-06-14
**Status:** Approved (brainstorming), pending implementation plan
**Author:** Honza Chromec (with Claude Code)

## 1. Purpose

A private web app for one high-school graduating class to track **where in the
world its members are**, what they **do for work**, and their **travel plans** —
so members can spot when they'll be in the same place and plan meet-ups.

Closed, invite-only, one shared dataset. Each member maintains their own profile
and trips (self-service).

## 2. Core decisions (from brainstorming)

| # | Decision |
|---|----------|
| Audience | Private, single class. Invite-only. One shared dataset. No multi-tenant/groups. |
| Editing | Self-service — each member owns and edits their own profile and trips. |
| Auth | Magic link (passwordless). Invite = email on roster. |
| Contact | Each member has a WhatsApp number; person-to-person reach is a `wa.me/<number>` deep link (free, no API). |
| Notifications | Overlap alerts by **email** at MVP, behind a `Notifier` interface. WhatsApp auto-alerts are a documented v2 stretch. |
| Home screen | Map-first with a linked trips/overlaps panel (the approved "combined view"). |
| Overlap signal | **Graded**: same city = strong; same country (different city) = medium. Trip↔trip and trip↔home both count. Date ranges must intersect. |
| Photos | Members can upload a profile photo (object storage). |
| Platform | Web, mobile-first responsive. FastAPI JSON API + React/Vite SPA. |
| Privacy | All authenticated members see all profiles, trips, and WhatsApp numbers. No per-field privacy in MVP. |
| Scale | ~tens of members. |

## 3. System shape

```
React/Vite SPA  ──HTTP/JSON──▶  FastAPI API  ──▶  Postgres
  (react-leaflet)                  │
                                   ├─▶ Geocoder (Photon — free, no key): place autocomplete → city/country/lat/lng
                                   ├─▶ Object storage (S3-compatible / Railway bucket): profile photos
                                   ├─▶ Notifier (EmailNotifier now → WhatsAppNotifier later)
                                   └─▶ Overlap worker (scheduled recompute + alerts)
```

One repository, two codebases:

- `backend/` — Python 3.13, uv, ruff, pytest, SQLAlchemy 2.x, alembic, FastAPI.
  Mirrors the `dokturek-mkn10` toolchain and conventions.
- `frontend/` — React + TypeScript + Vite, react-query, react-leaflet.

Deploy on Railway: Postgres, an `api` service, a `web` static service, a
scheduled overlap job, and an object-storage bucket. Multi-stage `Dockerfile`;
`alembic upgrade head` runs on backend entrypoint before serving traffic
(mkn10 parity).

## 4. Data model

| Table | Key fields | Notes |
|-------|-----------|-------|
| `member` | id, name, email (unique), photo_url, whatsapp (E.164), home_place_id (FK place), job_title, company, note, created_at | One row per classmate. `email` is both invite key and login identity. |
| `place` | id, city, country_code (ISO 3166-1 alpha-2), country_name, lat, lng | Normalized via geocoder; deduplicated so the same city is shared by many members/trips. |
| `trip` | id, member_id (FK), place_id (FK), start_date, end_date, note, created_at | A member's planned presence somewhere. |
| `overlap` | id, member_a_id, member_b_id (a<b), kind (`trip-trip`\|`trip-home`), strength (`strong`\|`medium`), place_id\|country_code, start_date, end_date, notified_at | Computed/materialized by the worker. `notified_at IS NULL` ⇒ alert not yet sent. |

`roster_email` (allowed invite emails) may be a small table or a seeded config
list; see §6.

All date handling uses inclusive `[start_date, end_date]` day ranges.

## 5. Overlap detection

Pure function over `(trips, members' homes) → list[overlap]`, with no DB access;
a runner persists the result.

- **Home presence**: a member's `home_place` is treated as an always-present
  interval (unbounded dates) at their home city/country.
- **Strong** (⚡): two members in the **same city** with **intersecting** date
  ranges. Covers trip↔trip and trip↔home (a visitor's trip overlapping a
  resident's home).
- **Medium**: two members in the **same country but different city**, with
  intersecting date ranges.
- Pairs are **unordered** (`member_a_id < member_b_id`) to avoid duplicates.
- For trip↔home, the overlap interval is the visitor's trip dates (the resident
  is always present).

The worker recomputes overlaps on a schedule, upserts the table, and for each row
with `notified_at IS NULL` sends an alert via the `Notifier`, then stamps
`notified_at`. A failed send leaves the row un-notified so it retries next run.

## 6. Auth — magic link

- **Invite / roster**: an allowed-email roster gates access. Only roster emails
  can request a login link. The owner seeds it (admin action or migration seed).
- **Login flow**: member enters email → if on roster, a signed, single-use,
  short-TTL token is emailed as a link → clicking it sets an httpOnly, signed
  session cookie. No passwords.
- Link requests are rate-limited per email/IP.
- First successful login for a roster email auto-creates that member's row
  (empty profile to fill in).

## 7. Backend layout (mkn10-style separation)

```
backend/src/catchup/
  config.py        # pydantic-settings BaseSettings (DATABASE_URL, secrets, bucket, geocoder, email)
  db.py            # engine + SessionLocal + session_scope
  models.py        # SQLAlchemy models (member, place, trip, overlap, roster_email)
  auth/            # magic-link token issue/verify, session cookie, email sender glue
  api/             # FastAPI routers
  places/          # geocoder client (pure HTTP client) + place service (dedupe/upsert)
  storage/         # object-storage client (S3-compatible) for photo upload
  overlaps/         # detection.py (pure, no DB) + runner.py (persist + notify)
  notify/          # Notifier Protocol; EmailNotifier (impl) + WhatsAppNotifier (stub)
  worker.py        # scheduled overlap recompute + notify entrypoint
```

Convention (from mkn10): pure logic modules never import the DB; only
runners/services touch the session. Logging via stdlib `logging`, not `print`.

### API surface

| Method & path | Purpose |
|---|---|
| `POST /auth/request-link` | Email a magic link (roster-gated, rate-limited). |
| `GET  /auth/callback?token=` | Verify token, set session cookie. |
| `POST /auth/logout` | Clear session. |
| `GET  /auth/me` | Current member or 401. |
| `GET  /members` | All members (profiles, home, whatsapp). |
| `GET  /members/{id}` | One member with their trips. |
| `PATCH /members/me` | Edit own profile fields. |
| `POST /members/me/photo` | Upload profile photo → object storage → sets `photo_url`. |
| `GET  /trips` | All upcoming trips. |
| `POST /trips` | Create own trip. |
| `PATCH /trips/{id}` · `DELETE /trips/{id}` | Edit/delete own trip (ownership-checked). |
| `GET  /overlaps/me` | Current member's overlaps, strong first. |
| `GET  /places/search?q=` | Geocoder proxy → city/country/lat/lng suggestions. |

## 8. Photo upload

- Profile photos upload to an **S3-compatible object-storage bucket** (Railway
  bucket at deploy; any S3 endpoint locally, e.g. MinIO).
- `POST /members/me/photo` accepts an image (size/type validated), stores it under
  a per-member key, and sets `member.photo_url` to the served URL.
- The `storage/` module wraps the S3 client behind a small interface so the
  bucket provider is swappable and testable.
- Constraints: max ~5 MB, `image/jpeg|png|webp`, server validates content type.

## 9. Frontend

React + TypeScript + Vite. react-query for server state. react-leaflet with
OpenStreetMap tiles (no API key) for the map.

Screens:

- **Map home** — the approved combined view: map canvas (home pins, trip pins,
  overlap markers) + a linked trips/overlaps panel. Overlaps section pinned on
  top, upcoming trips below. Side panel on desktop, swipe-up bottom sheet on
  mobile. Map ↔ panel linked both ways (tap trip → highlight pin; tap pin →
  scroll trip / open member drawer).
- **My profile** — edit name, photo (upload), home location (place autocomplete),
  job title, company, WhatsApp, note.
- **Trip add/edit** — destination (place autocomplete), start/end date, note.
- **Member drawer** — a classmate's profile, trips, and a `wa.me` "Message on
  WhatsApp" button.
- **Login** — email entry → "check your inbox" confirmation.

## 10. Error handling & edges

- Geocoder unavailable → place search surfaces a retry; allow manual
  city + country entry as fallback (lat/lng best-effort/null).
- Email send failure → overlap row stays `notified_at IS NULL`, retried next run;
  error logged.
- Expired or already-used magic link → friendly "request a new link" screen.
- Photo upload failure (too large / wrong type / storage down) → clear error,
  profile otherwise saves.
- Trip with `end_date < start_date` → rejected with a validation message.
- Non-roster email requesting a link → generic "if you're invited, check your
  inbox" (no account enumeration).

## 11. Testing (mkn10 parity)

- **Backend unit** — overlap detection is a pure function: rich table-driven
  tests (same/different city, same/different country, date intersect/disjoint,
  trip↔home, pair ordering). No DB.
- **Backend smoke** — `@pytest.mark.smoke`, live Postgres: migrations, member/trip
  CRUD, overlap runner persistence, magic-link issue/verify.
- **Frontend** — vitest + React Testing Library, light: panel↔map linking,
  profile/trip forms, login flow happy path.

## 12. Deployment

- Railway project: Postgres, `api` (FastAPI + gunicorn/UvicornWorker), `web`
  (static React build), scheduled **overlap job** (Railway cron invoking the
  worker), and an object-storage bucket.
- Multi-stage `Dockerfile`; entrypoint runs `alembic upgrade head` before serving.
- Trunk-based: push to `main` auto-deploys (mkn10 convention).
- Config via env (`DATABASE_URL`, session secret, geocoder base URL, email
  provider creds, bucket creds/endpoint).

## 13. Out of scope (MVP)

- WhatsApp **automated** alerts (Cloud API: WABA, template approval, per-message
  cost) — designed-for behind `Notifier`, not built.
- Per-field / per-member privacy controls.
- Multiple classes / groups / multi-tenancy.
- Radius / "within X km" matching (only city + country tiers).
- Native mobile app.
- Social logins beyond magic link.

## 14. Open questions for the plan

- Email provider choice (e.g. Resend vs SMTP/SES) — pick during planning.
- Overlap job cadence (e.g. hourly vs daily) and whether to also send a periodic
  digest vs only on new overlaps.
- Whether `web` is a separate Railway static service or served by FastAPI
  `StaticFiles` (one service). Lean: separate static service.
