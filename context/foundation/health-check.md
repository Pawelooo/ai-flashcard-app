---
project: ai-flashcard-app
checked_at: 2026-05-20T00:00:00Z
health_status: needs-attention
context_type: brownfield
language_family: python
stack_assessment_available: false
checks_run:
  - lockfile
  - dependency_audit
  - outdated_deps
  - test_runner
  - ci_cd
  - configuration
audit_findings:
  critical: 0
  high: 0
  moderate: 0
  low: 0
test_runner_detected: false
ci_provider: null
recommended_fixes: 6
---

## Dependency Health

### Lockfile

```
Status:          present (uv.lock)
Package manager: uv
```

`uv.lock` is committed and pins all four direct and transitive dependencies (django 6.0.5, asgiref 3.11.1, sqlparse 0.5.5, tzdata 2026.2). Dependency versions are reproducible across machines. No action needed here.

### Security Audit

```
Tool:   pip-audit --format json
Status: failed to run
Reason: SSL certificate verification failed — corporate proxy or custom CA intercepts PyPI
        connections. Python's ssl module cannot verify the issuer certificate.
        Error: ssl.SSLCertVerificationError: certificate verify failed: unable to get local
        issuer certificate
```

pip-audit installed successfully but cannot reach `pypi.org` to fetch advisory data. This is a network configuration issue, not a vulnerability in the project. No advisory data is available for this run.

**Fix**: Configure Python's requests/urllib to trust the system certificate store:

```powershell
# Option 1 — point pip-audit at the system CA bundle
$env:REQUESTS_CA_BUNDLE = (python -c "import certifi; print(certifi.where())")
# or set to your corporate CA bundle path:
$env:REQUESTS_CA_BUNDLE = "C:\path\to\corporate-ca.crt"
pip-audit --format json

# Option 2 — use pip trusted-host workaround (less secure, dev-only)
pip-audit --format json --skip-editable
```

### Outdated Dependencies

```
Status: not checked — network blocked by SSL certificate error (same root cause as audit)
```

Cannot reach PyPI to compare installed versions against latest releases. Once the SSL issue is resolved, run:

```powershell
uv pip list --outdated
```

Django 6.0.5 was released recently (installed 2026-05-20); no staleness concern is expected.

---

## Test Suite

```
Test runner:    not detected
Tests found:    n/a
Test execution: not attempted
```

No test runner is configured. The `pyproject.toml` has no `[tool.pytest.ini_options]` section, and no `pytest.ini`, `setup.cfg`, or `tox.ini` files are present. The `config/` Django module has no `tests.py` files.

⚠ No test runner detected. The agent cannot verify its own changes — every code edit is unverifiable without a test suite.

**Recommended fix**: Add pytest and the Django test integration:

```powershell
uv add --dev pytest pytest-django

# Then add to pyproject.toml:
# [tool.pytest.ini_options]
# DJANGO_SETTINGS_MODULE = "config.settings"
# pythonpath = ["."]
```

---

## CI/CD

```
Provider:      not detected
Configuration: not found
```

ℹ No CI/CD configuration detected. You'll set this up in [Sprint Zero z Agentem: infrastruktura, walking skeleton i pierwszy deploy (M1L5)](https://platforma.przeprogramowani.pl/external/10xdevs-3/m1-l5).
For now, a local test runner is sufficient for agent collaboration.

---

## Configuration

### High severity

- **No type checker configured** — Django is untyped by default. Without mypy or pyright, the agent generates Python code without type annotations and has no signal when types are incorrect. Fix:

  ```powershell
  uv add --dev mypy django-stubs
  # Add to pyproject.toml:
  # [tool.mypy]
  # plugins = ["mypy_django_plugin.main"]
  # [tool.django-stubs]
  # django_settings_module = "config.settings"
  ```

  Effort: moderate (15–30 min to configure and baseline).

### Medium severity

- **No formatter configured** — the agent's output will have inconsistent indentation, trailing whitespace, and import ordering, creating noisy diffs. Fix:

  ```powershell
  uv add --dev ruff
  # Add to pyproject.toml:
  # [tool.ruff]
  # line-length = 88
  # [tool.ruff.lint]
  # select = ["E", "F", "I"]
  ```

  Effort: quick (< 5 min).

- **No linter configured** — without a linter, the agent can introduce unused imports, undefined names, and style violations without any feedback loop. Ruff covers both formatting and linting — the formatter fix above handles this too.

### Low severity

- **`.editorconfig` missing** — editors opened by the agent (or teammates) may use different tab/space/line-ending defaults, causing whitespace noise in diffs. Fix: create `.editorconfig` with `indent_style = space`, `indent_size = 4`, `end_of_line = lf`. Effort: quick (< 5 min).

- **`.env.example` missing** — the Django project uses `SECRET_KEY`, `DEBUG`, and `DATABASE_URL` from environment variables (or `settings.py` defaults). Without an `.env.example`, the agent has no documentation of required secrets and may hardcode values. Fix: create `.env.example`:

  ```
  SECRET_KEY=your-secret-key-here
  DEBUG=True
  DATABASE_URL=sqlite:///db.sqlite3
  ALLOWED_HOSTS=localhost,127.0.0.1
  ```

  Effort: quick (< 5 min).

