---
project: AI Flashcard App
researched_at: 2026-05-24
recommended_platform: Fly.io
runner_up: Railway
context_type: mvp
tech_stack:
  language: Python
  framework: Django 6.0
  runtime: Python ≥ 3.14
  database: PostgreSQL (external Supabase)
  package_manager: uv
---

## Recommendation

**Deploy on Fly.io.**

Fly.io is the lowest-cost persistent-process platform for a Django WSGI application with an external Supabase database — approximately $4.27/month, no free-tier cold starts, and a Docker-based model that gives full control over the Python 3.14 runtime. The cost-minimize constraint from the developer interview drove the final choice over Railway ($5/month, better Nixpacks DX) and Render ($7/month Starter, best GA MCP server). Persistent WSGI processes are Fly.io's core model, not a workaround, which directly satisfies the confirmed requirement for always-on server-side connections.

---

## Platform Comparison

Three platforms were hard-dropped before scoring: **Netlify** (no Python runtime), **Vercel** (Python runs as serverless functions only, no persistent WSGI), and **Cloudflare Workers/Pages** (V8 isolates, no persistent processes, Django ORM incompatible with Pyodide + D1 transaction model). All three fail Q1 (persistent connections required).

| Platform | CLI-first | Managed/Serverless | Agent-readable docs | Stable deploy API | MCP / Integration | Cost/mo |
|---|---|---|---|---|---|---|
| **Fly.io** ✓ | Pass | Pass | Partial | Pass | Partial (experimental) | ~$4.27 |
| **Railway** | Pass | Pass | Pass | Pass | Partial (beta/"WIP") | $5 |
| **Render** | Partial | Pass | Pass | Pass | Pass (GA) | $7 |
| Cloudflare | — | — | — | — | — | DROPPED |
| Vercel | — | — | — | — | — | DROPPED |
| Netlify | — | — | — | — | — | DROPPED |

**Scoring notes:**

- **Fly.io CLI-first — Pass**: `fly deploy`, `fly logs`, `fly secrets set`, `fly status`, `fly releases` cover the full operational loop. Rollback is a re-deploy of a prior image (`fly deploy --image registry.fly.io/<app>:<tag>`) rather than a dedicated command — functional but requires the prior image to still exist in the registry.
- **Fly.io agent-readable docs — Partial**: Docs are hosted on GitHub as MDX with a "Copy as Markdown" button. No formal `llms.txt` at fly.io root was found. Content is agent-readable via the GitHub source but without the convenience of a formal LLM endpoint.
- **Fly.io MCP — Partial**: `fly mcp server --claude` auto-configures Claude Code, but is explicitly labeled **experimental** (checked 2026-05-24). The `superfly/flymcp` Go binary is pre-release (4 commits, no published releases). CLI is the reliable fallback.
- **Railway CLI-first — Pass**: `railway up`, `railway logs`, `railway redeploy`, `railway run` cover full operations. Strong CI support via `RAILWAY_TOKEN`.
- **Railway agent-readable docs — Pass**: Full docs at `docs.railway.com/api/llms-docs.md` (LLM-optimized flat file), GitHub MDX source, dedicated "Railway for Agents" section.
- **Railway MCP — Partial**: Official MCP server at `mcp.railway.com` explicitly described as "work in progress" (beta, checked 2026-05-24). Tools cover deploy, variables, logs, and service management — but reliability is unverified.
- **Render CLI-first — Partial**: `render deploys create`, `render logs` work via CLI. Rollback requires the REST API (`POST /v1/services/{id}/deploys/{deploy_id}/rollback`) — no CLI subcommand. Two-step rollback is fragile under pressure.
- **Render agent-readable docs — Pass**: `render.com/llms.txt` + `render.com/llms-full.txt` published. Any docs page returns simplified markdown via `Accept: text/markdown` header.
- **Render MCP — Pass**: Official MCP server **GA** since August 2025 at `mcp.render.com`. 20+ tools covering services, deploys, logs, metrics, and environment variables. Cannot trigger new deploys (deploy hook or CLI required for that). Claude Code integration: `claude mcp add --transport http render https://mcp.render.com/mcp --header "Authorization: Bearer <API_KEY>"`.

