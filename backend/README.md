# catch-up backend

FastAPI + SQLAlchemy + Postgres backend for catch-up (members, magic-link auth,
profiles). See `../specs/001-member-auth-profiles/quickstart.md` for the full dev
loop and `../CLAUDE.md` for conventions.

## Quick commands

```bash
uv sync
docker compose -f docker-compose.dev.yml up -d   # Postgres + MinIO
uv run alembic upgrade head
uv run catchup-roster add you@example.com
uv run uvicorn catchup.app:app --reload

uv run pytest -m "not smoke"   # unit tests (no DB)
uv run pytest -m smoke         # smoke tests (live Postgres)
uv run ruff check . && uv run ruff format --check .
```
