---
description: "Task list for slice 002 — Map, Trips & Overlap Detection"
---

# Tasks: Map, Trips & Overlap Detection

**Input**: Design documents from `specs/002-map-trips-overlaps/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/rest-api.md, quickstart.md

**Tests**: INCLUDED — Constitution VI (pure logic = unit tests, integration = `@pytest.mark.smoke` on live Postgres, no DB mocking) and SC-008 ("verified by the detection test suite") require them. Test tasks precede their implementation (write-and-fail first).

**Builds on slice 001** (merged): members, magic-link auth, profiles, `place` table, geocoder, `Notifier`, `get_current_member`, `PlaceAutocomplete`. Reused, not rebuilt.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1–US4 (maps to spec user stories). Setup/Foundational/Polish carry no story label.

## Path Conventions

Web app: backend at `backend/src/catchup/`, backend tests at `backend/tests/`, frontend at `frontend/src/`, frontend tests at `frontend/tests/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Dependencies + entrypoints needed before feature work.

- [ ] T001 [P] Add `leaflet`, `react-leaflet`, and `@types/leaflet` to `frontend/package.json` and install (map stack, OSM tiles, no API key)
- [ ] T002 [P] Add `catchup-overlap = "catchup.overlaps.worker:main"` under `[project.scripts]` in `backend/pyproject.toml` (scheduled-worker console entry)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared schema + place-dedup refactor that ALL stories build on.

**⚠️ CRITICAL**: No user story work begins until this phase is complete.

- [ ] T003 Add `Trip` and `Overlap` SQLAlchemy models to `backend/src/catchup/models.py` per data-model.md (Trip: member_id FK CASCADE, place_id FK, start_date/end_date Date, note, created_at; Overlap: member_a_id<member_b_id, kind, strength, place_id nullable FK, country_code, scope_key, start/end_date, notified_at, created_at)
- [ ] T004 Create migration `backend/alembic/versions/0002_trips_overlaps.py` creating `trip` + `overlap` tables with `UNIQUE (member_a_id, member_b_id, kind, scope_key)`, indexes on `trip.member_id`, `overlap.member_a_id`, `overlap.member_b_id`, and member-delete cascade (depends on T003; downgrade drops both)
- [ ] T005 Create `backend/src/catchup/places/service.py` and move `_upsert_place` there from `backend/src/catchup/members/service.py`; update `members/service.py` to import it (single source of place dedup, shared by members + trips)

**Checkpoint**: Schema + shared place service ready — user stories can begin.

---

## Phase 3: User Story 1 - Plan a trip (Priority: P1) 🎯 MVP

**Goal**: Members add/edit/delete their own trips (destination + inclusive dates + optional note); ownership enforced server-side; inverted dates rejected; geocoder-down falls back to manual entry.

**Independent Test**: Sign in, add a trip, see it in own list, edit it, delete it; confirm 403 editing another member's trip and 422 on `end_date < start_date`.

### Tests (write first, must fail)

