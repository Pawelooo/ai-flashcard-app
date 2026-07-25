
# Redis Caching and Rate Limiting — Implementation Plan

## Overview

Add Redis as the cache backend and rate-limiting store to the AI Flashcard App. Currently the app has no caching (default DummyCache) and no protection on auth or study endpoints. This change introduces `django-redis` for caching frequently-read global data and `django-ratelimit` to protect login, register, and session_start from brute-force and abuse.

## Current State Analysis

- `config/settings.py` has no `CACHES` key — Django uses DummyCache (no-op).
- `stats/services.py:12` — `get_leaderboard()` runs a DB aggregation query on every request with no caching.
- `flashcards/views.py:18` — `TopicsListView` queries `Topic.objects.all()` on every page load.
- `config/urls.py` — `LoginView` and `RegisterView` have no rate limiting.
- `flashcards/views.py:31` — `session_start` has no rate limiting.
- `pyproject.toml` — `django-redis>=7.0.0` and `django-ratelimit>=4.1.0` added (installed).
- No `docker-compose.yml` exists; no `.env.example` documents required env vars.

## Desired End State

- `REDIS_URL` env var controls the cache backend: set → `django-redis`; unset → `LocMemCache` fallback.
- `get_leaderboard()` returns cached data for 15 minutes; topic list cached for 1 day.
- Login and register endpoints block at 10 POST requests/minute per IP.
- `session_start` blocks at 20 POST requests/hour per authenticated user.
- Redis unavailability is silent: `IGNORE_EXCEPTIONS=True` + `RATELIMIT_FAIL_OPEN=True` keep the app running.
- `docker-compose.yml` runs Redis 7 locally; `.env.example` documents `REDIS_URL`.

### Key Discoveries

- `get_leaderboard()` in `stats/services.py:12` must `list()` the queryset before caching — Django querysets are lazy and cannot be pickled.
- `django-ratelimit` uses the configured cache backend as its counter store — so Redis setup in Phase 1 is a prerequisite for Phases 2 and 3.
- `TopicsListView.get_queryset()` returns a queryset, not a list — the cache must store a `list()` to avoid lazy evaluation issues.
- `handler429` must be defined as a module-level function in `config/urls.py` (not a lambda) so Django can resolve it as the 429 error handler.

## What We're NOT Doing

- No per-user stats caching (`compute_study_stats`) — it changes after every session and its DB queries are cheap.
- No cache invalidation signals (post_save on CardReview) — TTL-based expiry is sufficient for MVP scale.
- No WebSocket or async infrastructure.
- No Celery or background task queue.
- No CI/CD pipeline changes.

## Implementation Approach

Three sequential phases that build on each other: Redis infrastructure first (Phase 1), then add cache calls to services and views (Phase 2), then add rate-limit decorators to views and URLs (Phase 3). Phase 1 must land before 2 and 3 because `django-ratelimit` reads from the cache backend.

---

## Phase 1: Redis Infrastructure

### Overview

Wire Redis as the Django cache backend via `REDIS_URL`, add LocMem fallback, configure resilience settings, create `docker-compose.yml` for local dev, and document env vars in `.env.example`.

### Changes Required

#### 1. Cache backend + constants

**File**: `config/settings.py`

**Intent**: Configure Django's cache backend to use `django-redis` when `REDIS_URL` is set, fall back to `LocMemCache` when it isn't (local dev without Docker, CI). Define TTL constants and rate-limit resilience flag used by later phases.

**Contract**: Append after `DEFAULT_AUTO_FIELD`:

- `REDIS_URL = os.environ.get('REDIS_URL')` — reads env var, `None` if absent.
- `CACHES` dict: when `REDIS_URL` is set, backend = `django_redis.cache.RedisCache`, location = `REDIS_URL`, options include `IGNORE_EXCEPTIONS: True`; else backend = `django.core.cache.backends.locmem.LocMemCache`.
- `CACHE_TTL_LEADERBOARD = 900` (15 min in seconds).
- `CACHE_TTL_TOPICS = 86400` (1 day in seconds).
- `RATELIMIT_FAIL_OPEN = True` — rate limiting fails open when cache is unavailable.

