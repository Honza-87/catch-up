# Implementation Plan: Map, Trips & Overlap Detection

**Branch**: `002-map-trips-overlaps` | **Date**: 2026-06-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/002-map-trips-overlaps/spec.md`

## Summary

Second slice of `catch-up`, built directly on the 001 foundation (members,
magic-link auth, profiles with normalized home places, geocoder, `Notifier`). It
adds: per-member **trips** (destination + inclusive date range, self-service CRUD
with server-side ownership); a **map home screen** (react-leaflet) showing home
pins + trip pins + overlap highlights linked to a trips/overlaps panel; a **pure,
DB-free overlap engine** that grades matches (strong = same city, medium = same
country/different city) across trip↔trip and trip↔home, with a member's home
treated as an always-present interval *minus their own trip windows*; and a
**scheduled worker** that reconciles overlaps and sends one **digest email per
affected member per run** through the `Notifier`, alerting only on newly appeared
overlaps. No new auth, storage, or geocoder machinery — those are reused.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript 5.x (frontend) — unchanged
from 001.

**Primary Dependencies**: existing — FastAPI, SQLAlchemy 2.x, alembic,
pydantic-settings v2, httpx, typer. New backend: none required (pure stdlib date
math for the overlap engine). New frontend: `leaflet` + `react-leaflet` (map),
over the existing React + Vite + react-query + react-router stack.

**Storage**: Postgres (system of record). Two new tables — `trip`, `overlap` —
via alembic migration `0002`. Reuses the existing `place` table for destinations.
No object-storage changes.

**Testing**: pytest — exhaustive **unit** tests for the pure overlap engine (no
DB) plus `@pytest.mark.smoke` tests on live Postgres for trip CRUD, the
reconcile-and-notify runner, and the new endpoints. vitest + RTL for the trip
form, panel↔map linking, and overlap list (light).

**Target Platform**: Linux server (Railway, Docker); mobile-first browsers. Adds a
**Railway scheduled (cron) service** invoking the overlap worker.

**Project Type**: Web application (existing `backend/` + `frontend/`).

**Performance Goals**: Tens of members → at most a few hundred trips. Overlap
detection is O(intervals²) over a tiny set; a full recompute is milliseconds. New
overlaps reach members within one recompute cycle (cadence default **hourly**,
well inside the SC-002 24-hour bound).

**Constraints**: Invite-only — every new endpoint requires a session (FR-026). No
member may mutate another's trip (FR-004). The overlap engine MUST stay pure (no
DB/network) per Constitution IV. Alerts MUST flow through the swappable `Notifier`
(FR-025 / Constitution V). Inclusive `[start, end]` day ranges throughout.

**Scale/Scope**: One class, ~tens of members. ~6 new API endpoints; 1 new
frontend screen (map home) + trip form + member drawer; 1 scheduled worker.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | How this plan complies |
|---|---|
| I. Spec-Driven & Trunk-Based | Plan derives from spec 002 on branch `002-map-trips-overlaps`; merges to `main`, auto-deploys. |
| II. Private, Invite-Only by Default | Every trip/map/overlap route depends on `get_current_member` → 401 otherwise (FR-026); no public data routes added. |
| III. Self-Service Data Ownership | Trip create/edit/delete resolve the actor from the session; service refuses to mutate a trip whose `member_id` ≠ caller (FR-004). Overlaps are computed, never user-written. |
| IV. Pure Core, Thin Edges | `overlaps/detection.py` is a pure function `(presences) → list[Overlap]` with zero imports of db/httpx; persistence + notify live in `overlaps/runner.py`; the worker is the only scheduler edge. `logging`, never `print()`. |
| V. Provider-Swappable Integrations | Alerts go through the existing `Notifier` interface, extended with one `send_overlap_digest` method implemented by both `ConsoleNotifier` and `ResendNotifier`; detection knows nothing about email. Geocoder/place reuse unchanged. |
| VI. Test Discipline | Pure overlap engine gets table-driven unit tests (city/country tiers, trip↔home, home suppression, date intersect/disjoint, pair ordering, self-exclusion); trip CRUD + runner reconcile/notify covered by smoke tests on live Postgres (no DB mocking). ruff + pre-commit gate. |
| Tech Constraints | uv-managed Python 3.13; schema via alembic migration `0002` (no manual DDL); React/Vite + react-leaflet; Docker + Railway; existing `alembic upgrade head` entrypoint covers the new tables; worker shipped as a console-script run by Railway cron. |

**Result**: PASS — no violations. Complexity Tracking left empty.

## Project Structure

### Documentation (this feature)

```text
specs/002-map-trips-overlaps/
├── plan.md              # This file
├── research.md          # Phase 0 — decisions (interval algebra, cadence, worker, notifier, map lib)
├── data-model.md        # Phase 1 — trip + overlap entities, identity/dedup, state
├── quickstart.md        # Phase 1 — local dev (DB port!), worker run, smoke
├── contracts/
│   └── rest-api.md      # Phase 1 — trip/overlap endpoint contracts
└── checklists/
    └── requirements.md  # Spec quality checklist (passing)
