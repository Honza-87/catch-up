<!--
SYNC IMPACT REPORT
Version change: (initial) → 1.0.0 (initial ratification)
Ratified: 2026-06-14 | Last amended: 2026-06-14

Principles (all new):
- I. Spec-Driven & Trunk-Based
- II. Private, Invite-Only by Default
- III. Self-Service Data Ownership
- IV. Pure Core, Thin Edges
- V. Provider-Swappable Integrations
- VI. Test Discipline

Added sections:
- Technology Constraints
- Development Workflow
- Governance

Removed sections: none (initial version)

Templates reviewed:
- ✅ .specify/templates/plan-template.md — generic Constitution Check, no principle-name hardcoding
- ✅ .specify/templates/spec-template.md — no constraints requiring change
- ✅ .specify/templates/tasks-template.md — task categories compatible
- ⚠ CLAUDE.md — Stack + Architectural rules updated alongside this ratification

Follow-up TODOs: none
-->

# catch-up Constitution

**Repo:** `catch-up`
**Scope:** A private, invite-only web app for one high-school graduating class to
track where members are in the world, what they do for work, and their travel
plans — so members can spot when they will be in the same place and plan meet-ups.
**Owner:** Honza Chromec
**Established:** 2026-06-14
**Version:** 1.0.0

## Core Principles

### I. Spec-Driven & Trunk-Based

Every non-trivial change flows through the Spec Kit workflow: constitution →
specify → (clarify) → plan → tasks → (analyze) → implement. `main` is the trunk;
work happens on sequentially numbered feature branches (`NNN-name`) and merges
back to `main`, which auto-deploys. No feature code lands without a spec and plan
behind it. Rationale: the spec is the source of truth that keeps the app and its
intent aligned, and the brainstorming design doc under
`docs/superpowers/specs/` is valid `/speckit-specify` input.

### II. Private, Invite-Only by Default

The app is a closed dataset for invited classmates only. All profile, trip, and
contact data is visible exclusively to authenticated members — there are no
public, unauthenticated data endpoints. Access is gated by an email roster;
authentication is passwordless magic link. The app MUST NOT enumerate accounts
(non-roster login requests get a generic response). Rationale: members share home
locations, travel plans, and WhatsApp numbers only because the circle is closed;
that trust is the product.

### III. Self-Service Data Ownership

Each member owns and edits only their own profile and trips. The system MUST NOT
require one person to act as a data-entry bottleneck, and ownership is enforced
server-side on every mutating endpoint (a member cannot edit another's data).
Rationale: travel plans stay current only when their owner maintains them.

### IV. Pure Core, Thin Edges

Domain logic — overlap detection and place/location normalization — is written as
pure functions with no database or network access, and is unit-tested in
isolation. Persistence and I/O live in separate runners, services, and clients
that call the pure core. Library code MUST use stdlib `logging`, never `print()`.
Rationale (mirrors `dokturek-mkn10`'s pure-parser/pure-writer rule): pure cores
are fast to test and easy to reason about; isolating I/O keeps the rules honest.

### V. Provider-Swappable Integrations

Every external dependency — notifier (email today, WhatsApp later), geocoder, and
object storage — sits behind a small in-repo interface. Concrete providers are
implementation details that MUST be swappable without touching domain or call-site
code. Rationale: WhatsApp alerts are a planned v2; the design must not bake in
today's provider choices.

### VI. Test Discipline

Pure domain logic has unit tests that run without a database. Integration paths
are covered by `@pytest.mark.smoke` tests against a live Postgres — these MUST NOT
mock SQLAlchemy or the database. `ruff` lint + format and the pre-commit hooks
gate every commit. Rationale (mkn10 parity): the overlap engine is the heart of
the product and must be exhaustively, cheaply testable; smoke tests prove the real
SQL and migrations work.

## Technology Constraints

- **Backend** mirrors `dokturek-mkn10`: Python 3.13, uv-managed, FastAPI,
  SQLAlchemy 2.x, alembic (sync), pydantic-settings v2, ruff (line-length 120),
  pytest. Schema changes go through alembic migrations — no manual DDL. No Poetry
  (uv only).
- **Frontend**: React + TypeScript + Vite, react-query, react-leaflet
  (OpenStreetMap tiles, no API key). One repository, two codebases
  (`backend/`, `frontend/`).
- **Persistence**: Postgres is the system of record. Object storage
  (S3-compatible / Railway bucket) holds profile photos.
- **Deploy**: multi-stage `Dockerfile`, Railway. `alembic upgrade head` runs on
  entrypoint before serving traffic. Push to `main` auto-deploys.
- **MVP scope boundaries** (out of scope until amended): WhatsApp *automated*
  alerts, per-field privacy controls, multiple classes / multi-tenancy, radius
  ("within X km") matching, native app, social logins beyond magic link.

## Development Workflow

- Author or amend the constitution with `/speckit-constitution`; specify features
  with `/speckit-specify`; plan, generate tasks, and implement through the
  matching Spec Kit skills. The `git` extension auto-commits at phase boundaries.
- One feature = one spec under `specs/NNN-name/`, one plan, one branch.
- Quality gates before merge to `main`: `ruff check`, `ruff format`, `pytest`
  (unit; smoke where a Postgres is available), and green pre-commit hooks.
- Distil binding rules from these principles into `CLAUDE.md` so the working agent
  has them in context.

## Governance

This constitution supersedes ad-hoc practice. Amendments are made by editing this
file via `/speckit-constitution`, which records a Sync Impact Report and bumps the
version using semantic versioning:

- **MAJOR** — removing or redefining a principle in a backward-incompatible way.
- **MINOR** — adding a principle/section or materially expanding guidance.
- **PATCH** — clarifications and wording fixes with no change in meaning.

Plans and reviews MUST verify compliance with these principles; any deviation is
justified in the plan's Complexity/Constitution-Check section or it does not ship.

**Version**: 1.0.0 | **Ratified**: 2026-06-14 | **Last Amended**: 2026-06-14
