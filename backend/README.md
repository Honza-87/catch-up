# catch-up backend

FastAPI + SQLAlchemy + Postgres backend for catch-up. Slice 001: members,
magic-link auth, profiles. Slice 002: trips, the map data, the overlap engine, and
a scheduled overlap-alert worker. See `../specs/002-map-trips-overlaps/quickstart.md`
for the slice-002 dev loop and `../CLAUDE.md` for conventions.

## Modules

- `trips/` — pure date validation (`validation.py`) + self-service CRUD with
  server-side ownership (`service.py`); routes in `api/trips.py`.
- `overlaps/` — **pure** graded-overlap engine (`detection.py`, no DB/IO), the
  reconcile + digest-notify runner (`runner.py`), and the `catchup-overlap` cron
  worker (`worker.py`); read-only routes in `api/overlaps.py`.
- `places/service.py` — shared place dedup (`upsert_place`) used by members + trips.
- `notify/` — `Notifier` gains `send_overlap_digest` (console logs it, Resend mails it).

## Quick commands

```bash
uv sync
docker compose -f docker-compose.dev.yml up -d   # Postgres + MinIO
uv run alembic upgrade head
uv run catchup-roster add you@example.com
uv run uvicorn catchup.app:app --reload

uv run catchup-overlap         # one overlap reconcile-and-notify pass, then exit
                               # (Railway runs this hourly as a cron service)

uv run pytest -m "not smoke"   # unit tests (no DB): overlap engine, trip validation
uv run pytest -m smoke         # smoke tests (live Postgres): trip CRUD, runner, endpoints
uv run ruff check . && uv run ruff format --check .
```
