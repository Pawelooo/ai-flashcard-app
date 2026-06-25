# Artifact 1 — Terytorium: historia zmian i aktywne obszary

> Zakres: ostatnie 12 miesięcy (projekt startował 2026-05, dane z 2 miesięcy).  
> Odfiltrowane: lockfile'y, node_modules, db.sqlite3, .env, pliki generowane.

---

## Aktywność — TOP folderów (commity zawierające zmiany w danym folderze)

| # | Folder | Commity |
|---|--------|---------|
| 1 | `flashcards/` | 45 |
| 2 | `stats/` | 17 |
| 3 | `flashcards/templates/flashcards/` | 12 |
| 4 | `context/changes/refactor-opportunities/` | 10 |
| 5 | `context/changes/crud-gap-analysis/` | 9 |
| 6 | `context/changes/tool-loop-agent/` | 9 |
| 7 | `context/changes/code-review-evals/` | 9 |
| 8 | `context/foundation/` | 8 |
| 9 | `context/changes/complete-study-session/` | 8 |
| 10 | `config/` | 8 |
| 11 | `packages/code-reviewer/` | 7 |
| 12 | `.github/actions/ai-code-review/` | 4 |

## Aktywność — TOP plików

| # | Plik | Commity |
|---|------|---------|
| 1 | `flashcards/views.py` | 15 |
| 2 | `flashcards/tests.py` | 13 |
| 3 | `flashcards/urls.py` | 7 |
| 4 | `templates/base.html` | 5 |
| 5 | `stats/tests.py` | 4 |
| 6 | `packages/code-reviewer/src/agent.ts` | 4 |
| 7 | `flashcards/models.py` | 3 |
| 8 | `config/settings.py` | 3 |
| 9 | `stats/views.py` | 2 |
| 10 | `stats/services.py` | 2 |

Wszystkie wymienione pliki istnieją w repo (zweryfikowano).

---

## Kwartały / timeline

Projekt ma tylko 2 miesiące historii:

| Okres | Commity |
|-------|---------|
| 2026-05 | 20 |
| 2026-06 | 33 |

**Obserwacja:** intensywność rośnie — czerwiec ma 65% więcej commitów niż maj. Projekt jest w fazie aktywnego budowania, nie utrzymania.

---

## Współzmiany — co zmienia się razem

Analiza kombinacji katalogów w tych samych commitach:

| Kombinacja | Commity | Interpretacja |
|------------|---------|---------------|
| `flashcards/` (sam) | 19 | Większość zmian jest izolowana w `flashcards` |
| `templates/` (sam) | 2 | Zmiany layoutu bez dotyku logiki |
| `stats/` (sam) | 2 | `stats` zmienia się niezależnie |
| `config + flashcards + stats + templates` | 2 | Duże cross-cuttingowe commity (np. routing, auth redirects) |
| `flashcards + stats` | 1 | Rzadka zmiana obu domen razem |

**Wspólny mianownik:** `templates/base.html` (5 commitów) — zmienia się razem z nawigacją, auth, theme. To plik łączący wszystkie warstwy UI. Nie jest hubem w sensie importów, ale jest hubem UI.

**Wniosek:** `flashcards/views.py` + `flashcards/tests.py` to de facto centrum projektu — każda feature ląduje w tych dwóch plikach. Brak naturalnej separacji między widokami (`views.py` 201 linii, rośnie).