---

### Shortlisted Platforms

#### 1. Fly.io (Recommended)

Fly.io's core model is persistent micro-VMs — Django's WSGI process runs continuously with no serverless constraints. The Docker-based deployment gives full control over the Python 3.14 runtime (critical, since `fly launch` auto-generates a Dockerfile with Python 3.12). At ~$4.27/month with external Supabase, it's the cheapest persistent-process option. The CLI is mature and well-documented for Django (`fly deploy`, `fly secrets set`, `fly logs`). The tech-stack.md `deployment_target: fly` hint further confirms alignment. MCP is experimental — agent-driven ops rely on CLI, which is sufficient at MVP scale.

#### 2. Railway

Railway's Nixpacks auto-detection makes Django deployment faster than Fly's Docker-from-scratch approach — `railway up` is typically the first deploy command after `railway login`. The LLM-optimized docs endpoint and "Railway for Agents" section make it the most agent-friendly of the three. At $5/month Hobby (with $5 usage credit), effective cost matches Fly.io at low traffic. Ranked second because Fly.io's cost advantage is confirmed and the Dockerfile control it gives is valuable when the Python version must be exactly 3.14. The MCP server is beta ("work in progress") — same maturity level as Fly.io's experimental MCP.

#### 3. Render

Render has the most mature agent tooling: GA MCP server (20+ tools, Aug 2025), published `llms.txt`/`llms-full.txt`, and Python 3.14 as the default runtime (no Dockerfile needed). Ranked third because it is the most expensive option ($7/month Starter) given the cost-minimize constraint, and the GA MCP server — while impressive — cannot trigger deploys, so the CLI is still required for the core deployment operation. The free tier (useful for validation) introduces 60-second cold starts that conflict with the PRD's sub-2-second UX requirement.

---

## Anti-Bias Cross-Check: Fly.io

### Devil's Advocate — Weaknesses

1. **`fly launch` auto-generates a Dockerfile with Python 3.12, not 3.14**: Fly's auto-generated Dockerfile defaults to `python:3.12-slim` regardless of `.python-version`. Without manually editing the `FROM` line before the first deploy, the app silently runs on Python 3.12 in production while Django 6.0 is developed locally on 3.14.

2. **Rollback requires the prior image to still exist in the registry**: There is no `fly rollback` command. Rollback is `fly deploy --image registry.fly.io/<app>:<tag>` using a prior release's image digest. If that image was pruned during a manual registry cleanup or Fly's retention policy, the rollback target is gone and the developer must fix forward from source code.

3. **`SECRET_KEY` can't be a Fly secret at Docker build time**: Fly secrets are runtime-only. Django's `collectstatic` loads settings (and requires `SECRET_KEY`) during the Dockerfile `RUN` step. Without a placeholder `SECRET_KEY` in the Dockerfile, every `fly deploy` fails at the collectstatic step. This is the most common first-deploy failure for Django on Fly.io.

4. **Fly Machines stop when idle unless explicitly configured**: The default stop policy halts a Machine after all connections go idle. A low-traffic MVP with no keep-alive traffic will sleep between requests — equivalent to a cold-start problem. `auto_stop_machines = false` in `fly.toml` is required for always-on behavior but is not the default.

5. **Dedicated IPv4 ($2/month) is effectively mandatory**: Fly charges $2/month for a dedicated IPv4. Without it, the app uses Anycast IPv6 only. IPv6 is unsupported on many corporate and ISP networks, making the $2/month charge non-optional for broad user access. This is included in the ~$4.27/month estimate but not surfaced on Fly's pricing page as a required line item.

---

### Pre-Mortem — How This Could Fail

The developer deployed the AI Flashcard app to Fly.io on sprint day one. `fly launch` auto-detected Django, generated a Dockerfile, and the app was live. Everything looked correct in the deploy output.

The first serious problem appeared two weeks later after a bad deploy broke the admin panel. The developer ran `fly releases` and identified the prior working image. They had cleaned the registry the previous day during a disk-space audit. The rollback target was gone. The developer had to fix forward — reverting the git commit, fixing the bug, and redeploying from source. A 15-minute fix became 45 minutes under deadline pressure.

