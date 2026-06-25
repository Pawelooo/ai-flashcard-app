# Artifact 3 — Kontrybutorzy: kto wie co i o co go zapytać

> Wychodzi z: `context/map/artifact-1-territory.md` + `context/map/artifact-2-structure.md`.  
> Zakres: ostatnie 12 miesięcy. Odfiltrowano: boty, automatyzacje, commity agentów AI (Claude Sonnet — `Co-Authored-By` bez wyraźnego ludzkiego autora jako `git author`).

---

## Identyfikacja obszarów — Top 5 wymagających kontaktu

Na podstawie artifact-1 (aktywność) i artifact-2 (ryzyka strukturalne):

| # | Obszar | Dlaczego wymaga kontaktu |
|---|--------|--------------------------|
| 1 | `flashcards/views.py` | Najgorętszy plik (15 commitów), God View — każda zmiana dotyka całej logiki sesji, CRUD i guards |
| 2 | `stats/services.py → flashcards.models` | Jedyne cross-app sprzężenie; zmiana `CardReview` ma ukryty blast radius w `stats` |
| 3 | `flashcards/session.py` | Nowy moduł (1 commit), kontrakt 5 kluczy sesji współdzielony przez 3 widoki — brak testów własnych |
| 4 | `config/urls.py` | Logika biznesowa (redirect) w warstwie konfiguracji — zidentyfikowane naruszenie granicy warstw |
| 5 | `packages/code-reviewer/src/` | Osobna paczka TypeScript, 7 commitów w czerwcu, aktywnie rozwijana w kierunku CI/CD |

---

## Linia wsparcia — kto pracował przy danym obszarze

> Filtr: `git log --pretty=format:"%an"` — odrzucono wpisy gdzie `author = Claude Sonnet 4.6` (żaden commit nie ma takiego `git author`; Claude pojawia się wyłącznie w `Co-Authored-By` w treści commita, nie jako git author).

### Kontrybutor: Pawelooo / Paweł
**E-mail:** paweloo0147@gmail.com (ta sama osoba, różnica konfiguracji `user.name`)  
**Commity łącznie:** 53 (jedyny kontrybutor)

---

### Obszar 1: `flashcards/views.py` — 15 commitów

| Data | Commit | Tematyka |
|------|--------|----------|
| 2026-06-14 | `refactor(refactor-opportunities): migrate study_* (p2–p5)` | Migracja do SK constants — 4 commity z rzędu |
| 2026-06-11 | `feat(crud-gap-analysis): data foundation, detail view, permissions (p1–p3)` | CRUD + owner guard, `created_by` FK |
| 2026-06-03 | `test(testing-score-accuracy): partial session fix + tests (p3)` | Naprawa partial-session bug |
| 2026-05-30 | `fix(s-01): apply impl-review fixes` | Post-review poprawki |
| 2026-05-27 | `feat(complete-study-session): p1–p3` | Cały flow sesji: topics → study → results |
| 2026-05-26 | Initial scaffold | Bazowy widok `study` |

**Klasyfikacja wiedzy:** architektura sesji (SK keys), CRUD + permission guards, topic/card flow, refaktoring warstw.

---

### Obszar 2: `stats/services.py` — 2 commity

| Data | Commit | Tematyka |
|------|--------|----------|
| 2026-05-30 | `feat(leaderboard): Phase 1 — service, view, and URL` | Dodanie `get_leaderboard()` |
| 2026-05-26 | Initial scaffold | Bazowy `compute_study_stats()` |

**Klasyfikacja wiedzy:** agregacja `CardReview` (ORM queries), stats dashboard, leaderboard service.  
**Uwaga:** serwis nie był modyfikowany od czasu dodania leaderboardu — może być stabilny lub niedotknięty.

---

### Obszar 3: `flashcards/session.py` — 1 commit

| Data | Commit | Tematyka |
|------|--------|----------|
| 2026-06-14 | `refactor(refactor-opportunities): scaffold flashcards/session.py (p1)` | Wydzielenie SK constants z `views.py` |

**Klasyfikacja wiedzy:** kontrakt kluczy sesji (`session_topic_id`, `session_cards`, `session_index`, `session_score`, `session_wrong_ids`), uzasadnienie dla `SK` klasy.  
**Ryzyko:** jeden commit, brak własnych testów — kontrybutor wie dlaczego te nazwy, inni nie.

---

### Obszar 4: `config/urls.py` — 2 commity

| Data | Commit | Tematyka |
|------|--------|----------|
| 2026-05-27 | `feat(complete-study-session): topic selection entry point (p1)` | Zmiana redirectu home/register na `flashcards:topics` |
| 2026-05-26 | Initial scaffold | Bazowa konfiguracja URL |

**Klasyfikacja wiedzy:** auth flow (redirect po login/register), HomeView dispatch logic.

---

### Obszar 5: `packages/code-reviewer/src/` — 7 commitów

| Data | Commit | Tematyka |
|------|--------|----------|
| 2026-06-25 | `feat(code-review-evals): add agent factory and subprocess eval provider (p3)` | `createCodeReviewerAgent`, ESM/CJS subprocess pattern |
| 2026-06-24 | `feat(ci-cd): add openrouter-model input to composite action` | GHA input dla modelu |
| 2026-06-24 | `feat(ci-cd): extend code-reviewer package for CI use (p1)` | `DIFF_FILE`, `PR_TITLE` env vars |
| 2026-06-21 | `feat(tool-loop-agent): add main.ts (p5), ToolLoopAgent (p4), prompts (p3), schema (p2)` | Cały agent stack |

**Klasyfikacja wiedzy:** AI SDK (`ToolLoopAgent`), OpenRouter API, Zod schemas, promptfoo eval, GHA composite action, TLS workaround (`NODE_TLS_REJECT_UNAUTHORIZED`).

---

## Podsumowanie

Projekt jednosobowy — **brak bus factora > 1**. Cała wiedza operacyjna (sesja Django, CRUD guards, TypeScript agent, CI/CD) leży u jednej osoby. Brak możliwości "zapytania innego kontrybutora" — wszelkie niejasności wymagają albo odczytania historii commitów, albo dokumentacji w `context/changes/`.

**Najsłabiej udokumentowany obszar:** `flashcards/session.py` — 1 commit, brak docstringu w `SK`, brak testów jednostkowych. Uzasadnienie dla nazw kluczy sesji istnieje wyłącznie w `context/changes/complete-study-session/plan.md`.