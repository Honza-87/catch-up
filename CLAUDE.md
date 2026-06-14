# CLAUDE.md

Guidance for Claude Code working in this repo.

## Project

`catch-up` — _purpose TBD_. New repo, bootstrapped 2026-06-14 with the same
spec-driven workflow and tooling discipline as `dokturek-mkn10`. Define the real
scope by running `/speckit-constitution`, then `/speckit-specify` for the first
feature.

## Stack

**Undecided.** No language/runtime committed yet. Pick it in the constitution
(`/speckit-constitution`), then fill this section and add the matching tooling
(see "Tooling" below). Until then, keep the repo stack-agnostic.

## Workflow (the mindset)

Spec-driven, trunk-based — copied from `dokturek-mkn10`:

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
end-of-file-fixer, check-yaml, large-files, merge-conflict). Install them once
the stack is chosen:

```bash
pre-commit install
```

**Pending stack decision** (mirror `dokturek-mkn10` once language is set):

- Python → `uv` env, `ruff` (lint + format, line-length 120, `E/W/F/I/B/UP/SIM`),
  `pytest` with `--strict-markers` + smoke markers, `alembic` if Postgres.
  Add the `ruff` + `ruff-format` hooks to `.pre-commit-config.yaml`.
- Other stack → port the equivalent lint/format/test loop, keep the hygiene hooks.

Deploy target (Railway + multi-stage Docker, like mkn10) is also deferred until
there's something to deploy.

## Architectural rules

_None yet._ These come from the constitution. After
`/speckit-constitution`, distill the binding principles here as terse,
testable rules (mkn10's CLAUDE.md "Architectural rules" section is the model).

## Don't

- Don't pick a stack or add framework deps before the constitution records the
  decision.
- Don't bypass the Spec Kit workflow for non-trivial features — spec first.
- Don't commit secrets; `.env` is gitignored, use `.env.example` for shape.

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
<!-- SPECKIT END -->