On the second sprint day, `fly deploy` started failing at `collectstatic` with `django.core.exceptions.ImproperlyConfigured: The SECRET_KEY setting must not be empty`. The Fly secret was runtime-only; Django needed it at Docker build time. The fix — a placeholder `SECRET_KEY=placeholder-for-build` in the Dockerfile — took an hour to diagnose because the error message pointed at Django rather than the Fly secret injection timing.

Six months later, a QA partner reported the app loading slowly on first visit. The Fly Machine had been configured with the default stop policy and was sleeping after idle periods. Setting `auto_stop_machines = false` in `fly.toml` fixed it — but the cold-start behavior had been silently present the entire MVP period, creating a poor first impression for every new user arriving after any quiet stretch.

---

### Unknown Unknowns

- **`fly launch` doesn't read `.python-version`**: The generated Dockerfile uses `python:3.12-slim`. Edit the `FROM` line to `python:3.14-slim` before the first `fly deploy`. There is no warning if the Dockerfile Python version diverges from `.python-version`.

- **Fly's health check expects HTTP 200 at `/` by default**: Django commonly returns 301 or 302 at `/` (login redirect, HTTPS redirect). Fly marks the Machine unhealthy and loops the deployment indefinitely. Fix: add a dedicated `/healthz/` endpoint returning 200 unconditionally and configure `[http_service.checks] path = "/healthz/"` in `fly.toml`.

- **`ALLOWED_HOSTS` must use a wildcard pattern, not a specific subdomain**: Internal Fly routing may reach the app via multiple addresses. `ALLOWED_HOSTS = ['myapp.fly.dev']` can cause 400 errors on health checks. Use `ALLOWED_HOSTS = ['.fly.dev', 'yourdomain.com']` or derive from `FLY_APP_NAME`.

- **256 MB RAM is tight for Django + Gunicorn**: Django with 2 Gunicorn workers under modest concurrency can exceed 256 MB, triggering OOM kills that restart the Machine mid-request. The first symptom is intermittent 502s under light load. Fix: reduce to 1 Gunicorn worker or upgrade to a 512 MB Machine (~+$2/month).

- **Media uploads write to ephemeral storage by default**: The Fly VM filesystem is ephemeral — any file written to disk is lost on redeploy or Machine restart. The project uses Supabase for the database, which is correct. If user-uploaded files are added later (profile images, custom flashcard media), they require Supabase Storage or an S3-compatible bucket — not local disk.

---

## Operational Story

- **Preview deploys**: Fly.io has no built-in PR preview URL feature. Branch previews require manually deploying to a separate Fly app (`fly deploy --app myapp-staging`). For this solo MVP, previews are not set up; all validation happens locally before deploying to the single production app.

- **Secrets**: Set via `fly secrets set KEY=value` — stored encrypted in Fly's vault. `fly secrets list` shows key names only (values are never readable after set). Rotation: `fly secrets set KEY=new_value`, which triggers an automatic rolling redeploy. Critical secrets: `SECRET_KEY`, `DATABASE_URL` (Supabase connection string with Supavisor pooler on port 6543), `DEBUG=0`.

- **Rollback**: Run `fly releases` to list prior deploy images. Then `fly deploy --image registry.fly.io/<app>:<tag> --strategy immediate`. Typical time-to-revert: 2–3 minutes. Django database migrations do not auto-rollback — if the broken deploy included a migration, the database schema is now ahead of the reverted code. Manual migration reversal (`uv run python manage.py migrate <app> <prior_migration>`) is required separately.

- **Approval**: The following actions require a human: destroying the app (`fly destroy`), scaling to zero (`fly scale count 0`), rotating `SECRET_KEY` (triggers session invalidation for all users), and modifying the Fly.io billing or organization settings. An agent may run unattended: `fly deploy`, `fly logs`, `fly status`, `fly secrets set` for non-critical secrets (e.g., API keys that can be rotated without user impact), and `fly releases`.

- **Logs**: Live tail: `fly logs --app <name>`. Per-Machine scope: `fly logs --instance <machine-id>`. Structured JSON output: not natively supported in `fly logs`; Django logging to stdout is captured and streamed. For structured log queries, Fly supports log shipping to external providers (Papertrail, Logtail) via `fly log-shipper` — not required at MVP.

