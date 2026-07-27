<!-- IMPL-REVIEW-REPORT -->
# Implementation Review: Redis Caching and Rate Limiting

- **Plan**: context/changes/redis-caching-ratelimit/plan.md
- **Scope**: Phase 1-3 of 3 (full plan)
- **Date**: 2026-07-26
- **Verdict**: REJECTED (gate rule: 1 CRITICAL Safety & Quality finding)
- **Findings**: 1 critical, 2 warnings, 0 observations
- **Resolution (2026-07-27)**: All 3 findings FIXED — see Decision lines below.

## Verdicts

| Dimension | Verdict |
|-----------|---------|
| Plan Adherence | PASS |
| Scope Discipline | PASS |
| Safety & Quality | FAIL |
| Architecture | PASS |
| Pattern Consistency | PASS |
| Success Criteria | WARNING |

## Findings

### F1 — Per-IP rate limit is meaningless behind Fly.io's proxy

- **Severity**: ❌ CRITICAL
- **Impact**: 🔬 HIGH — architectural stakes; think carefully before deciding
- **Dimension**: Safety & Quality
- **Location**: config/urls.py:60-68, flashcards/views.py:43
- **Detail**: `key='ip'` reads `request.META['REMOTE_ADDR']` (django_ratelimit/core.py:33). No `RATELIMIT_IP_META_KEY` set in config/settings.py. `fly.toml` confirms Fly.io deploy target. Fly's edge proxy means REMOTE_ADDR reflects Fly's gateway IP, not the real client — Fly exposes the true client IP via `Fly-Client-IP` header instead. In production, the "10/min per IP" bucket is shared across all real visitors, not per-client. One bursty client can lock every real user out of login/register repeatedly. Breaks the plan's own Desired End State: "Login and register endpoints block at 10 POST requests/minute per IP."
- **Fix A ⭐ Recommended**: Set `RATELIMIT_IP_META_KEY = 'HTTP_FLY_CLIENT_IP'` in settings.py
  - Strength: One-line fix using Fly's trusted, edge-set header (can't be client-spoofed).
  - Tradeoff: Fly-specific; needs revisiting if the app ever moves off Fly.
  - Confidence: HIGH — documented Fly.io trusted-header behavior.
  - Blind spot: Not verified against a live Fly deployment.
- **Fix B**: Accept as-is for MVP, document the limitation
  - Strength: Zero code change.
  - Tradeoff: Bug exists regardless of traffic volume — all traffic funnels through Fly's edge IPs.
  - Confidence: MEDIUM — real risk even at low request volume.
  - Blind spot: Unclear how many distinct gateway IPs Fly rotates per region.
- **Decision**: FIXED (Fix A, adapted) — `RATELIMIT_IP_META_KEY` set to a callable (`_ratelimit_client_ip` in config/settings.py) rather than the literal string `'HTTP_FLY_CLIENT_IP'`, because django_ratelimit raises `ImproperlyConfigured` when a string-keyed META header is absent (true for every non-Fly request: local dev, CI, test suite). The callable falls back to `REMOTE_ADDR` when the Fly header isn't present. Verified via `manage.py check` (0 issues) and `manage.py test` (69/69 passing).

### F2 — Topic list cache has no invalidation path (24h staleness)

- **Severity**: ⚠️ WARNING
- **Impact**: 🔎 MEDIUM — real tradeoff; pause to reason through it
- **Dimension**: Safety & Quality
- **Location**: flashcards/views.py:20-33, flashcards/admin.py:4
- **Detail**: `topics_list` cached for `CACHE_TTL_TOPICS` = 24h. `Topic` registered in admin with bare `admin.site.register(Topic)` (no save/delete override); `seed_cards.py:73` uses `get_or_create`. Neither busts the cache. CLAUDE.md states the admin panel is "wired for content seeding" — a newly added Topic can be invisible for up to 24h. The plan's "What We're NOT Doing" only excludes invalidation signals for CardReview/per-user stats, never considers Topic — a blind spot, not a deliberate scope call.
- **Fix A ⭐ Recommended**: Invalidate on Topic write via signal or admin override
  - Strength: `post_save`/`post_delete` on Topic (or `save_model`/`delete_model` override) calling `cache.delete('topics_list')` makes seeding instant; Topic writes are admin-only and rare.
  - Tradeoff: A few lines of new code in an area the plan otherwise avoided touching.
  - Confidence: HIGH — negligible cost, directly fixes the seeding workflow.
  - Blind spot: None significant.
- **Fix B**: Shorten CACHE_TTL_TOPICS during active content seeding
  - Strength: Zero new code — just lower the constant (e.g. 15m).
  - Tradeoff: Doesn't eliminate staleness, only shrinks the window.
  - Confidence: MEDIUM — good mitigation, not a full fix.
  - Blind spot: None significant.
- **Decision**: FIXED (Fix A) — added `flashcards/signals.py` with `post_save`/`post_delete` receivers on `Topic` that call `cache.delete('topics_list')`, wired up via `FlashcardsConfig.ready()` in `flashcards/apps.py`. Admin and `seed_cards.py` writes now invalidate the cache immediately instead of waiting out the 24h TTL. Verified via `manage.py test` (71/71 passing).

### F3 — Testing Strategy's promised unit tests were never written

- **Severity**: ⚠️ WARNING
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Success Criteria
- **Location**: flashcards/tests.py (missing), stats/tests.py (missing)
- **Detail**: plan.md's Testing Strategy promises two unit tests: (1) "Leaderboard view returns 200 with Redis unavailable" and (2) "authenticated POST to session_start succeeds on attempt 1, fails with 429 on attempt 21 (requires overriding rate to 1/h)." Neither exists — flashcards/tests.py has zero references to ratelimit/429; LeaderboardViewTests.setUp only calls cache.clear(), never exercising the Redis-down path. Phase 3's actual Success Criteria checkboxes (3.1/3.2 — generic manage.py test/check) passed and don't require these specific tests, so this is a plan-vs-delivery gap, not a failed checkbox — but the 429 behavior verified manually has no regression protection.
- **Fix**: Add both tests — an override-rate test in flashcards/tests.py asserting 429 on the 2nd session_start POST when rate is forced to 1/h, and a stats/tests.py test pointing CACHES at an unreachable Redis (IGNORE_EXCEPTIONS) asserting the leaderboard view still returns 200.
- **Decision**: FIXED (adapted) — added `SessionStartRateLimitTests` in `flashcards/tests.py` (loops 20 successful POSTs to `session_start` then asserts the 21st returns 429; forces `LocMemCache` via `override_settings` so the counter is deterministic regardless of whether a local Redis is reachable — this machine's `.env` has `REDIS_URL` set but Redis wasn't running, which would otherwise fail the ratelimit check open) and `LeaderboardRedisDownTests` in `stats/tests.py` (points `CACHES` at an unreachable Redis with `IGNORE_EXCEPTIONS` + a short `SOCKET_CONNECT_TIMEOUT`/`SOCKET_TIMEOUT` so the test fails fast instead of hanging, asserts `/stats/leaderboard/` still returns 200). Verified via `manage.py test` (71/71 passing).