- [ ] T006 [P] [US1] Unit test trip date-range validation (end ≥ start; equal allowed) in `backend/tests/test_trip_validation.py`
- [ ] T007 [P] [US1] Smoke test trip CRUD + ownership (create/edit/delete own; 403 other member's trip; 422 inverted dates; place dedup; 401 when unauthenticated on `POST/PATCH/DELETE /trips` and `GET /trips/me`) in `backend/tests/test_trips_smoke.py`

### Implementation

- [ ] T008 [P] [US1] Pure date-range validation (`validate_trip_dates`) in `backend/src/catchup/trips/validation.py` (+ `backend/src/catchup/trips/__init__.py`)
- [ ] T009 [P] [US1] Add `TripSchema`, `TripCreate`, `TripUpdate` (partial via `model_fields_set`) to `backend/src/catchup/api/schemas.py`
- [ ] T010 [US1] Implement trip service — own-trip create/edit/delete, ownership guard (raise `forbidden` 403 when `member_id` ≠ caller), place upsert via `places.service` — in `backend/src/catchup/trips/service.py` (depends on T005, T008)
- [ ] T011 [US1] Implement trips router `GET /trips/me`, `POST /trips`, `PATCH /trips/{id}`, `DELETE /trips/{id}` (all `Depends(get_current_member)`) in `backend/src/catchup/api/trips.py` (depends on T009, T010)
- [ ] T012 [US1] Register trips router in `_register_routers` in `backend/src/catchup/app.py`
- [ ] T013 [P] [US1] Add `Trip` type to `frontend/src/types.ts`
- [ ] T014 [P] [US1] Add trip API hooks (`listMine`, `create`, `update`, `delete`) in `frontend/src/api/trips.ts`
- [ ] T015 [US1] Build `TripForm` (destination via existing `PlaceAutocomplete`, start/end dates, note, client date validation) in `frontend/src/components/TripForm.tsx` (depends on T013, T014)
- [ ] T016 [US1] Add "My trips" management (list own upcoming trips + add/edit/delete via `TripForm`) to `frontend/src/pages/Profile.tsx` (depends on T015)
- [ ] T017 [P] [US1] Frontend test for `TripForm` (valid submit; inverted-date error shown; manual city/country entry saves a trip when destination lookup returns no results — FR-007) in `frontend/tests/TripForm.test.tsx`

**Checkpoint**: US1 fully functional — members manage their own trips. MVP demoable.

---

## Phase 4: User Story 2 - See the class on a world map (Priority: P2)

**Goal**: Map home screen shows every home + trip destination (visually distinct), with a linked trips/overlaps panel; selecting a panel item highlights its pin and vice versa; overlaps listed above upcoming trips.

**Independent Test**: With several homes + trips present, load the home screen; homes and trips both appear and are distinguishable; tap a trip in the panel → its pin highlights, and tapping a pin surfaces the trip/member.

### Tests (write first, must fail)

- [ ] T018 [P] [US2] Smoke test `GET /trips` (all upcoming, excludes past `end_date < today`, sorted), 401 when unauthenticated on `GET /trips`, and `MemberDetail` embeds upcoming `trips` in `backend/tests/test_map_smoke.py`

### Implementation

- [ ] T019 [US2] Add `GET /trips` (all members' upcoming trips, member+place embedded, sorted by start_date) to `backend/src/catchup/api/trips.py` (depends on T011)
- [ ] T020 [US2] Embed upcoming trips in member detail — add `trips: list[TripSchema]` to `MemberDetail` in `backend/src/catchup/api/schemas.py` and load them in `get_member` in `backend/src/catchup/members/service.py`
- [ ] T021 [P] [US2] Add `listAllUpcoming` trip hook in `frontend/src/api/trips.ts`
- [ ] T022 [P] [US2] `MapView` (react-leaflet + OSM tiles; distinct home/trip/overlap markers; fit-to-bounds; exposes selected-id ↔ highlight) in `frontend/src/components/MapView.tsx`
- [ ] T023 [P] [US2] `TripsOverlapsPanel` (overlaps section pinned above upcoming-trips list; selectable rows emit selection) in `frontend/src/components/TripsOverlapsPanel.tsx`
- [ ] T024 [P] [US2] `MemberDrawer` (classmate profile + trips + `wa.me` button, reusing `WhatsAppButton`) in `frontend/src/components/MemberDrawer.tsx`
- [ ] T025 [US2] `Home` page composing `MapView` + `TripsOverlapsPanel` with two-way selection linking (tap trip ↔ highlight pin; tap pin → scroll/open drawer), querying `GET /members` + `GET /trips` in `frontend/src/pages/Home.tsx` (depends on T021, T022, T023, T024)
- [ ] T026 [US2] Make `Home` the landing route + update nav in `frontend/src/App.tsx` (depends on T025)
- [ ] T027 [P] [US2] Frontend test panel↔map linking (select trip → marker highlighted) in `frontend/tests/HomeLinking.test.tsx`

**Checkpoint**: US1 + US2 work independently. Overlaps section renders (empty until US3).

---

## Phase 5: User Story 3 - Discover overlaps (Priority: P3)

**Goal**: Graded overlaps (strong = same city, medium = same country/diff city) across trip↔trip and trip↔home, home suppressed while the resident is away; members view their own overlaps strongest-first; computed by a scheduled recompute.

**Independent Test**: Two members same city/overlapping dates → strong; change one to another city same country → medium; trip into a third member's home city → trip-home; disjoint dates → none; home↔home → none; resident-away → no trip-home; pair shown once, strongest first.

### Tests (write first, must fail)

- [ ] T028 [P] [US3] Table-driven unit tests for the pure engine in `backend/tests/test_overlap_detection.py`: same/diff city, same/diff country, trip↔trip, trip↔home (strong + medium), date intersect/disjoint, home suppression + resident-away, home↔home excluded, self excluded, unordered-pair canonicalization, strongest-first ordering
- [ ] T029 [P] [US3] Smoke test runner reconcile in `backend/tests/test_overlap_runner_smoke.py`: inserts new overlaps, deletes vanished ones, updates dates on a still-matching overlap (rows keyed by `(a,b,kind,scope_key)`); plus `GET /overlaps/me` returns the caller's overlaps strong-first and 401 when unauthenticated

### Implementation

- [ ] T030 [P] [US3] Pure overlap engine + value objects (`Presence`, `DetectedOverlap`, `detect_overlaps(presences, today)`) — interval intersection, home = window minus resident's own trips, scope_key derivation, NO db/io — in `backend/src/catchup/overlaps/detection.py` (+ `backend/src/catchup/overlaps/__init__.py`)
- [ ] T031 [US3] Overlap runner reconcile — load homes + upcoming trips, build presences, call `detect_overlaps`, upsert/delete `overlap` rows by `scope_key` identity (keep `notified_at` on date-shift) — in `backend/src/catchup/overlaps/runner.py` (depends on T030)
- [ ] T032 [US3] Worker entrypoint `catchup-overlap` (typer `main` → run reconcile pass, then exit) in `backend/src/catchup/overlaps/worker.py` (depends on T031, T002)
- [ ] T033 [P] [US3] Add `OverlapSchema` (other_member resolved, place nullable for medium) to `backend/src/catchup/api/schemas.py`
- [ ] T034 [US3] Overlaps router `GET /overlaps/me` (strong-first, then start_date; resolves the non-caller member) in `backend/src/catchup/api/overlaps.py` and register it in `backend/src/catchup/app.py` (depends on T033)
- [ ] T035 [P] [US3] Add `Overlap` type + overlaps API hook (`listMine`) in `frontend/src/types.ts` and `frontend/src/api/overlaps.ts`
- [ ] T036 [US3] Wire overlaps into `TripsOverlapsPanel` (strong-first list) and overlap-place highlights on `MapView`, querying `GET /overlaps/me` from `Home` in `frontend/src/components/TripsOverlapsPanel.tsx` + `frontend/src/components/MapView.tsx` (depends on T022, T023, T035)
- [ ] T037 [P] [US3] Frontend test overlap list ordering (strong before medium) in `frontend/tests/OverlapList.test.tsx`

**Checkpoint**: All three in-app stories functional. Overlaps visible and graded; recompute runs via the worker.

---

## Phase 6: User Story 4 - Get alerted to new overlaps (Priority: P4)

**Goal**: New overlaps trigger one digest email per affected member per run via the swappable `Notifier`; alert each overlap identity once; retry on send failure; channel-swappable.

**Independent Test**: Create a trip forming a new overlap → run worker → exactly one digest per affected member; rerun unchanged → no repeat; force send failure → overlap stays un-notified and retries next run.

### Tests (write first, must fail)

- [ ] T038 [P] [US4] Smoke test runner notify in `backend/tests/test_overlap_notify_smoke.py`: one digest per member per run, no re-alert on rerun (notified_at stamped), failed send leaves `notified_at` NULL for retry, reappearance re-alerts (overlap removed → recompute deletes it → same-identity overlap re-added → fresh digest) — uses a stub Notifier capturing/raising

### Implementation

- [ ] T039 [P] [US4] Extend `Notifier` protocol with `send_overlap_digest(email, member_name, overlaps)` + `OverlapDigestItem` dataclass in `backend/src/catchup/notify/base.py`
- [ ] T040 [P] [US4] Implement `send_overlap_digest` in `ConsoleNotifier` (logs the digest) in `backend/src/catchup/notify/console.py`
- [ ] T041 [P] [US4] Implement `send_overlap_digest` in `ResendNotifier` (render text/HTML digest, send) in `backend/src/catchup/notify/email_resend.py`
- [ ] T042 [US4] Add notify step to runner — group `notified_at IS NULL` rows by member, send one digest per member via `get_notifier()`, stamp `notified_at` only after a member's send succeeds, leave NULL on failure; call it after reconcile in the worker — in `backend/src/catchup/overlaps/runner.py` (depends on T031, T039, T040, T041)
- [ ] T043 [US4] Add a Railway scheduled (cron) service running `catchup-overlap` hourly (`0 * * * *`) sharing the API image + `DATABASE_URL`/notifier env in `backend/railway.json`; document provisioning in `specs/002-map-trips-overlaps/quickstart.md` (depends on T032, T042)

**Checkpoint**: Full feature — members are proactively alerted to new overlaps.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T044 [P] Update `backend/README.md` (trips/overlaps modules, worker, `catchup-overlap`) and frontend usage notes
- [ ] T045 [P] Mobile: render `TripsOverlapsPanel` as a swipe-up bottom sheet on small screens (desktop side panel unchanged) in `frontend/src/components/TripsOverlapsPanel.tsx`
- [ ] T046 Run full gates: `uv run pytest -m "not smoke"`, `uv run pytest -m smoke`, `uv run ruff check . && uv run ruff format --check .`, `npm test`; fix failures
- [ ] T047 Run `specs/002-map-trips-overlaps/quickstart.md` end-to-end (incl. DB-port remap + worker dev loop)

---

## Dependencies & Execution Order

### Phase dependencies

- **Setup (P1)**: no deps — start immediately.
- **Foundational (P2)**: after Setup — **blocks all stories** (models + migration + place service).
- **US1 (P3)**: after Foundational. No dependency on other stories. ← MVP.
- **US2 (P4)**: after Foundational. Backend `GET /trips` builds on US1's `api/trips.py` (T019 → T011). Frontend map is independently testable with homes+trips.
- **US3 (P5)**: after Foundational. Frontend wiring reuses US2's `MapView`/panel (T036 → T022/T023); backend engine/runner/API are independent of US1/US2.
- **US4 (P6)**: after US3 (notify extends US3's runner, T042 → T031).
- **Polish (P7)**: after all targeted stories.

### Within a story

Tests (write-and-fail) → models/pure logic → services/runner → endpoints/worker → frontend → integration.

### Parallel opportunities

- Setup: T001 ∥ T002.
- US1 tests T006 ∥ T007; then T008 ∥ T009 ∥ T013 ∥ T014 (different files); T017 ∥ later UI.
- US2: T021 ∥ T022 ∥ T023 ∥ T024 (distinct files) before T025 composes them.
- US3 tests T028 ∥ T029; engine T030 ∥ schema T033 ∥ frontend types T035.
- US4: T039 ∥ T040 ∥ T041 before T042 wires them.
- Different stories can run in parallel across developers once Foundational is done (mind the T019→T011 and T036→T022/23 and T042→T031 cross-links).

---

## Parallel Example: User Story 1

```bash
# Tests first (fail), in parallel:
Task: "Unit test trip date validation in backend/tests/test_trip_validation.py"   # T006
Task: "Smoke test trip CRUD + ownership in backend/tests/test_trips_smoke.py"      # T007

# Then independent implementation files in parallel:
Task: "Pure date validation in backend/src/catchup/trips/validation.py"           # T008
Task: "Trip schemas in backend/src/catchup/api/schemas.py"                         # T009
Task: "Trip type in frontend/src/types.ts"                                         # T013
Task: "Trip API hooks in frontend/src/api/trips.ts"                                # T014
```

---

## Implementation Strategy

### MVP first (US1 only)

1. Phase 1 Setup → 2. Phase 2 Foundational (CRITICAL) → 3. Phase 3 US1 → **STOP & validate** trips CRUD independently → demo. Class can record travel plans even before map/overlaps exist.

### Incremental delivery

Foundation → US1 (trips, MVP) → US2 (map) → US3 (overlaps, the payoff) → US4 (email alerts). Each ships value without breaking prior stories.

### Notes

- Pure engine (T030) stays import-clean of db/httpx — it is the heart of the product (Constitution IV) and the most-tested unit (T028).
- The home-suppression interval math (research §1) is the one tricky bit — cover resident-away + disjoint + both trip↔home tiers explicitly in T028.
- Commit after each task or logical group. Verify each story's tests fail before implementing.
- ⚠️ Smoke tests need live Postgres on a free port — remap the dev DB off 5432/5433 first (quickstart §⚠️).
