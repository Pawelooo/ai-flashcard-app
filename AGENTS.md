# Repository Guidelines

AI Flashcard App — Django 6.0.5 web app (Python ≥ 3.14) for studying AI/ML concepts before job interviews. All management commands run through `uv run python manage.py`. See `@CLAUDE.md` for full project guidance.

## Hard Rules

- New apps belong at the project root: `uv run python manage.py startapp <name>`. Register each in `INSTALLED_APPS` (`config/settings.py:33`).
- `SECRET_KEY` in `config/settings.py` is a dev placeholder (prefixed `django-insecure-`). Supply a real secret via env var before any staging or production deploy.
- Do not import from `main.py` — it is a `uv` scaffold artifact, not part of the Django project.
- No linter configured yet. If adding one, declare it under `[tool.ruff]` or `[tool.black]` in `pyproject.toml` and invoke via `uv run <tool>`.
- Display dates to the user in the format DD.MM.YYYY (e.g. 22/05/2026).

## Project Structure

- `config/` — Django project config module: settings, `config.urls` (root URLconf), wsgi, asgi. `DJANGO_SETTINGS_MODULE=config.settings`.
- `manage.py` — standard Django entry point.
- `main.py` — `uv` placeholder; not a Django module. Safe to delete.
- `pyproject.toml` — declares `django>=6.0.5` and `requires-python>=3.14`.
- No custom apps exist yet; all feature code goes into new apps created at the project root.
- Full requirements and open questions: `@context/foundation/prd.md`.

## Commands

| Command | Purpose |
|---|---|
| `uv run python manage.py runserver` | Dev server at `localhost:8000` |
| `uv run python manage.py migrate` | Apply pending migrations |
| `uv run python manage.py makemigrations` | Generate new migrations |
| `uv run python manage.py test` | Run all tests |
| `uv run python manage.py test <app>.<Class>.<method>` | Run a single test |
| `uv run python manage.py createsuperuser` | Create an admin user |
| `uv run python manage.py shell` | Django interactive shell |

## Coding Conventions

Python ≥ 3.14. No formatter is active; if one is added, `uv run <tool>` is the invoke pattern.

## Testing

Django's built-in `unittest`-based runner; no `pytest` configured. Tests live in `<app>/tests.py` or a `<app>/tests/` package. Run one class: `uv run python manage.py test <app>.<TestClass>`.

## CI / Deployment

GitHub Actions (not yet configured), planned to auto-deploy to Fly.io on merge to `main`. Dev DB: SQLite (`db.sqlite3`, not committed). Prod DB: PostgreSQL on Fly.io. Admin panel at `/admin/` is used for content seeding via Django's built-in auth.
