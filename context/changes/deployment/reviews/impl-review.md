<!-- IMPL-REVIEW-REPORT -->
# Implementation Review: Deploy — Fly.io + Cloudflare

- **Plan**: context/changes/deployment/deployment-plan.md
- **Scope**: All phases (0A–6)
- **Date**: 2026-07-04
- **Verdict**: APPROVED (post-triage)
- **Findings**: 1 critical  5 warnings  3 observations

## Verdicts

| Dimension | Verdict |
|-----------|---------|
| Plan Adherence | WARNING |
| Scope Discipline | PASS |
| Safety & Quality | FAIL → FIXED |
| Architecture | PASS |
| Pattern Consistency | WARNING → FIXED |
| Success Criteria | PASS |

## Findings

### F1 — ENV SECRET_KEY=placeholder persists w finalnym obrazie

- **Severity**: ❌ CRITICAL
- **Impact**: 🔎 MEDIUM — realny tradeoff; zatrzymaj się i przemyśl
- **Dimension**: Safety & Quality
- **Location**: Dockerfile:16
- **Detail**: `ENV SECRET_KEY=placeholder-for-build` baked do finalnego obrazu Docker; widoczny przez `docker inspect`. Jeśli Fly.io secret nie ustawiony, app startuje z publicznym kluczem.
- **Fix**: Zamieniono ENV na ARG dla build-only zmiennych; ENV zostało tylko dla DJANGO_SETTINGS_MODULE.
- **Decision**: FIXED via Fix A

### F2 — /healthz/ nie sprawdza bazy danych

- **Severity**: ⚠️ WARNING
- **Impact**: 🔎 MEDIUM — realny tradeoff; zatrzymaj się i przemyśl
- **Dimension**: Safety & Quality
- **Location**: config/urls.py:48
- **Detail**: Health check zwracał `ok` bez sprawdzania bazy. Fly.io uznawałby maszynę za zdrową przy uszkodzonym PostgreSQL.
- **Fix**: Dodano `_healthz()` z `db_connection.ensure_connection()`, zwraca 503 przy błędzie DB.
- **Decision**: FIXED

### F3 — flyctl-actions@master — pływający ref

- **Severity**: ⚠️ WARNING
- **Impact**: 🏃 LOW — szybka decyzja; fix oczywisty i wąski
- **Dimension**: Safety & Quality
- **Location**: .github/workflows/fly.yml:16
- **Detail**: Pływający branch ref z dostępem do FLY_API_TOKEN.
- **Fix**: Zmieniono na `@v1`.
- **Decision**: FIXED

### F4 — Brak bloku permissions: w fly.yml

- **Severity**: ⚠️ WARNING
- **Impact**: 🏃 LOW — szybka decyzja; fix oczywisty i wąski
- **Dimension**: Pattern Consistency
- **Location**: .github/workflows/fly.yml
- **Detail**: Brak jawnego bloku `permissions:`, dziedziczenie domyślnych uprawnień repo.
- **Fix**: Dodano `permissions: contents: read`.
- **Decision**: FIXED

### F5 — conn_max_age=0 wyłącza pooling połączeń DB

- **Severity**: ⚠️ WARNING
- **Impact**: 🔎 MEDIUM — realny tradeoff; zatrzymaj się i przemyśl
- **Dimension**: Safety & Quality
- **Location**: config/settings.py:85
- **Detail**: Każdy request otwiera nowe połączenie TCP do Supabase (+5-15ms overhead).
- **Fix**: Dodano komentarz wyjaśniający że Supavisor transaction mode (port 6543) zarządza poolingiem server-side — `conn_max_age=0` jest celowe.
- **Decision**: FIXED via Fix B

### F6 — primary_region = 'arn' zamiast 'waw' z planu

- **Severity**: ⚠️ WARNING
- **Impact**: 🏃 LOW — szybka decyzja; fix oczywisty i wąski
- **Dimension**: Plan Adherence
- **Location**: fly.toml:2
- **Detail**: Plan specyfikował `waw` (Warszawa); faktyczna wartość to `arn` (Sztokholm).
- **Fix**: Zmieniono na `primary_region = 'waw'`.
- **Decision**: FIXED

### F7 — --workers 1: brak współbieżności

- **Severity**: 💡 OBSERVATION
- **Impact**: 🏃 LOW — szybka decyzja; fix oczywisty i wąski
- **Dimension**: Plan Adherence
- **Location**: Dockerfile:28
- **Detail**: Plan specyfikował 2 workery; implementacja używała 1.
- **Fix**: Zmieniono na `--workers 2`.
- **Decision**: FIXED

### F8 — Pusta CSRF_TRUSTED_ORIGINS zerwie custom domain w przyszłości

- **Severity**: 💡 OBSERVATION
- **Impact**: 🏃 LOW — szybka decyzja; fix oczywisty i wąski
- **Dimension**: Safety & Quality
- **Location**: config/settings.py:35
- **Detail**: Przy dodaniu ainauka.com wszystkie POST-y zwrócą 403 bez aktualizacji CSRF_TRUSTED_ORIGINS.
- **Fix**: Dodano komentarz w settings.py przypominający o aktualizacji.
- **Decision**: FIXED

### F9 — Filtr pustych stringów w ALLOWED_HOSTS/CSRF (drift od planu)

- **Severity**: 💡 OBSERVATION
- **Impact**: 🏃 LOW — szybka decyzja; fix oczywisty i wąski
- **Dimension**: Plan Adherence
- **Location**: config/settings.py:15,35
- **Detail**: Implementacja używa list comprehension zamiast `.split(',')` z planu.
- **Fix**: Zaktualizowano plan żeby odzwierciedlał faktyczną implementację.
- **Decision**: FIXED