#### 2. Local Redis service

**File**: `docker-compose.yml` (new)

**Intent**: Provide a one-command local Redis for development so engineers don't need a system Redis install.

**Contract**: Single `redis` service, image `redis:7-alpine`, port `6379:6379`, `restart: unless-stopped`.

#### 3. Environment variable documentation

**File**: `.env.example` (new)

**Intent**: Document all required and optional env vars so new developers know what to set.

**Contract**: Include `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_URL`, `REDIS_URL=redis://localhost:6379/0`, and a comment showing the Upstash format for production.

### Success Criteria

#### Automated Verification

- `uv run python manage.py check` reports 0 issues with `REDIS_URL` unset (LocMem path).
- `uv run python manage.py check` reports 0 issues with `REDIS_URL=redis://localhost:6379/0` set.
- `uv run python manage.py test` passes with `REDIS_URL` unset (LocMem fallback used in tests).

#### Manual Verification

- `docker compose up -d` starts Redis container without errors.
- Django shell `from django.core.cache import cache; cache.set('x', 1); cache.get('x')` returns `1` with Redis running.
- Stopping Redis and reloading the app does not raise an exception (IGNORE_EXCEPTIONS silences it).

---

## Phase 2: Caching

### Overview

Wrap `get_leaderboard()` and `TopicsListView.get_queryset()` with cache read-through pattern using the TTL constants from Phase 1.

### Changes Required

#### 1. Leaderboard cache

**File**: `stats/services.py`

**Intent**: Cache the leaderboard aggregation query for `CACHE_TTL_LEADERBOARD` seconds so the expensive JOIN + annotation runs at most once per 15 minutes instead of on every leaderboard page load.

**Contract**: Import `cache` from `django.core.cache` and `settings` from `django.conf`. Before the DB query, `cache.get('leaderboard_top10')` — return hit immediately. On miss, evaluate the queryset with `list(...)`, `cache.set('leaderboard_top10', result, timeout=settings.CACHE_TTL_LEADERBOARD)`, then return result. The queryset must be evaluated to a `list` before caching.

#### 2. Topic list cache

**File**: `flashcards/views.py`

**Intent**: Cache the topic list in `TopicsListView` for `CACHE_TTL_TOPICS` seconds — topics change only when an admin adds/edits one, which is rare.

**Contract**: Import `cache` from `django.core.cache` and `settings` from `django.conf`. Override `get_queryset()`: `cache.get('topics_list')` → return hit; on miss `list(Topic.objects.order_by('name'))` → `cache.set('topics_list', result, timeout=settings.CACHE_TTL_TOPICS)` → return result. Drop the `ordering` class attribute (ordering is now in the queryset).

### Success Criteria

#### Automated Verification

- `uv run python manage.py test` passes.

#### Manual Verification

- Load `/stats/leaderboard/` twice; second request is faster (confirm via Django debug toolbar or log).
- Load `/flashcards/topics/` twice; second request serves from cache.
- With Redis running, `redis-cli KEYS "*"` shows `leaderboard_top10` and `topics_list` keys after first load.

---

## Phase 3: Rate Limiting

### Overview

Apply `@ratelimit` to `session_start` (per-user, 20/h) and wrap `LoginView` / `RegisterView` in `config/urls.py` (per-IP, 10/min). Add `handler429` to return a clean 429 response when a limit is exceeded.

### Changes Required

#### 1. Rate limit on session_start

**File**: `flashcards/views.py`

**Intent**: Prevent a logged-in user from spamming study sessions (e.g., scripted abuse that floods `CardReview`). Limit to 20 sessions per hour per user.

**Contract**: Import `ratelimit` from `django_ratelimit.decorators`. Add `@ratelimit(key='user', rate='20/h', block=True, method=['POST'])` between `@login_required` and the function body of `session_start`. The `@login_required` decorator must remain outermost so unauthenticated requests are redirected before the rate check.

#### 2. Rate limit on login and register + 429 handler

**File**: `config/urls.py`