```

### Source Code (repository root)

```text
backend/src/catchup/
├── models.py                 # + Trip, Overlap models (extend existing)
├── config.py                 # + overlap email subject / lookahead knobs (minimal)
├── api/
│   ├── schemas.py            # + TripSchema/Create/Update, OverlapSchema; MemberDetail gains trips
│   ├── trips.py              # NEW router: GET /trips, /trips/me, POST/PATCH/DELETE
│   └── overlaps.py           # NEW router: GET /overlaps/me
├── trips/
│   ├── __init__.py
│   ├── service.py            # NEW: own-trip CRUD, ownership checks, place upsert reuse
│   └── validation.py         # NEW pure: date-range validation (end >= start)
├── places/
│   └── service.py            # NEW: extract shared _upsert_place from members.service
├── overlaps/
│   ├── __init__.py
│   ├── detection.py          # NEW pure: presences → graded overlaps (NO db/io)
│   ├── runner.py             # NEW: load → detect → reconcile rows → digest-notify
│   └── worker.py             # NEW: `catchup-overlap` console entrypoint (typer)
└── notify/
    ├── base.py               # + send_overlap_digest on Notifier protocol
    ├── console.py            # + impl (logs digest)
    └── email_resend.py       # + impl (renders + sends digest email)

backend/alembic/versions/
└── 0002_trips_overlaps.py    # NEW migration

backend/tests/
├── test_overlap_detection.py # NEW unit (pure engine, table-driven)
├── test_trip_validation.py   # NEW unit (date range)
├── test_trips_smoke.py       # NEW smoke (CRUD + ownership)
└── test_overlap_runner_smoke.py # NEW smoke (reconcile + notify once + retry)

frontend/src/
├── api/{trips.ts, overlaps.ts}   # NEW query/mutation hooks
├── pages/Home.tsx                # NEW map home (combined view) — becomes landing
├── components/
│   ├── MapView.tsx               # NEW react-leaflet map (home/trip/overlap markers)
│   ├── TripsOverlapsPanel.tsx    # NEW linked side panel / bottom sheet
│   ├── TripForm.tsx              # NEW add/edit trip (reuses PlaceAutocomplete)
│   └── MemberDrawer.tsx          # NEW classmate profile + trips + wa.me
└── types.ts                      # + Trip, Overlap types
```

**Structure Decision**: Reuse the established 001 web-app layout and mkn10-style
module separation (pure logic modules never import the DB; services/runners/clients
own I/O). New domain code is grouped into `trips/` and `overlaps/` packages; the
overlap engine is isolated in `overlaps/detection.py` so it is unit-testable
without Postgres, and the scheduled side-effect lives only in `overlaps/worker.py`
+ `overlaps/runner.py`. A small `places/service.py` is introduced to share the
existing `_upsert_place` between members (home) and trips (destination) rather than
duplicating it.

## Complexity Tracking

> No constitution violations. Section intentionally empty.
