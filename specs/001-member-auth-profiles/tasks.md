# Tasks: Members, Magic-Link Auth & Profiles

**Input**: Design documents from `specs/001-member-auth-profiles/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/rest-api.md

**Tests**: INCLUDED — the project constitution (Principle VI, Test Discipline)
mandates unit tests for pure logic and `@pytest.mark.smoke` tests on live Postgres.

**Organization**: Tasks grouped by user story (US1 P1, US2 P1, US3 P2) for
independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on incomplete tasks)
- Paths follow the web-app layout from plan.md: `backend/`, `frontend/`

---

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Create monorepo structure (`backend/`, `frontend/`) per plan.md
- [X] T002 [P] Initialize backend uv project in `backend/pyproject.toml` (name `catchup`, py3.13; deps fastapi, sqlalchemy, alembic, psycopg[binary], pydantic-settings, itsdangerous, boto3, httpx, phonenumbers, pillow, typer; dev: pytest, pytest-cov, ruff, pre-commit; `[project.scripts] catchup-roster`; ruff line-length 120 + `E/W/F/I/B/UP/SIM`; pytest `--strict-markers` + `smoke` marker)
- [X] T003 [P] Initialize frontend Vite+TS project in `frontend/package.json` (react, react-dom, react-router-dom, @tanstack/react-query; dev: vite, typescript, vitest, @testing-library/react, jsdom)
- [X] T004 [P] Add `ruff` + `ruff-format` hooks to `.pre-commit-config.yaml`
- [X] T005 [P] Create `backend/docker-compose.dev.yml` (Postgres + MinIO)
- [X] T006 [P] Create `backend/.env.example` with all env vars from quickstart.md
- [X] T007 [P] Implement settings in `backend/src/catchup/config.py` (pydantic-settings: DATABASE_URL, SESSION_SECRET, NOTIFIER, RESEND_API_KEY, GEOCODER_URL, S3_*, MAGIC_LINK_TTL_MINUTES, cookie flags)
- [X] T008 [P] Implement `backend/src/catchup/db.py` (engine + SessionLocal + `session_scope`)
- [X] T009 [P] Configure stdlib logging via `LOG_LEVEL` in `backend/src/catchup/logging_config.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: No user story work begins until this phase is complete.

- [X] T010 Define SQLAlchemy models in `backend/src/catchup/models.py` (`member`, `place`, `roster_invite`, `signin_token`, `session`) per data-model.md
- [X] T011 Init alembic in `backend/alembic/` (env.py wired to config) + migration `0001_initial` creating all 5 tables + indexes (depends T010)
- [X] T012 [P] Notifier interface + impls: `backend/src/catchup/notify/base.py` (Protocol), `console.py` (dev), `email_resend.py` (Resend)
- [X] T013 [P] Geocoder interface + Photon impl in `backend/src/catchup/places/geocoder.py`
- [X] T014 [P] PhotoStore interface + S3 impl in `backend/src/catchup/storage/photos.py`
- [X] T015 FastAPI app factory in `backend/src/catchup/app.py` (error-shape handler, CORS, router registration, startup) (depends T007, T008)
- [X] T016 Session auth dependency (current member or 401) in `backend/src/catchup/auth/deps.py` (depends T010, T008)
- [X] T017 [P] Frontend skeleton: typed fetch client + error shape in `frontend/src/api/client.ts`, react-query provider + router in `frontend/src/main.tsx`

**Checkpoint**: Foundation ready — user stories can begin.

---

## Phase 3: User Story 1 — Invited classmate signs in (Priority: P1) 🎯 MVP

**Goal**: Roster-gated, passwordless magic-link sign-in with a server session.
**Independent Test**: Seed a roster email, request a link, follow it → signed in with
an empty profile; non-roster email → same neutral response; reused/expired link → denied.

### Tests for User Story 1

- [X] T018 [P] [US1] Unit tests for token issue/verify (expiry, single-use, hash) in `backend/tests/test_tokens.py`
- [X] T019 [P] [US1] Smoke test sign-in flow (roster gate, neutral 202, used/expired link denied, member created on first login) in `backend/tests/test_auth_smoke.py`

### Implementation for User Story 1

- [X] T020 [P] [US1] PURE token issue/verify (random token, hash, 15-min TTL, single-use) in `backend/src/catchup/auth/tokens.py`
- [X] T021 [US1] Auth service (request-link → roster check + create signin_token + send via Notifier; verify → validate + upsert member + create session; logout → revoke) in `backend/src/catchup/auth/service.py` (depends T020, T010, T012)
- [X] T022 [US1] Auth routers (POST /auth/request-link neutral 202, GET /auth/callback, POST /auth/logout, GET /auth/me) in `backend/src/catchup/api/auth.py` (depends T021, T016)
- [X] T023 [P] [US1] `catchup-roster` Typer CLI (add/remove/list) in `backend/src/catchup/cli.py` (depends T010, T008)
- [X] T024 [US1] Register auth router + rate-limit request-link (default 5/email/hour, 20/IP/hour, configurable) in `backend/src/catchup/app.py` (depends T022)
- [X] T025 [P] [US1] Frontend Login page + "check inbox" + callback handling + `useAuth` hook in `frontend/src/pages/Login.tsx`, `frontend/src/api/auth.ts`

**Checkpoint**: US1 fully functional — a real classmate can sign in. MVP demoable.

---

## Phase 4: User Story 2 — Member maintains their own profile (Priority: P1)

**Goal**: Self-service edit of own profile (name, structured home, job, company,
WhatsApp, note, photo) with ownership enforcement.
**Independent Test**: As a signed-in member, fill every field + upload a photo, reload
→ persists; editing another member is refused.

