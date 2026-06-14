# catch-up

A private, invite-only web app for one high-school graduating class to track where
members are in the world, what they do, and (later) their travel plans — so they can
spot when they'll be in the same place and plan meet-ups.

Built with the same spec-driven workflow and toolchain as `dokturek-mkn10`.
Design: [`docs/superpowers/specs/2026-06-14-catchup-design.md`](docs/superpowers/specs/2026-06-14-catchup-design.md) ·
principles: [`.specify/memory/constitution.md`](.specify/memory/constitution.md).

## Status

**Slice 001 — members, magic-link auth & profiles** is implemented: invite-roster
passwordless sign-in, self-service profiles (name, photo, structured home location,
job, WhatsApp), and a class directory with one-tap WhatsApp contact. Map, trips, and
overlap detection are later slices (002+).

## Structure

```
backend/    FastAPI + SQLAlchemy + alembic, Python 3.13 (uv). Pure core, thin edges.
frontend/   React + TypeScript + Vite SPA.
specs/      Spec Kit features (spec → plan → tasks).
docs/       Design docs.
```

## Run it locally

```bash
# Backend (Postgres + MinIO via Docker, console notifier prints the magic link)
cd backend
uv sync
docker compose -f docker-compose.dev.yml up -d
cp .env.example .env
uv run alembic upgrade head
uv run catchup-roster add you@example.com
uv run uvicorn catchup.app:app --reload     # http://localhost:8000

# Frontend
cd ../frontend
npm install
npm run dev                                  # http://localhost:5173
```

Open the SPA, enter your roster email, and grab the magic link from the backend
logs (the dev `console` notifier prints it). See
[`specs/001-member-auth-profiles/quickstart.md`](specs/001-member-auth-profiles/quickstart.md)
for the full walk-through.

## Test & lint

```bash
cd backend
uv run pytest -m "not smoke"     # unit (no DB)
uv run pytest -m smoke           # smoke (needs Postgres at $DATABASE_URL)
uv run ruff check . && uv run ruff format --check .

cd ../frontend
npm test                         # vitest + RTL
npm run build                    # type-check + production build
```

`pre-commit install` wires the hygiene + ruff hooks.

## Deploy (Railway)

Two services from this repo plus a Postgres and an object-storage bucket:

- **api** — `backend/` Docker image; entrypoint runs `alembic upgrade head` then
  gunicorn. Set `DATABASE_URL`, `SESSION_SECRET`, `NOTIFIER=resend` + `RESEND_API_KEY`,
  `S3_*`, `APP_BASE_URL`, `COOKIE_SECURE=true`.
- **web** — `frontend/` Docker image (nginx). Set `API_URL` to the api service URL;
  nginx serves the SPA and reverse-proxies `/api/*` to it (same-origin cookies).

Trunk-based: push to `main` auto-deploys.