**Intent**: Protect auth endpoints from brute-force login attempts and registration spam. Return a readable 429 response when limits are exceeded.

**Contract**:
- Import `ratelimit` from `django_ratelimit.decorators`.
- Define module-level `handler429(request, exception=None)` returning `HttpResponse('Zbyt wiele prób. Poczekaj chwilę i spróbuj ponownie.', status=429)`.
- In `urlpatterns`, create `_rate_auth = ratelimit(key='ip', rate='10/m', block=True, method=['POST'])` and apply it: `_rate_auth(auth_views.LoginView.as_view())` and `_rate_auth(RegisterView.as_view())`.

### Success Criteria

#### Automated Verification

- `uv run python manage.py test` passes.
- `uv run python manage.py check` reports 0 issues.

#### Manual Verification

- Submit login form 11 times rapidly → 11th attempt returns HTTP 429 with the Polish message.
- Submit register form 11 times rapidly → same result.
- Start 21 study sessions within an hour as the same user → 21st returns HTTP 429.
- After waiting 1 minute, login works again (rate window resets).

---

## Testing Strategy

### Unit Tests

- Leaderboard view returns 200 with Redis unavailable (IGNORE_EXCEPTIONS + RATELIMIT_FAIL_OPEN).
- Rate limit: authenticated POST to `session_start` succeeds on attempt 1, fails with 429 on attempt 21 (requires overriding rate to `1/h` in test).

### Manual Testing Steps

1. Start Redis: `docker compose up -d`.
2. Set `REDIS_URL=redis://localhost:6379/0` in `.env`.
3. Run dev server: `uv run python manage.py runserver`.
4. Open `/stats/leaderboard/` — check `redis-cli KEYS "*"` shows the cache key.
5. Open `/flashcards/topics/` — check `redis-cli KEYS "*"` shows topics key.
6. POST to `/accounts/login/` 11 times rapidly — confirm 429 on 11th.
7. Stop Redis (`docker compose down`) — confirm app still loads (fail-open).

## Performance Considerations

`get_leaderboard()` runs a `COUNT` + `JOIN` aggregation across all users. At MVP scale (<100 users) it's fast, but caching it eliminates the query entirely for 15 minutes. Topic list is a simple `SELECT` on a tiny table — 1-day TTL is conservative.

## References

- `stats/services.py:12` — `get_leaderboard()` target for caching
- `flashcards/views.py:18` — `TopicsListView` target for topic cache
- `flashcards/views.py:31` — `session_start` target for rate limiting
- `config/urls.py:59` — login/register URL entries for rate limiting
- `pyproject.toml` — `django-redis>=7.0.0`, `django-ratelimit>=4.1.0`

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands. Do not rename step titles. See `references/progress-format.md`.

### Phase 1: Redis Infrastructure

#### Automated

- [x] 1.1 `manage.py check` passes with REDIS_URL unset — b7f31b9
- [x] 1.2 `manage.py check` passes with REDIS_URL set — b7f31b9
- [x] 1.3 `manage.py test` passes with REDIS_URL unset — b7f31b9

#### Manual

- [x] 1.4 `docker compose up -d` starts Redis without errors — b7f31b9
- [x] 1.5 Cache round-trip works in Django shell with Redis running — b7f31b9
- [x] 1.6 App does not raise on Redis connection failure — b7f31b9

### Phase 2: Caching

#### Automated

- [x] 2.1 `manage.py test` passes

#### Manual

- [x] 2.2 Leaderboard served from cache on second request
- [x] 2.3 Topic list served from cache on second request
- [x] 2.4 `redis-cli KEYS "*"` shows expected keys after first load

### Phase 3: Rate Limiting

#### Automated

- [ ] 3.1 `manage.py test` passes
- [ ] 3.2 `manage.py check` reports 0 issues

#### Manual

- [ ] 3.3 11th rapid login attempt returns HTTP 429
- [ ] 3.4 11th rapid register attempt returns HTTP 429
- [ ] 3.5 21st session_start attempt returns HTTP 429
- [ ] 3.6 Rate window resets after 1 minute (login works again)