---

## Stack Assessment Cross-Reference

No stack-assessment.md found. Run `/10x-stack-assess` for quality-gate analysis.

---

## Recommended Fixes

### Fix before agent work (Category A)

#### 1. Add a test runner

**Impact**: Without tests, the agent cannot verify its own changes. Every code edit is a blind guess — regressions go undetected, and the agent's confidence is unanchored.
**Severity**: high
**Effort**: quick (< 5 min to install, moderate to write the first test)
**Fix**:

```powershell
uv add --dev pytest pytest-django
```

Then add to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings"
pythonpath = ["."]
```

Create `tests/` directory and a smoke test:

```powershell
New-Item -ItemType Directory tests
# tests/test_smoke.py
# def test_django_loads(): pass
```

---

#### 2. Configure formatter and linter (ruff)

**Impact**: The agent's output style will be inconsistent without a formatter. Linting catches undefined names and unused imports before they accumulate.
**Severity**: medium
**Effort**: quick (< 5 min)
**Fix**:

```powershell
uv add --dev ruff
```

Add to `pyproject.toml`:

```toml
[tool.ruff]
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I"]
```

---

#### 3. Configure type checker (mypy)

**Impact**: Django is dynamically typed by default. Without mypy + django-stubs, the agent generates code with unverified type assumptions. Catching type errors locally prevents runtime surprises.
**Severity**: high
**Effort**: moderate (15–30 min — installing is quick; baselining existing code takes time)
**Fix**:

```powershell
uv add --dev mypy django-stubs
```

Add to `pyproject.toml`:

```toml
[tool.mypy]
plugins = ["mypy_django_plugin.main"]
strict = false
ignore_missing_imports = true

[tool.django-stubs]
django_settings_module = "config.settings"
```

---

#### 4. Resolve dependency audit SSL issue

**Impact**: pip-audit cannot check for known vulnerabilities in django, asgiref, or sqlparse because the network connection to PyPI is blocked by a corporate proxy. No advisory data means you are flying blind on security.
**Severity**: medium (infrastructure issue, not a known vulnerability)
**Effort**: quick (< 5 min once the CA path is known)
**Fix**:

```powershell
# Set the corporate CA bundle path for Python's SSL
$env:REQUESTS_CA_BUNDLE = "C:\path\to\your\corporate-ca.crt"
pip-audit --format json

# Or disable verification temporarily (dev-only, not for CI):
pip-audit --format json --no-deps
```

Once resolved, run `pip-audit` after every `uv add` to catch new advisories early.

---

#### 5. Add `.env.example`

**Impact**: Django's settings rely on environment variables (`SECRET_KEY`, `DEBUG`, `DATABASE_URL`). Without documentation, the agent may hardcode secrets or miss required variables.
**Severity**: low
**Effort**: quick (< 5 min)
**Fix**: Create `.env.example` at the project root:

```
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
```

Then add `python-decouple` or `django-environ` to read from `.env`:

```powershell
uv add django-environ
```

---

#### 6. Add `.editorconfig`

**Impact**: Consistent indentation and line endings prevent whitespace noise in the agent's diffs.
**Severity**: low
**Effort**: quick (< 5 min)
**Fix**: Create `.editorconfig` at the project root:

```ini
root = true

[*]
indent_style = space
indent_size = 4
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.md]
trim_trailing_whitespace = false
```

---

### Addressed in upcoming lessons (Category B)

#### No CI/CD pipeline

**Lesson**: [Sprint Zero z Agentem: infrastruktura, walking skeleton i pierwszy deploy (M1L5)](https://platforma.przeprogramowani.pl/external/10xdevs-3/m1-l5)
**What you'll do there**: Set up a GitHub Actions workflow that runs tests, linting, and deploys to Fly.io on merge to main. The `ci_provider: github-actions` and `ci_default_flow: auto-deploy-on-merge` flags from your tech-stack hand-off will guide that lesson's configuration.

#### Missing AGENTS.md / CLAUDE.md (agent instruction files)

**Lesson**: [Agent Onboarding: Agents.md, AI Rules i feedback loops (M1L4)](https://platforma.przeprogramowani.pl/external/10xdevs-3/m1-l4)
**What you'll do there**: Build `AGENTS.md` and `CLAUDE.md` with project conventions, Django-specific patterns, and rules that compensate for Django's untyped default (a quality-gate gap the stack lacks). Generating stubs now would be premature — the lesson walks through the right content.

---

## Summary

Health status: **needs-attention**

The project scaffolded cleanly with a pinned dependency tree (`uv.lock` present, Django 6.0.5 installed). The two priority gaps for agent-assisted development are: **no test runner** (the agent has no way to verify its own changes) and **no formatter/type-checker** (code quality feedback is absent). The dependency audit could not run due to a corporate SSL proxy — this is an infrastructure issue, not a known vulnerability, but it should be resolved so ongoing security posture is visible.

All Category A gaps are addressable in under an hour with the commands above. CI/CD and agent instruction files are coming up in the next two lessons and are expected to be absent at this stage.

Next step: install pytest and ruff (fixes 1 and 2 above — both quick), then proceed to [Agent Onboarding (M1L4)](https://platforma.przeprogramowani.pl/external/10xdevs-3/m1-l4).
