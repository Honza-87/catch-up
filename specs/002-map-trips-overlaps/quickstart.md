# Quickstart — Map, Trips & Overlap Detection (slice 002)

Builds on slice 001 (auth, members, profiles). Same toolchain. Adds trips, the map
home screen, the overlap engine, and a scheduled overlap-alert worker. No real
email or cloud needed locally: the console notifier logs the digest.

## Prerequisites

- Slice 001 running locally (members can sign in and set a home location).
- Python 3.13 + `uv`; Node 20+; Docker.

## ⚠️ Local DB port conflict (read before smoke tests)

`docker-compose.dev.yml` maps Postgres to host **5432**, which on this machine is
already taken by the `dokturek`/`umls` stacks (and **5433** is also occupied).
Before bringing up the catch-up DB or running smoke tests, do one of:

- **Remap** the host port — edit `docker-compose.dev.yml` `db.ports` to
  `"5434:5432"` and set `DATABASE_URL=...@localhost:5434/catchup` in `.env`; or
- **Stop** the conflicting containers occupying 5432.

(Captured in project memory; see research §8.)

## 1. Backing services

```bash
# from backend/ — Postgres + MinIO (after resolving the port conflict above)
docker compose -f docker-compose.dev.yml up -d
```

## 2. Backend (schema + run)

```bash
cd backend
uv sync
uv run alembic upgrade head     # applies 0002_trips_overlaps (trip + overlap tables)
uv run uvicorn catchup.app:app --reload   # API on http://localhost:8000
```

No new required env. Optional knobs (sensible defaults): overlap email subject.
`NOTIFIER=console` logs digests; `NOTIFIER=resend` + `RESEND_API_KEY` sends real
mail.

## 3. Frontend (adds the map)

```bash
cd frontend
npm install                     # pulls leaflet + react-leaflet
npm run dev                     # SPA on http://localhost:5173
```

The map home screen (`/`) renders home + trip pins over OpenStreetMap tiles (no API
key) with a linked trips/overlaps panel.

## 4. Run the overlap worker (the scheduled job, run by hand in dev)

```bash
cd backend
uv run catchup-overlap          # one reconcile-and-notify pass, then exits
```

With `NOTIFIER=console`, new-overlap digests print to the backend logs. Run it
again with no data change → no new digest (idempotent; FR-022/023). In production
this is a Railway **cron** service on the same image, scheduled hourly (`0 * * * *`).

## 5. Dev loop to see an overlap

1. Sign in as member A; set a **home** city; add a **trip** to e.g. Lisbon
   (2026-07-01 → 07-10).
2. Sign in as member B; add a trip to **Lisbon** overlapping those dates → expect a
   **strong** trip-trip overlap. Change B's trip to **Porto** (same country) →
   **medium**. Point a trip at A's **home city** → **trip-home**.
3. Run `uv run catchup-overlap` → both members get one digest email/log listing
   their new overlaps; the overlap appears in `GET /overlaps/me` and is highlighted
   on the map.
4. Re-run the worker unchanged → no duplicate alert.

## 6. Tests

```bash
cd backend
uv run pytest -m "not smoke"    # unit: overlap engine (table-driven), trip date validation — NO DB
uv run pytest -m smoke          # smoke: trip CRUD + ownership, overlap runner reconcile/notify (live Postgres)
uv run ruff check . && uv run ruff format --check .

cd ../frontend
npm test                        # vitest + RTL: trip form, panel↔map linking, overlap list
```

## Acceptance walk-through (maps to spec)

- **US1 (P1)**: add/edit/delete own trip; inverted dates rejected; cannot edit
  another member's trip; geocoder-down → manual city/country entry still works.
- **US2 (P2)**: map shows homes + trips distinctly; tap a trip in the panel →
  pin highlights, and vice versa; overlaps listed above upcoming trips.
- **US3 (P3)**: same-city = strong, same-country/diff-city = medium; trip↔home
  matched; disjoint dates → none; home↔home → none; resident-away → no trip-home;
  pair shown once, strongest first.
- **US4 (P4)**: new overlap → one digest per affected member; re-run → no repeat;
  simulated send failure (bad `RESEND_API_KEY`) leaves overlap un-notified → retried
  next run.
