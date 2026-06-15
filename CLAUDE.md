# CLAUDE.md

Guidance for Claude Code working in this repo.

## Project

`catch-up` — private, invite-only web app for one high-school class to track where
members live, what they do, and their travel plans, surfacing meet-up overlaps.
Bootstrapped 2026-06-14 with a spec-driven workflow and disciplined tooling.
Design: `docs/superpowers/specs/2026-06-14-catchup-design.md`;
principles: `.specify/memory/constitution.md` (v1.0.0).

## Stack

Backend: Python 3.13, uv, FastAPI, SQLAlchemy 2.x,
alembic (sync), pydantic-settings v2, ruff (line 120), pytest. Frontend: React +
TypeScript + Vite, react-query, react-leaflet (OSM tiles). Postgres = system of
record; S3-compatible object storage for photos. Deploy: multi-stage Docker on
Railway. One repo, two codebases: `backend/`, `frontend/`.

## Workflow (the mindset)

Spec-driven, trunk-based:

1. `/speckit-constitution` — establish project principles (the non-negotiables).
2. `/speckit-specify` — write the feature spec (`specs/NNN-name/spec.md`).
3. `/speckit-clarify` *(optional)* — de-risk ambiguity before planning.
4. `/speckit-plan` — implementation plan + design docs.
5. `/speckit-tasks` — break the plan into actionable tasks.
6. `/speckit-analyze` *(optional)* — cross-artifact consistency check.
7. `/speckit-implement` — execute.

Spec Kit auto-commits at each phase boundary via the `git` extension
(`.specify/extensions.yml`). Branch per feature (`NNN-name`, sequential
numbering), merge to `main`. `main` is the trunk.

## Tooling

Hygiene hooks are wired (`.pre-commit-config.yaml`: trailing-whitespace,
end-of-file-fixer, check-yaml, large-files, merge-conflict):

```bash
pre-commit install
```

- **Backend** (`backend/`): `uv` env; `ruff` (lint + format, line-length 120,
  `E/W/F/I/B/UP/SIM`); `pytest` with `--strict-markers` + `smoke` marker;
  `alembic`.
- **Frontend** (`frontend/`): Vite + TypeScript; vitest + React Testing Library.
- **Deploy**: multi-stage Docker on Railway; `alembic upgrade head` on entrypoint.

## Architectural rules

From the constitution (`.specify/memory/constitution.md` v1.0.0):

- **Spec-driven, trunk-based.** No feature code without spec + plan. `main` is the
  trunk; feature branches `NNN-name` auto-deploy on merge.
- **Private by default.** No public/unauthenticated data endpoints. Magic-link
  auth, roster-gated, no account enumeration. All data is members-only.
- **Self-service ownership.** Members edit only their own profile/trips; enforce
  ownership server-side on every mutating endpoint.
- **Pure core, thin edges.** Overlap detection + place normalization are pure,
  DB-free, unit-tested. I/O lives in runners/services/clients. `logging`, never
  `print()`, in library code.
- **Provider-swappable integrations.** Notifier (email now, WhatsApp later),
  geocoder, object storage each sit behind a small interface; no provider details
  in domain/call-site code.
- **Test discipline.** Pure logic = unit tests (no DB). Integration =
  `@pytest.mark.smoke` on live Postgres, never mock the DB. ruff + pre-commit gate
  every commit.
- **Migrations only.** Schema changes via alembic; no manual DDL. uv only.

## Don't

- Don't bypass the Spec Kit workflow for non-trivial features — spec first.
- Don't add public/unauthenticated data endpoints, or let one member edit
  another's data.
- Don't put I/O (DB, HTTP, storage) in the pure overlap/place logic.
- Don't hard-wire a provider (email/geocoder/storage) into domain code — use the
  interface.
- Don't use `print()` in library code; don't add Poetry (uv only).
- Don't commit secrets; `.env` is gitignored, use `.env.example` for shape.

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan:
`specs/002-map-trips-overlaps/plan.md`
<!-- SPECKIT END -->
