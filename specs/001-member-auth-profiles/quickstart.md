# Quickstart — Members, Magic-Link Auth & Profiles (slice 001)

Local dev for the foundation slice. No real email or cloud needed: the dev
notifier prints the sign-in link, and Postgres + object storage run in Docker.

## Prerequisites

- Python 3.13 + `uv`
- Node 20+ (`pnpm` or `npm`)
- Docker (Postgres + MinIO)

## 1. Backing services

```bash
# from backend/ — Postgres + MinIO (S3-compatible) for local dev
docker compose -f docker-compose.dev.yml up -d
```

## 2. Backend

```bash
cd backend
uv sync
cp .env.example .env          # fill DATABASE_URL, SESSION_SECRET, geocoder + storage vars
uv run alembic upgrade head   # create schema

# seed the invite roster (owner action)
uv run catchup-roster add you@example.com
uv run catchup-roster add classmate@example.com
uv run catchup-roster list

uv run uvicorn catchup.app:app --reload   # API on http://localhost:8000
```

Key env (`.env`):

| Var | Purpose | Dev value |
|---|---|---|
| `DATABASE_URL` | Postgres | `postgresql+psycopg://catchup:catchup@localhost:5432/catchup` |
| `SESSION_SECRET` | cookie/token signing | any long random string |
| `NOTIFIER` | email impl | `console` (prints link) |
| `RESEND_API_KEY` | prod email | unset in dev |
| `GEOCODER_URL` | Photon base | `https://photon.komoot.io` |
| `S3_ENDPOINT` / `S3_BUCKET` / `S3_ACCESS_KEY` / `S3_SECRET_KEY` | photos | MinIO local values |
| `MAGIC_LINK_TTL_MINUTES` | link expiry | `15` |

## 3. Frontend

```bash
cd frontend
pnpm install
pnpm dev                      # SPA on http://localhost:5173, proxying /api → :8000
```

## 4. Sign in (dev loop)

1. Open the SPA, enter a **roster** email on the Login screen.
2. With `NOTIFIER=console`, the magic link is printed in the backend logs — open it.
3. You land signed in with an empty profile. Fill it in (name, home location via
   autocomplete, job, WhatsApp, photo) and save.
4. Sign in as a second roster member to see the directory + WhatsApp button.

## 5. Tests

```bash
cd backend
uv run pytest -m "not smoke"   # unit: tokens, validation, place parsing (no DB)
uv run pytest -m smoke         # smoke: live Postgres (auth/profile/directory)
uv run ruff check . && uv run ruff format --check .

cd ../frontend
pnpm test                      # vitest + RTL
```

## Acceptance walk-through (maps to spec)

- **US1**: roster email → link → signed in; non-roster email → same neutral
  response, no access; reused/expired link → denied.
- **US2**: edit every profile field incl. photo; reload persists; cannot edit
  another member.
- **US3**: directory lists joined members; tapping WhatsApp opens `wa.me`.