### Tests for User Story 2

- [X] T026 [P] [US2] Unit tests for validation (WhatsApp E.164, image type/size) in `backend/tests/test_validation.py`
- [X] T027 [P] [US2] Unit tests for geocoder→Place parsing in `backend/tests/test_place_parse.py`
- [X] T028 [P] [US2] Smoke test profile edit + photo upload + ownership refusal in `backend/tests/test_members_smoke.py`

### Implementation for User Story 2

- [X] T029 [P] [US2] PURE validation (WhatsApp E.164 via phonenumbers; image type/size) in `backend/src/catchup/members/validation.py`
- [X] T030 [P] [US2] PURE geocoder response → Place in `backend/src/catchup/places/parse.py`
- [X] T031 [US2] Places service + `GET /places/search` proxy (Photon) with place dedupe/upsert in `backend/src/catchup/api/places.py` (depends T013, T030, T010)
- [X] T032 [US2] Members service: read/update own profile + home-place upsert (ownership-checked) in `backend/src/catchup/members/service.py` (depends T010, T029)
- [X] T033 [US2] `PATCH /members/me` router in `backend/src/catchup/api/members.py` (depends T032, T016)
- [X] T034 [US2] Photo endpoints `POST`/`DELETE /members/me/photo` (validate + PhotoStore, set/clear photo_url) in `backend/src/catchup/api/members.py` (depends T014, T029, T032)
- [X] T035 [US2] Register members + places routers in `backend/src/catchup/app.py` (depends T033, T031)
- [X] T036 [P] [US2] Frontend Profile edit page + `PhotoUpload` + `PlaceAutocomplete` in `frontend/src/pages/Profile.tsx`, `frontend/src/components/`

**Checkpoint**: US1 + US2 work — members can get in and curate their profile.

---

## Phase 5: User Story 3 — Member browses the class directory (Priority: P2)

**Goal**: Signed-in members see all joined classmates and reach them on WhatsApp.
**Independent Test**: With two joined members, sign in as one, open the other's
profile → all shared fields visible, WhatsApp opens `wa.me`.

### Tests for User Story 3

- [ ] T037 [P] [US3] Smoke test directory list (joined only) + member detail in `backend/tests/test_directory_smoke.py`

### Implementation for User Story 3

- [ ] T038 [US3] Extend members service: directory list (joined only, FR-016) + get-by-id in `backend/src/catchup/members/service.py` (depends T032)
- [ ] T039 [US3] `GET /members` + `GET /members/{id}` routers in `backend/src/catchup/api/members.py` (depends T038)
- [ ] T040 [P] [US3] Frontend Directory + MemberDetail pages + `WhatsAppButton` (`wa.me`) in `frontend/src/pages/Directory.tsx`, `frontend/src/pages/MemberDetail.tsx`, `frontend/src/components/WhatsAppButton.tsx`

**Checkpoint**: All three stories independently functional.

---

## Phase 6: Polish & Cross-Cutting

- [ ] T041 [P] Multi-stage `backend/Dockerfile` + `backend/scripts/entrypoint.sh` (`alembic upgrade head` before serving)
- [ ] T042 [P] Railway config `railway.json` (api + web services, Postgres, object-storage bucket)
- [ ] T043 [P] Frontend production build config + static-serve notes in `frontend/`
- [ ] T044 Run `quickstart.md` end-to-end and fix gaps
- [ ] T045 [P] Ensure `ruff check`, `ruff format --check`, `pytest`, `vitest` all green; document `pre-commit install`
- [ ] T046 [P] Write `README.md` (run + deploy, mkn10-style)
- [ ] T047 [P] Frontend component tests (vitest + RTL): Login flow, Profile form validation, Directory render + `wa.me` link in `frontend/tests/`

---

## Dependencies & Execution Order

- **Setup (P1)** → **Foundational (P2)** blocks everything → **User stories (P3–P5)**.
- US1 (P1) and US2 (P1) both depend only on Foundational; US2 can proceed alongside
  US1 (different files), but sign-in (US1) is needed to exercise US2/US3 manually.
- US3 (P2) reuses the members service from US2 (T038 extends T032).
- **Polish (P6)** after the desired stories.

### Within a story
Tests written first and FAIL → pure units → services → endpoints → register → frontend.

### Parallel opportunities
- Setup: T002–T009 mostly [P].
- Foundational: T012, T013, T014, T017 in parallel.
- US1: T018/T019 (tests) parallel; T020 + T023 + T025 parallel.
- US2: T026/T027/T028 parallel; T029 + T030 + T036 parallel.

## Parallel Example: User Story 1

```bash
# Tests first (must fail):
Task: "Unit tests for tokens in backend/tests/test_tokens.py"
Task: "Smoke test sign-in flow in backend/tests/test_auth_smoke.py"
# Then parallel impl on different files:
Task: "PURE tokens in backend/src/catchup/auth/tokens.py"
Task: "catchup-roster CLI in backend/src/catchup/cli.py"
Task: "Frontend Login page in frontend/src/pages/Login.tsx"
```

## Implementation Strategy

### MVP (US1 only)
Setup → Foundational → US1 → validate sign-in independently → demo. A working,
invite-only passwordless login is the smallest shippable increment.

### Incremental delivery
Add US2 (profiles) → validate → demo. Add US3 (directory) → validate → demo. Each
story adds value without breaking the prior. Then Phase 6 to deploy on Railway.

## Notes
- Commit after each task or logical group (Spec Kit `after_implement` auto-commit).
- Verify tests fail before implementing (Constitution VI).
- No `print()` in library code; pure modules import no DB/HTTP/storage.
