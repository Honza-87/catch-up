# Implementation Plan: Members, Magic-Link Auth & Profiles

**Branch**: `001-member-auth-profiles` | **Date**: 2026-06-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-member-auth-profiles/spec.md`

## Summary

Foundation slice of `catch-up`: invited classmates sign in passwordlessly via a
single-use email link, maintain their own profile (name, photo, structured home
city/country, job, company, WhatsApp, note), and browse a directory of joined
classmates with one-tap WhatsApp contact. Built as a FastAPI JSON API + React/Vite
SPA over Postgres, with profile photos in S3-compatible object storage and home
locations normalized through a free geocoder — exactly the toolchain and
conventions of `dokturek-mkn10`. Map, trips, overlap detection, and email overlap
alerts are deliberately deferred to later slices (002+); this slice only stands up
identity, profiles, and the directory they populate.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript 5.x (frontend)

**Primary Dependencies**: FastAPI, SQLAlchemy 2.x, alembic, pydantic-settings v2,
itsdangerous (token signing), boto3 (S3-compatible storage), httpx (geocoder),
phonenumbers (WhatsApp validation), Pillow (image validation). Frontend: React,
Vite, react-query, react-router.

**Storage**: Postgres (system of record); S3-compatible object storage (Railway
bucket in prod, MinIO locally) for profile photos.

**Testing**: pytest (unit, no DB; `@pytest.mark.smoke` on live Postgres); vitest +
React Testing Library (frontend).

**Target Platform**: Linux server (Railway, Docker); modern mobile-first browsers.

**Project Type**: Web application (separate `backend/` + `frontend/`).

**Performance Goals**: Tens of users; not a scaling problem. Profile/directory
reads feel instant (well under SC targets). No background jobs in this slice.

**Constraints**: Invite-only — no unauthenticated data access. No account
enumeration. Owner-only roster management. Photos ≤ 5 MB, jpeg/png/webp.

**Scale/Scope**: One graduating class, ~tens of members. ~10 API endpoints, ~5
frontend screens.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | How this plan complies |
|---|---|
| I. Spec-Driven & Trunk-Based | Plan derives from spec 001 on branch `001-member-auth-profiles`; merges to `main`. |
| II. Private, Invite-Only by Default | All data endpoints require a session; roster gate on sign-in; neutral response prevents enumeration (FR-004); no public data routes. |
| III. Self-Service Data Ownership | Mutations limited to `/members/me*`; server resolves the actor from the session — no member can edit another's data (FR-008). |
| IV. Pure Core, Thin Edges | Pure, DB-free units: magic-link token issue/verify, WhatsApp E.164 validation, image validation, geocoder-response → Place parsing. I/O isolated in services/clients. `logging`, never `print()`. |
| V. Provider-Swappable Integrations | `Notifier` (Resend impl now; console impl for dev; WhatsApp later), `Geocoder` (Photon impl), `PhotoStore` (S3 impl) each behind an in-repo interface. |
| VI. Test Discipline | Pure units fully unit-tested; auth/profile/directory paths covered by smoke tests on live Postgres (no DB mocking); ruff + pre-commit gate. |
| Tech Constraints | uv-managed Python 3.13, FastAPI, SQLAlchemy + alembic migrations (no manual DDL), React/Vite, Docker + Railway, `alembic upgrade head` on entrypoint. |

**Result**: PASS — no violations. Complexity Tracking left empty.

## Project Structure

### Documentation (this feature)

```text
specs/001-member-auth-profiles/
├── plan.md              # This file
├── research.md          # Phase 0 — decisions (email, sessions, geocoder, storage, validation)
├── data-model.md        # Phase 1 — entities, fields, validation, state
├── quickstart.md        # Phase 1 — local dev + run instructions
├── contracts/
│   └── rest-api.md      # Phase 1 — endpoint contracts
└── checklists/
    └── requirements.md  # Spec quality checklist (already passing)
```

### Source Code (repository root)

```text
backend/
├── pyproject.toml                 # uv project; ruff + pytest config (mkn10 parity)
├── Dockerfile                     # multi-stage; entrypoint runs alembic upgrade head
├── alembic/                       # migrations (0001 initial schema)
├── src/catchup/
│   ├── config.py                  # pydantic-settings BaseSettings
│   ├── db.py                      # engine + SessionLocal + session_scope
│   ├── models.py                  # member, place, roster_invite, signin_token, session
│   ├── auth/
│   │   ├── tokens.py              # PURE: issue/verify single-use magic-link token
│   │   ├── service.py             # request-link, verify, session create/revoke (DB + Notifier)
│   │   └── deps.py                # FastAPI session dependency (current member or 401)
│   ├── members/
│   │   ├── service.py             # profile read/update, directory, ownership checks
│   │   └── validation.py          # PURE: WhatsApp E.164, image type/size checks
│   ├── places/
│   │   ├── geocoder.py            # Geocoder protocol + Photon client
│   │   └── parse.py               # PURE: geocoder response → Place
│   ├── storage/
│   │   └── photos.py              # PhotoStore protocol + S3 impl
│   ├── notify/
│   │   ├── base.py                # Notifier protocol
│   │   ├── email_resend.py        # Resend impl
│   │   └── console.py             # dev impl (prints link)
│   ├── api/                       # FastAPI routers: auth, members, places
│   ├── cli.py                     # catchup-roster (add/remove/list) — owner-only
│   └── app.py                     # FastAPI app factory + entrypoint
└── tests/
    ├── conftest.py                # live_db + clean_tables + alembic-head fixtures
    ├── test_tokens.py             # unit
    ├── test_validation.py         # unit
    ├── test_place_parse.py        # unit
    └── test_*_smoke.py            # @pytest.mark.smoke (live PG)

frontend/
├── package.json                   # Vite + TS; vitest
├── src/
│   ├── api/                       # typed fetch client + react-query hooks
│   ├── pages/                     # Login, Profile (edit), Directory, MemberDetail
│   ├── components/                # PhotoUpload, PlaceAutocomplete, WhatsAppButton
│   └── main.tsx
└── tests/                         # vitest + RTL
```

**Structure Decision**: Web-application layout (Option 2) — `backend/` (Python,
mkn10 conventions) and `frontend/` (React/TS) side by side in one repo, matching
the design spec. The backend keeps the mkn10 pure-core/thin-edges module split.

## Complexity Tracking

No constitution violations — section intentionally empty.
