---
bootstrapped_at: 2026-05-20T00:00:00Z
starter_id: django
starter_name: Django
project_name: ai-flashcard-app
language_family: python
package_manager: uv
cwd_strategy: native-cwd
bootstrapper_confidence: verified
phase_3_status: ok
audit_command: pip-audit --format json
---

## Hand-off

```yaml
starter_id: django
package_manager: uv
project_name: ai-flashcard-app
hints:
  language_family: python
  team_size: solo
  deployment_target: fly
  ci_provider: github-actions
  ci_default_flow: auto-deploy-on-merge
  bootstrapper_confidence: verified
  path_taken: standard
  quality_override: false
  self_check_answers: null
  has_auth: true
  has_payments: false
  has_realtime: false
  has_ai: true
  has_background_jobs: false
```

**Why this stack**

Django is the natural fit for AI Flashcard App: auth, admin panel, ORM, and migrations ship out of the box, directly covering FR-001 (user registration/login) and FR-007 (admin deck management) without third-party assembly. The batteries-included model keeps a 3-week after-hours sprint on schedule — standard CRUD and auth are measured in hours, not days. The leaderboard (FR-005) and session scoring (FR-004) map cleanly to Django's ORM aggregation and queryset API. Fly.io with GitHub Actions provides a proven, low-configuration deployment pipeline for Django + PostgreSQL that a solo developer can wire up in an afternoon.

## Pre-scaffold verification

| Signal      | Value                                                    | Severity | Notes                                                    |
| ----------- | -------------------------------------------------------- | -------- | -------------------------------------------------------- |
| npm package | n/a — Python starter                                     | n/a      | skipped; JS-only check                                   |
| GitHub repo | not run                                                  | n/a      | gh CLI not installed on this machine; docs_url (https://docs.djangoproject.com) is not a GitHub URL |

Recency check unavailable — gh CLI not installed and docs_url is not a GitHub URL. Proceeding.

## Scaffold log

**Resolved invocation**:
1. `uv init --no-readme` (pre-step: initialise uv Python project in cwd)
2. `uv add django --native-tls` (pre-step: install Django 6.0.5 + dependencies)
3. `uv run django-admin startproject config .` (main cmd_template with `{name}` set to `config`)

**Strategy**: scaffold directly into the current directory

**Exit code**: 0

**`{name}` substitution note**: The registry card's cmd_template is `django-admin startproject {name} .`. For this strategy the generic rule would substitute `{name}=.`, producing `django-admin startproject . .` — an invalid invocation (Django requires a valid Python identifier as the project module name). `{name}` was therefore set to `config` (the Django community convention for the main configuration module). The `.` suffix in the template already positions all files in cwd.

**Pre-flight files-to-touch**: pyproject.toml, main.py, .python-version (from uv init); uv.lock, .gitignore (from uv add); manage.py, config/ directory (from django-admin startproject)

**Files written by CLI**:
- `pyproject.toml` — uv project manifest (name: naukaai, python >=3.14, django>=6.0.5)
- `main.py` — uv placeholder (can be deleted; not part of Django project structure)
- `.python-version` — pins Python version for uv
- `uv.lock` — locked dependency tree (django 6.0.5, asgiref 3.11.1, sqlparse 0.5.5, tzdata 2026.2)
- `.gitignore` — created by uv init (covers __pycache__, *.py[oc], build/, dist/, wheels/, *.egg-info, .venv)
- `manage.py` — Django management entry point
- `config/__init__.py`
- `config/asgi.py`
- `config/settings.py`
- `config/urls.py`
- `config/wsgi.py`
- `.venv/` — virtual environment (not counted in file log; managed by uv)

**Pre-existing files preserved**: CLAUDE.md, skills-lock.json, context/, .agents/, .claude/

**Conflicts (.scaffold siblings)**: none

**.gitignore handling**: created fresh by uv init (no pre-existing .gitignore in cwd at scaffold time)

## Post-scaffold audit

**Tool**: pip-audit --format json

**Status**: failed to run

**Reason**: pip-audit was downloaded and installed successfully (28 packages via uv --native-tls) but failed at runtime with a Windows OpenSSL error: `OPENSSL_Uplink(00007FFA05047C58,08): no OPENSSL_Applink`. This is a known compatibility issue between pip-audit's bundled OpenSSL and certain Windows Python builds.

**Recommended next step**: Run `pip install pip-audit` using the system Python (Python 3.14.0 / pip 26.0.1 on PATH) rather than via uv's isolated tool runner, then re-run `pip-audit --format json` from the project directory to get dependency advisories. Alternatively, `safety check` or Snyk CLI are usable substitutes on Windows.

**Partial output**:
```
Downloading pip (1.7MiB)
Installed 28 packages in 176ms
OPENSSL_Uplink(00007FFA05047C58,08): no OPENSSL_Applink
```

## Hints recorded but not acted on

| Hint                    | Value               |
| ----------------------- | ------------------- |
| bootstrapper_confidence | verified            |
| quality_override        | false               |
| path_taken              | standard            |
| self_check_answers      | null                |
| team_size               | solo                |
| deployment_target       | fly                 |
| ci_provider             | github-actions      |
| ci_default_flow         | auto-deploy-on-merge |
| has_auth                | true                |
| has_payments            | false               |
| has_realtime            | false               |
| has_ai                  | true                |
| has_background_jobs     | false               |

All hint fields above were read at bootstrap time and copied to this log for audit-trail completeness. None drove automated action in v1. The feature flags (`has_auth`, `has_ai`) and deployment target (`fly`) will inform the future M1L4 skill (agent context setup) and the M1L5 skill (infrastructure and CI/CD).

## Next steps

Next: a future skill will set up agent context (CLAUDE.md, AGENTS.md). For now, your project is scaffolded and verified — happy hacking.

Useful manual steps in the meantime:
- `git init` (if you have not already) to start your own repo history.
- Review `main.py` — it was created by `uv init` as a placeholder and is not needed by Django; you can delete it or repurpose it.
- Update `pyproject.toml` to set `name = "ai-flashcard-app"` (currently `naukaai`, derived from the directory name by `uv init`).
- Run the security audit once the OpenSSL issue is resolved: `pip install pip-audit && pip-audit`.
- Address audit findings per your project's risk tolerance — the full breakdown will appear in this log once the audit runs cleanly.
