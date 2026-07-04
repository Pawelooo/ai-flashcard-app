# Deploy Plan: Fly.io + Cloudflare Integration

> **Artifact location:** `cocmdntext/changes/deployment/deployment-plan.md`

## Context

The Django project is infrastructure-incomplete: no Dockerfile, no `fly.toml`, no env-var reading in settings, no production dependencies (gunicorn, psycopg, whitenoise). This plan covers every step from the current bare-Django state to a fully deployed, Cloudflare-proxied application on Fly.io, matching the decisions in `context/foundation/infrastructure.md`.

**Architecture**: Django WSGI on Fly.io ← Cloudflare proxy (CDN + DDoS + SSL) ← users

**Prerequisite (manual, before starting):**
- A custom domain already managed by Cloudflare (DNS tab visible in Cloudflare dashboard)
- A Fly.io account + flyctl installed and authenticated (Phase 0A below)
- A Supabase project created and connection string ready (Phase 0B below)

---

## Phase 0A — Fly.io CLI Setup

- [x] **0A.1 Install flyctl** (Windows):
  ```powershell
  winget install Fly.io.flyctl
  ```
  Verify: `fly version` — should print `v0.3.x` or later.

- [x] **0A.2 Create a Fly.io account** (if you don't have one):
  Go to https://fly.io/app/sign-up — free account, no credit card required to sign up.
  > A credit card IS required before first deploy (Fly charges per-resource). Add one at https://fly.io/dashboard/billing.

- [x] **0A.3 Authenticate the CLI**:
  ```powershell
  fly auth login
  ```
  This opens a browser tab. Log in and return to the terminal — you should see `Successfully logged in as <email>`.

- [x] **0A.4 Verify authentication**:
  ```powershell
  fly auth whoami    # prints your email
  fly orgs list      # prints your default org
  ```

---

## Phase 0B — Supabase Project Setup

- [x] **0B.1 Create a Supabase project**:
  1. Go to https://supabase.com/dashboard and sign in (GitHub login works)
  2. Click **New project**
  3. Choose organization, set project name (e.g. `nauka-ai`), choose a strong database password (save it — you'll need it for the connection string), pick region **EU West (Ireland)** for lowest latency from Poland
  4. Wait ~2 minutes for provisioning

- [x] **0B.2 Get the pooler connection string** (for the Django app):
  1. In your project dashboard → **Project Settings** → **Database**
  2. Scroll to **Connection string** → select **Transaction** mode
  3. Copy the URI — it looks like:
     ```
     postgresql://postgres.[project-ref]:[password]@aws-0-eu-west-1.pooler.supabase.com:6543/postgres
     ```
  4. Save this as `DATABASE_URL` — this is the value for `fly secrets set DATABASE_URL=...`

  > **Port 6543 = Supavisor transaction pooler** — required for production to avoid exhausting the 25-connection limit on the free tier. Do NOT use port 5432 (direct) for the running app.

- [x] **0B.3 Get the direct connection string** (for running migrations only):
  1. Same Settings → Database page → select **Session** mode or scroll to **Direct connection**
  2. Copy the URI — format:
     ```
     postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
     ```
  3. Save separately — use this only when running `manage.py migrate` locally or via `fly ssh console`

  > Supavisor transaction mode doesn't support all session-level SQL commands Django uses during migrations. Use the direct connection (5432) for migrations, pooler (6543) for the running app.

- [x] **0B.4 Verify connectivity** from local machine (optional but recommended):
  ```powershell
  uv run python -c "
  import psycopg, os
  conn = psycopg.connect('postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres')
  print('Connected:', conn.info.server_version)
  conn.close()
  "
  ```
  > Run this after adding `psycopg[binary]` in Phase 1.1.

- [x] **0B.5 Note the Supabase project URL and anon key** (for future AI/API features):
  Project Settings → API → copy **Project URL** and **anon public** key.
  These are not needed for basic deployment but will be needed when wiring OpenRouter or Supabase client-side queries later.

---

## Phase 1 — Django Project Hardening
> Files changed: `pyproject.toml`, `config/settings.py`, `config/urls.py`

- [x] **1.1 Add production dependencies** to `pyproject.toml`:
  ```
  gunicorn          # WSGI production server
  psycopg[binary]   # PostgreSQL driver for Supabase
  whitenoise        # Static file serving in-process
  dj-database-url   # Parse DATABASE_URL env var
  python-dotenv     # Load .env for local dev
  ```
  Run: `uv add gunicorn "psycopg[binary]" whitenoise dj-database-url python-dotenv`

- [x] **1.2 Refactor `config/settings.py`** to read all secrets from env vars:
  ```python
  import os
  from pathlib import Path
  from dotenv import load_dotenv
  import dj_database_url

  load_dotenv()  # no-op in production (Fly secrets are real env vars)

  BASE_DIR = Path(__file__).resolve().parent.parent

  SECRET_KEY = os.environ['SECRET_KEY']          # required — no default
  DEBUG = os.environ.get('DEBUG', '0') == '1'
  ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

  # Fly.io auto-injects FLY_APP_NAME; append .fly.dev subdomain
  _fly_app = os.environ.get('FLY_APP_NAME')
  if _fly_app:
      ALLOWED_HOSTS.append(f'{_fly_app}.fly.dev')

  # Cloudflare proxy support
  SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
  USE_X_FORWARDED_HOST = True

  CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',')

  # Static files
  STATIC_URL = '/static/'
  STATIC_ROOT = BASE_DIR / 'staticfiles'

  WHITENOISE_USE_FINDERS = False

  # Database
  DATABASES = {
      'default': dj_database_url.config(
          default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
          conn_max_age=0,          # 0 = no pooling (Supabase Supavisor handles it)
          conn_health_checks=True,
      )
  }
  ```

- [x] **1.3 Add WhiteNoise to MIDDLEWARE** — second position (after `SecurityMiddleware`):
  ```python
  MIDDLEWARE = [
      'django.middleware.security.SecurityMiddleware',
      'whitenoise.middleware.WhiteNoiseMiddleware',   # ← add here
      ...
  ]
  ```

- [x] **1.4 Add `/healthz/` endpoint** to `config/urls.py` (required by Fly.io health checker; avoids deploy loops from Django's ALLOWED_HOSTS 400 response):
  ```python
  from django.http import HttpResponse
  urlpatterns = [
      path('healthz/', lambda request: HttpResponse('ok'), name='healthz'),
      path('admin/', admin.site.urls),
      path('stats/', include('stats.urls')),
  ]
  ```

- [x] **1.5 Create `.env` for local development** (add `.env` to `.gitignore`):
  ```
  SECRET_KEY=local-dev-key-replace-me
  DEBUG=1
  ALLOWED_HOSTS=localhost,127.0.0.1
  DATABASE_URL=          # leave blank to use SQLite locally
  ```

---

## Phase 2 — Containerisation
> Files created: `Dockerfile`, `fly.toml`, `.dockerignore`

- [x] **2.1 Create `Dockerfile`** at project root:
  ```dockerfile
  FROM python:3.14-slim

  # Install uv from official image
  COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

  ENV PYTHONDONTWRITEBYTECODE=1 \
      PYTHONUNBUFFERED=1 \
      UV_SYSTEM_PYTHON=1

  WORKDIR /app

  # Dependencies first for layer caching
  COPY pyproject.toml uv.lock ./
  RUN uv sync --frozen --no-dev

  COPY . .

  # Build-time placeholder — overridden by Fly secrets at runtime
  # Required because collectstatic loads Django settings (needs SECRET_KEY)
  ENV SECRET_KEY=placeholder-for-build \
      DJANGO_SETTINGS_MODULE=config.settings \
      DATABASE_URL=sqlite:////tmp/build.db \
      ALLOWED_HOSTS=localhost

  RUN uv run python manage.py collectstatic --noinput

  EXPOSE 8080

  CMD ["uv", "run", "gunicorn", "config.wsgi:application", \
       "--bind", "0.0.0.0:8080", \
       "--workers", "2", \
       "--timeout", "30", \
       "--access-logfile", "-"]
  ```

- [x] **2.2 Create `.dockerignore`**:
  ```
  .git
  .env
  db.sqlite3
  __pycache__
  *.pyc
  .python-version
  staticfiles/
  ```

- [x] **2.3 Run `fly launch`** from project root to auto-generate `fly.toml`:
  ```powershell
  fly launch --no-deploy
  ```
  When prompted: choose app name, region `waw` (Warsaw), skip Postgres and Redis (using Supabase externally).

- [x] **2.4 Edit generated `fly.toml`** — critical overrides:
  ```toml
  app = '<your-app-name>'
  primary_region = 'waw'

  [build]
    # Uses Dockerfile automatically

  [http_service]
    internal_port = 8080
    force_https = true
    auto_stop_machines = 'off'     # never sleep — avoids cold starts
    auto_start_machines = true
    min_machines_running = 1

    [[http_service.checks]]
      grace_period = "10s"
      interval = "30s"
      method = "GET"
      timeout = "5s"
      path = "/healthz/"           # custom endpoint, not / — avoids 400 from ALLOWED_HOSTS

  [[vm]]
    memory = '256mb'
    cpu_kind = 'shared'
    cpus = 1
  ```

---

## Phase 3 — Fly.io Initial Deployment
> Manual steps — requires Fly.io account + Supabase project ready

- [x] **3.1 Allocate a dedicated IPv4** (required for Cloudflare A record, costs $2/mo):
  ```powershell
  fly ips allocate -v 4
  fly ips list    # note both IPv4 and IPv6 for DNS setup
  ```
  IPv4: 169.155.49.210 / IPv6: 2a09:8280:1::11a:a155:0

- [x] **3.2 Set production secrets** (never committed to repo):
  ```powershell
  fly secrets set `
    SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(50))')" `
    DATABASE_URL="postgres://user:pass@db.supabase.co:6543/postgres" `
    DEBUG=0 `
    ALLOWED_HOSTS="<yourapp>.fly.dev" `
    CSRF_TRUSTED_ORIGINS="https://<yourapp>.fly.dev"
  ```
  > Use Supabase Supavisor port **6543**, not direct port 5432.

- [x] **3.3 Run database migrations** — handled automatically via `release_command` in fly.toml.

- [x] **3.4 Deploy**:
  ```powershell
  fly deploy
  ```
  Verify: `fly status`, `fly logs`, check `https://<yourapp>.fly.dev/healthz/` returns `ok`.

- [x] **3.5 Confirm Python 3.14** in build output — look for `FROM python:3.14-slim` in the deploy log. If 3.12 appears, the Dockerfile was not edited correctly (Step 2.1).

---

## Phase 4 — Cloudflare DNS + SSL Integration
> **SKIPPED** — brak własnej domeny. Apka dostępna pod `https://naukaai.fly.dev`. Faza 4 może być wdrożona w przyszłości po zakupie domeny.

### 4A — Certificate ownership (run before enabling orange cloud)

- [x] **4.1 Register custom domain cert with Fly.io**:
  ```powershell
  fly certs add yourdomain.com
  fly certs setup yourdomain.com   # copy the _fly-ownership TXT record value
  ```

- [ ] **4.2 Add TXT record in Cloudflare** (DNS tab):
  | Type | Name | Content | Proxy |
  |---|---|---|---|
  | TXT | `_fly-ownership` | (value from `fly certs setup`) | DNS-only (grey) |

- [ ] **4.3 Add A and AAAA records** pointing to Fly.io IPs (from Step 3.1):
  | Type | Name | Content | Proxy |
  |---|---|---|---|
  | A | `@` | `169.155.49.210` | DNS-only (grey) initially |
  | AAAA | `@` | `2a09:8280:1::11a:a155:0` | DNS-only (grey) initially |
  | CNAME | `www` | `yourdomain.com` | DNS-only (grey) initially |

- [ ] **4.4 Verify cert issued** (wait 1–3 min for DNS propagation):
  ```powershell
  fly certs check yourdomain.com
  ```
  Both RSA and ECDSA should show green. If not, run `fly certs check` again after 2 more minutes.

### 4B — Enable Cloudflare proxy (orange cloud)

- [ ] **4.5 Set SSL/TLS mode to "Full (strict)"** in Cloudflare dashboard:
  SSL/TLS → Overview → select **Full (strict)**
  > Do NOT use Flexible (causes redirect loops) or Full without strict (allows MITM).

- [ ] **4.6 Enable "Always Use HTTPS"**:
  SSL/TLS → Edge Certificates → Always Use HTTPS → ON

- [ ] **4.7 Turn ON proxy (orange cloud)** for A, AAAA, and www CNAME records in Cloudflare DNS tab.

- [ ] **4.8 Update Django secrets to include custom domain**:
  ```powershell
  fly secrets set `
    ALLOWED_HOSTS="yourdomain.com,www.yourdomain.com,naukaai.fly.dev" `
    CSRF_TRUSTED_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"
  ```

- [ ] **4.9 Redeploy** to apply new secrets:
  ```powershell
  fly deploy
  ```

- [ ] **4.10 Smoke test via Cloudflare proxy**:
  - `https://yourdomain.com/healthz/` → `ok`
  - Cloudflare dashboard → Analytics shows requests flowing through proxy
  - Django admin at `https://yourdomain.com/admin/` loads with CSS (WhiteNoise serving static)

### 4C — Edge cases & extra support steps

- [ ] **4.11 If cert check stays pending >5 min**: The `_fly-ownership` TXT record may not have propagated. Verify with `dig TXT _fly-ownership.yourdomain.com` and run `fly certs check` again. Do not turn on orange cloud before certs are green.

- [ ] **4.12 If redirect loop on HTTPS**: Verify Cloudflare SSL mode is "Full (strict)" (not Flexible). Verify `SECURE_PROXY_SSL_HEADER` is set in Django settings. Check `fly logs` for what header the request is arriving with.

- [ ] **4.13 If Django returns 400 Bad Request**: `ALLOWED_HOSTS` does not include the domain. Run `fly ssh console -C "env | grep ALLOWED_HOSTS"` to confirm the secret is set correctly.

- [ ] **4.14 If Django admin CSS missing**: WhiteNoise middleware is missing or in the wrong position. It must be the second item in `MIDDLEWARE` (immediately after `SecurityMiddleware`). Verify `STATIC_ROOT` and that `collectstatic` ran in the build.

- [ ] **4.15 If Supabase connection errors**: Confirm `DATABASE_URL` uses port 6543 (Supavisor pooler), not 5432 (direct). Check Supabase project is in active state and connection string credentials are correct.

---

## Phase 5 — Auto-Deploy on Push to `master` (Fly.io native)
> Fly.io's auto-deploy uses GitHub Actions — `fly launch` generates the workflow file automatically.
> File created: `.github/workflows/fly.yml`

- [x] **5.1 Let `fly launch` generate the workflow** — when prompted during `fly launch --no-deploy`, answer **Yes** to "Do you want to set up GitHub Actions deployment?". Fly auto-generates `.github/workflows/fly.yml`. — f9c4009

- [x] **5.2 Edit `.github/workflows/fly.yml`** — confirm it targets `master`: — f9c4009
  ```yaml
  name: Fly Deploy
  on:
    push:
      branches:
        - master
  jobs:
    deploy:
      name: Deploy app
      runs-on: ubuntu-latest
      concurrency: deploy-production
      steps:
        - uses: actions/checkout@v4
        - uses: superfly/flyctl-actions/setup-flyctl@master
        - run: flyctl deploy --remote-only
          env:
            FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
  ```

- [x] **5.3 Add `FLY_API_TOKEN` to GitHub repository secrets**: — f9c4009
  1. Generate token: `fly tokens create deploy -x 999999h`
  2. GitHub repo → Settings → Secrets and variables →do Actions → New repository secret → `FLY_API_TOKEN`

- [x] **5.4 Test**: Push a trivial change to `master`, confirm green Actions run and `fly status` shows a new version. — f9c4009

---

## Phase 6 — End-to-End Verification

- [x] `https://naukaai.fly.dev/healthz/` returns `ok` (HTTP 200)
- [x] `https://naukaai.fly.dev/admin/` loads Django admin with CSS
- [x] Cloudflare Analytics shows traffic (proxy is active, not DNS-only) — SKIPPED (Phase 4 skipped, no custom domain)
- [x] `fly certs check yourdomain.com` shows RSA and ECDSA as green — SKIPPED (Phase 4 skipped, no custom domain)
- [x] `fly logs` shows no OOM kills or health check failures
- [x] GitHub Actions deploy succeeds on push to `master`
- [x] Cloudflare SSL shows "Full (strict)" in dashboard — SKIPPED (Phase 4 skipped, no custom domain)

---

## Critical Files

| File | Status | Action |
|---|---|---|
| `config/settings.py` | exists, needs full rewrite | env-var reading, WhiteNoise, SECURE_PROXY_SSL_HEADER |
| `config/urls.py` | exists, needs 1 line | add `/healthz/` route |
| `pyproject.toml` | exists, needs deps | add gunicorn, psycopg, whitenoise, dj-database-url, python-dotenv |
| `Dockerfile` | missing | create from scratch (python:3.14-slim + uv) |
| `fly.toml` | missing | generated by `fly launch --no-deploy`, then edited |
| `.dockerignore` | missing | create |
| `.env` | missing | create for local dev (gitignored) |
| `.github/workflows/fly.yml` | missing | generated by `fly launch`, then edited for `master` branch |
