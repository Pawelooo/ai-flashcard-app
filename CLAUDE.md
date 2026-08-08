# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

AI Flashcard App — a Django web app for developers studying AI/ML concepts before job interviews. Features flashcard study sessions, self-scoring, spaced repetition, and a leaderboard.

See `@context/foundation/prd.md` for full requirements and open questions. The admin-role question in FR-007 is resolved: Django's built-in `is_superuser` is the canonical admin mechanism.

## Commands

All commands use `uv` as the package manager.

```bash
uv run python manage.py runserver       # dev server at localhost:8000
uv run python manage.py migrate         # apply migrations
uv run python manage.py makemigrations  # create new migrations
uv run python manage.py test            # run all tests
uv run python manage.py test <app>.<TestClass>.<method>  # run a single test
uv run python manage.py createsuperuser # create admin user
uv run python manage.py shell           # Django shell
```

## Architecture

Django 6.0.5, Python ≥ 3.14, package manager `uv`.

- **`config/`** — Django project configuration module (settings, root URLconf, wsgi/asgi). `DJANGO_SETTINGS_MODULE=config.settings`.
- **`manage.py`** — standard Django entry point.
- **`main.py`** — uv placeholder, not part of the Django project; can be deleted.
- **Database** — SQLite in development (`db.sqlite3`); PostgreSQL planned for Fly.io production.
- **Auth** — Django's built-in `django.contrib.auth`; the admin panel (`/admin/`) is wired for content seeding.
- **Deployment target** — Fly.io, CI/CD via GitHub Actions (auto-deploy on merge).

No custom Django apps exist yet — they should be created under the project root (e.g. `uv run python manage.py startapp <name>`) and registered in `INSTALLED_APPS`.

No linter or formatter is configured. If adding one, register it under `[tool.ruff]` or `[tool.black]` in `pyproject.toml` and run via `uv run <tool>`.

<!-- BEGIN @przeprogramowani/10x-cli -->

## 10xDevs AI Toolkit - Module 2, Lesson 1

Move from sprint-zero setup to project orchestration with the **roadmap chain**:

```
(Module 1 foundation docs) -> /10x-roadmap -> backlog-ready roadmap items
```

`/10x-roadmap` is the lesson focus. `/10x-new` is intentionally introduced in Module 2, Lesson 2, when a selected roadmap item becomes an implementation change folder.

### Task Router - Where to start

| Skill | Use it when |
| --- | --- |
| **Roadmap (lesson focus)** | |
| `/10x-roadmap` | You have `context/foundation/prd.md` and a scaffolded project baseline, and you need a vertical-first MVP roadmap. The skill reads the PRD, inspects the code baseline, uses available foundation docs such as `tech-stack.md`, `infrastructure.md`, and `deploy-plan.md`, then writes `context/foundation/roadmap.md`. Use it BEFORE creating per-change folders or implementation plans. |
| **Re-run upstream if needed** | |
| `/10x-shape` / `/10x-prd` / `/10x-tech-stack-selector` / `/10x-bootstrapper` / `/10x-agents-md` / `/10x-infra-research` | Bundled from Module 1 so foundation contracts can be fixed before roadmap sequencing. If roadmap generation exposes a PRD gap, repair the PRD before pretending the backlog is ready. |

### How the chain hands off

- `/10x-roadmap` bridges product and implementation. It does not choose frameworks, design schemas, or write a per-change implementation plan.
- The output is `context/foundation/roadmap.md`: ordered milestones, vertical slices, bounded foundations, dependencies, unknowns, risk, and backlog handoff fields.
- Roadmap items should receive stable human-readable identifiers in backlog tools. The actual `context/changes/<change-id>/` folder is created in Lesson 2 with `/10x-new`.

### Roadmap boundaries

- Default to vertical slices: user-visible outcomes that cross UI, data, business logic, and integrations.
- Horizontal work is allowed only as a bounded enabler that names the downstream vertical milestone it unlocks.
- Avoid orphan horizontal work such as "build the whole database", "build all API endpoints", or "design the whole UI" before the first user-visible flow.
- Roadmap is not a calendar estimate. Do not invent dates, story points, or sprint velocity unless the user explicitly asks for a separate planning artifact.

### Foundation paths used by this lesson

- `context/foundation/prd.md` - input
- `context/foundation/tech-stack.md` - optional input
- `context/foundation/infrastructure.md` - optional input
- `context/deployment/deploy-plan.md` - optional input
- `context/foundation/roadmap.md` - output
- `context/foundation/lessons.md` - recurring rules and pitfalls
- `docs/reference/contract-surfaces.md` - load-bearing names registry

Skills must not write to `context/archive/`. Archived changes are immutable; if a resolved target path starts with `context/archive/`, abort with: "This change is archived. Open a new change with `/10x-new` instead."

<!-- END @przeprogramowani/10x-cli -->
