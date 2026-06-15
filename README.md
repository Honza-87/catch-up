# catch-up

A private, invite-only web app for one high-school graduating class to track where
members are in the world, what they do, and (later) their travel plans — so they can
spot when they'll be in the same place and plan meet-ups.

Built with a spec-driven workflow.
Design: [`docs/superpowers/specs/2026-06-14-catchup-design.md`](docs/superpowers/specs/2026-06-14-catchup-design.md) ·
principles: [`.specify/memory/constitution.md`](.specify/memory/constitution.md).

## Status

**Live in production at [catch-up.online](https://catch-up.online).** Slices shipped:

- **001 — members, magic-link auth & profiles:** invite-roster passwordless sign-in,
  self-service profiles (name, photo, structured home location, job, WhatsApp), class
  directory with one-tap WhatsApp contact.
- **002 — map, trips & overlaps:** class world map (`react-leaflet` + OSM), trips, a
  pure overlap-detection engine, and hourly digest emails for new overlaps (cron worker).
  Members can opt out of digest emails from their profile.
- **003 — significant events:** home-hosted open invitations (e.g. birthdays).

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

Live at **[catch-up.online](https://catch-up.online)**. One Railway project: three
services built from this monorepo (each sets its own **Root Directory**) plus managed
**Postgres** and an **object-storage bucket** (photos).

| Service | Root dir | Config file | Role |
|---|---|---|---|
| `frontend` | `frontend` | `railway.json` | nginx — serves the SPA, reverse-proxies `/api/*` to the backend (same-origin cookies) |
| `backend` | `backend` | `railway.json` | gunicorn API; entrypoint runs `alembic upgrade head` on boot |
| `worker` | `backend` | `railway.worker.json` | hourly cron `catchup-overlap` — recompute overlaps + send digests |

**Env** (set per service):

- backend + worker: `DATABASE_URL` (`postgresql+psycopg://…`), `SESSION_SECRET`,
  `NOTIFIER=resend` + `RESEND_API_KEY`, `EMAIL_FROM`, `APP_BASE_URL`, `COOKIE_SECURE=true`;
  backend also `S3_*` (bucket credentials).
- frontend: `API_URL=http://backend.railway.internal:8000` (private networking).

**Notes:**

- The `worker` shares `backend/`'s image — it differs from `backend` only by config file
  (`railway.worker.json` = `cronSchedule` + `startCommand catchup-overlap`). Set that path
  explicitly in the worker service's config-as-code setting; it does **not** default to it.
- frontend nginx re-resolves the backend upstream at **runtime** (`resolver` + variable
  `proxy_pass`, see `frontend/nginx.conf`) so a backend redeploy's new private IP doesn't
  strand it on a dead upstream.
- Seed the invite roster against the live DB:
  `railway ssh --service backend catchup-roster add <email>`.
- Trunk-based: push to `main` auto-deploys (GitHub connected; per-service watch paths
  scope rebuilds to the folder that changed).

## License

[MIT](LICENSE) © Honza Chromec. Reuse permitted with attribution.