---

## Risk Register

| Risk | Source | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| Dockerfile defaults to Python 3.12, not 3.14 | Unknown unknowns | H | M | Edit `FROM python:3.14-slim` in Dockerfile before first deploy; verify Python version in `fly logs` output |
| `SECRET_KEY` not available at build time causes `fly deploy` to fail | Unknown unknowns | H | M | Set `ENV SECRET_KEY=placeholder-for-build` in Dockerfile; runtime Fly secret overrides it |
| Health check gets 400 from Django ALLOWED_HOSTS → deploy loops | Unknown unknowns | H | H | Add `/healthz/` endpoint returning 200; configure `fly.toml` checks path; use wildcard in `ALLOWED_HOSTS` |
| Rollback image pruned before emergency revert is needed | Devil's advocate | M | H | Document rollback procedure; keep at least 3 prior releases; never bulk-clean registry before confirming stability |
| Fly Machine stops when idle (default stop policy) | Devil's advocate | H | M | Set `auto_stop_machines = false` in `fly.toml` on first deploy, before any users arrive |
| 256 MB RAM OOM kills under concurrent load | Unknown unknowns | M | M | Monitor `fly status` memory usage; reduce Gunicorn workers to 1 or upgrade to 512 MB Machine |
| Supabase connection pool exhausted under concurrency | Research finding | M | H | Use Supabase Supavisor pooler (port 6543) in `DATABASE_URL`, not direct connection (port 5432); set `CONN_MAX_AGE = 0` with pooler |
| Media uploads written to ephemeral disk lost on redeploy | Pre-mortem | L | H | Use Supabase Storage for all user-facing file uploads; never rely on local filesystem for persistence |
| Fly MCP experimental — agent workflows broken mid-session | Devil's advocate | M | L | Use CLI for all deployment operations; do not build agent pipelines around `fly mcp server` until it reaches GA |
| `SECURE_SSL_REDIRECT = True` may cause loops behind Fly proxy | Research finding | M | M | Use `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` instead of `SECURE_SSL_REDIRECT`; Fly terminates TLS at its proxy |

---

## Getting Started

1. **Install flyctl** (Windows):
   ```powershell
   winget install Fly.io.flyctl
   fly auth login
   ```

2. **Launch and auto-detect Django** (run from project root):
   ```bash
   fly launch
   ```
   This generates `fly.toml` and a `Dockerfile`. Accept defaults, but **do not deploy yet**.

3. **Fix the Dockerfile Python version** — `fly launch` defaults to `python:3.12-slim`. Edit the generated Dockerfile:
   - Change `FROM python:3.12-slim` → `FROM python:3.14-slim`
   - Replace the `pip install` lines with uv-based install:
     ```dockerfile
     COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
     COPY pyproject.toml uv.lock ./
     RUN uv sync --frozen --no-dev
     ```
   - Add `ENV SECRET_KEY=placeholder-for-build DJANGO_SETTINGS_MODULE=config.settings` before `collectstatic`
   - Set `auto_stop_machines = false` in `fly.toml` under `[http_service]`

4. **Set production secrets**:
   ```bash
   fly secrets set \
     SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(50))')" \
     DATABASE_URL="postgres://user:pass@db.supabase.co:6543/postgres" \
     DEBUG=0
   ```
   Use Supabase's Supavisor pooler port (6543), not the direct connection port (5432).

5. **Deploy**:
   ```bash
   fly deploy
   ```
   Verify with `fly status` and `fly logs`. Check the Python version line in the build output to confirm 3.14 is running.

---

## Out of Scope

The following were not evaluated in this research:
- Docker image configuration (covered above at a high level only; detailed Dockerfile is out of scope)
- CI/CD pipeline setup (GitHub Actions auto-deploy on merge is planned per `tech-stack.md`; wiring is a deploy-plan task)
- Production-scale architecture (multi-region, HA, DR)
- Cloudflare as CDN/DNS proxy in front of Fly.io (viable combination, but out of scope for MVP)
