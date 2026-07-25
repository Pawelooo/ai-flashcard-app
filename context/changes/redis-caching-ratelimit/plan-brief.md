# Redis Caching and Rate Limiting — Plan Brief

> Full plan: `context/changes/redis-caching-ratelimit/plan.md`

## What & Why

Dodajemy Redis jako backend cache i rate-limiter do aplikacji Django, która nie ma żadnego cachowania ani ochrony endpointów. Cel: zmniejszyć obciążenie bazy danych dla globalnych danych (leaderboard, tematy) i zabezpieczyć endpointy auth oraz sesji przed nadużyciami.

## Starting Point

Aplikacja używa domyślnego DummyCache (brak cache) i nie ma żadnego rate limitingu. `get_leaderboard()` odpytuje bazę przy każdym żądaniu; login i register są otwarte na brute-force.

## Desired End State

Leaderboard i lista tematów są serwowane z Redis cache (TTL 15 min / 1 dzień). Login, register i session_start mają limity requestów (10/min per IP, 20/h per user). Redis niedostępny → aplikacja działa normalnie (fail open). Deweloper startuje Redis jednym poleceniem: `docker compose up -d`.

## Key Decisions Made

| Decyzja | Wybór | Dlaczego |
|---------|-------|----------|
| Co cachować | Leaderboard + tematy | Globalne, rzadko zmieniane; najwyższy gain |
| TTL leaderboard | 15 minut | Balans między świeżością a redukcją DB queries |
| TTL tematów | 1 dzień | Tematy zmieniają się tylko gdy admin doda nowy |
| Dev Redis | docker-compose | Paritet prod/dev; jeden plik, jedno polecenie |
| Prod Redis | Upstash Redis | External serverless, HTTP API, free tier |
| Rate limit auth | 10/min per IP | Standardowa ochrona brute-force |
| Rate limit sesji | 20/h per user | Blokuje skrypty, nie blokuje aktywnych uczniów |
| Resilience | IGNORE_EXCEPTIONS + FAIL_OPEN | App działa gdy Redis jest niedostępny |

## Scope

**In scope:**
- Cache: `get_leaderboard()` (15 min TTL), `TopicsListView` (1 dzień TTL)
- Rate limit: `LoginView` + `RegisterView` (10/min IP), `session_start` (20/h user)
- Infrastruktura: `django-redis`, `django-ratelimit`, `docker-compose.yml`, `.env.example`
- Resilience: fail-open gdy Redis down

**Out of scope:**
- Per-user stats caching (`compute_study_stats`)
- Cache invalidation przez sygnały Django
- Upstash konfiguracja (tylko `REDIS_URL` env var — user ustawia sam)
- WebSocket, Celery, monitoring

## Architecture / Approach

Redis jest jedyną nową zależnością zewnętrzną. `django-redis` zastępuje domyślny DummyCache jako backend `CACHES['default']`. `django-ratelimit` używa tego samego backendu do przechowywania liczników — dlatego Phase 1 (Redis setup) musi być przed Phase 3 (rate limiting). Caching (Phase 2) i rate limiting (Phase 3) są niezależne od siebie.

## Phases at a Glance

| Faza | Co dostarcza | Główne ryzyko |
|------|-------------|---------------|
| 1. Redis Infrastructure | CACHES w settings, docker-compose, .env.example | Redis niedostępny w testach → rozwiązane przez IGNORE_EXCEPTIONS |
| 2. Caching | Leaderboard + tematy serwowane z cache | Queryset nie zewaluowany przed cache.set → rozwiązane przez list() |
| 3. Rate Limiting | Auth + session_start chronione | handler429 musi być module-level function, nie lambda |

**Prerequisites:** `django-redis>=7.0.0` i `django-ratelimit>=4.1.0` zainstalowane (już w pyproject.toml)
**Estimated effort:** ~1 sesja, 3 fazy

## Open Risks & Assumptions

- Upstash Redis wymaga ustawienia `REDIS_URL` przez użytkownika — nie jest automatycznie konfigurowany w tym planie.
- Testy mogą wymagać `override_settings(CACHES=...)` jeśli REDIS_URL jest ustawiony w środowisku testowym bez działającego Redis.

## Success Criteria (Summary)

- `uv run python manage.py test` przechodzi bez Redis uruchomionego lokalnie
- Leaderboard i tematy są w Redis cache po pierwszym żądaniu (`redis-cli KEYS "*"`)
- 11. żądanie POST do `/accounts/login/` zwraca HTTP 429
