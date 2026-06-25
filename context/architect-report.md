---
title: Raport Architektoniczny — Moduł 4 (10xArchitect)
created: 2026-06-25
type: architect-report
artifacts:
  L2: context/map/repo-map.md
  L3: context/changes/complete-study-session/research.md
  L4: context/changes/complete-study-session/plan.md
  L5: context/domain/01-domain-distillation.md, 02-invariant-aggregate-refactor.md, 03-anti-corruption-layer.md
---

# Raport Architektoniczny — Moduł 4

---

## 1. Opisane projekty

| Repo | Stack | Skala | Artefakt |
|------|-------|-------|---------|
| **naukaAI** | Django 6.0, Python ≥ 3.14, SQLite/PostgreSQL, uv | Solo dev, 2 mies., 53 commity, ~580 ln testów | L2, L3, L4, L5 |

Wszystkie cztery artefakty pochodzą z jednego repozytorium.

---

## 2. Mapa projektu (L2 — `context/map/repo-map.md`)

**5 stref ryzyka (według repo-map.md):**

1. **God View** — `flashcards/views.py`: 201 linii, 7 klas, 10 funkcji/metod, 16 commitów. Cała logika domenowa w jednym pliku; każda feature ląduje tutaj.
2. **Ukryty blast radius** — `stats/services.py → flashcards.CardReview`: jedyne cross-app sprzężenie w Pythonie. Zmiana schematu `CardReview` psuje `stats` bez sygnału typecheckera.
3. **session.py** — 1 commit, 0 unit testów. Kontrakt 5 kluczy sesji (SK) współdzielony przez 4 widoki — literówka = cichy `KeyError` w runtime.
4. **config/urls.py** — logika biznesowa (redirect po login/register) w warstwie konfiguracyjnej.
5. **packages/code-reviewer/** — osobny stack TypeScript bez przeanalizowanego grafu importów (unknown).

**Centrum aktywności:** `flashcards/views.py` + `flashcards/tests.py` zmieniają się razem przy każdej feature (co-change potwierdzone w historii gita). `templates/base.html` zmienia się przy każdej zmianie nawigacji.

---

## 3. Analiza ficzera (L3 — `research.md`)

**Wybór przepływu:** `complete-study-session` — north star projektu (roadmap S-01); bezpośrednio odpowiada strefie ryzyka #1 (God View) i #3 (session.py).

**Feature overview:** Użytkownik wybiera temat → `session_start` tasuje karty i inicjalizuje 5 kluczy SK w session dict → `study_card` wyświetla karty po jednej, zapisuje `CardReview` do DB per odpowiedź → `session_results` odczytuje SK.SCORE i czyści sesję. Szósty endpoint, `study_review`, przejmuje `SK.LAST_WRONG_IDS` z poprzedniej sesji do powtórki błędnych kart. Jedyny produkcyjny zapis do DB: `CardReview.objects.create()` w `views.py:179`.

**Technical debt (ast-grep verified):**

| # | Ryzyko | Dowód |
|---|--------|-------|
| **TD-1** | God View — cała logika sesji, CRUD, spaced-rep w jednym pliku | `views.py`: 201 ln, 16 commitów (raport: 15) — korekta ast-grep |
| **TD-3** | `stats/services.py` zna 4 pola `CardReview` bezpośrednio; zmiana schematu psuje stats bez błędu kompilatora | `stats/services.py:7,22,26,33,59` — ast-grep + grep |
| **TD-4** | `study_review` (views.py:139) był pominięty w pierwotnym opisie przepływu; to 4. widok piszący do SK i 6. endpoint sesji | `views.py:151-155` — odkryto przez ast-grep (wzorzec `request.session[SK.*]`) |

---

## 4. Plan refaktoryzacji (L4 — `plan.md`)

**Status: ZAIMPLEMENTOWANY** — wszystkie kroki `[x]` z SHA commitów (`62248fa`, `fbaec0d`, `8539c1a`).

**Co zrefaktoryzowano:** Stateless random-card loop → trzyekranowy flow: topic selection → ordered deck traversal → score screen. Stan sesji w Django session dict (5 kluczy SK).

**Czego świadomie NIE zrobiono** (cytat z plan.md):
- `"No StudySession DB model — session state lives in the Django session dict only."`
- `"No resume of an interrupted session."`
- Brak spaced-repetition (S-04), brak leaderboardu (S-02).

**Fazy:**

| Faza | Co | Weryfikacja |
|------|----|-------------|
| P1: Topic entry point | Dodanie topics screen, aktualizacja 3 hardcoded redirectów | auto: pytest + ręcznie: 5 kroków |
| P2: Session loop | `session_start` + przepisanie `study_card` na session-aware | auto: pytest + 3 testy HTTP + ręcznie: 4 kroki |
| P3: Score screen + testy | `session_results`, template, 5 przypadków integracyjnych | auto: 5 testów pytest + ręcznie: E2E |

---

## 5. Domena wg DDD (L5 — `context/domain/`)

**Ubiquitous Language — 5 kluczowych pojęć:**

| Termin | Definicja (z PRD) | Status w kodzie |
|--------|-------------------|----------------|
| **Study Session** | Sesja nauki jednej talii od wyboru do wyniku | BRAK modelu — ephemeral dict (session.py:6-13) |
| **Card Review** | Jednorazowa odpowiedź (correct/incorrect) na kartę | Model istnieje — `models.py:37` |
| **Session Score** | Liczba poprawnych odpowiedzi — jedyny feedback dla użytkownika | SK.SCORE w session dict; **nie persystowane** |
| **Deck** | Talia kart należących do tematu jako jednostka | BRAK modelu — realizacja: `topic.cards.values_list()` |
| **Lifetime Total** | Suma is_correct=True ze wszystkich sesji — podstawa leaderboardu | Obliczany on-demand `COUNT(*)`, nie persystowany |

**Najważniejszy rozjazd model-vs-kod (D-1):** PRD i roadmap mówią "Study Session" jako koncepcja; kod nie ma modelu `StudySession` — plan.md explicite: *"No StudySession DB model"*.

---

**Niezmiennik #1: Score Accuracy** (`02-invariant-aggregate-refactor.md`)

> "Score accuracy: the final score must reflect the user's actual answers. A wrong score breaks the only feedback loop the app provides." — prd.md Guardrails

**Gdzie łamany:** `SK.SCORE` (session dict) i `CardReview` (DB) to dwa niezależne liczniki bez transakcji. Double-submit POST tworzy dwa `CardReview` dla tej samej karty i dwukrotnie podnosi `SK.SCORE` — brak unique constraint na `(session, card)`.

**Agregat-strażnik:** `StudySession` z metodą `record_answer(card_id, is_correct)` + `SessionCardReview` z `unique_together=[('session','card')]`. Score = `session.session_reviews.filter(is_correct=True).count()` — jedyne źródło prawdy.

---

**Anti-Corruption Layer** (`03-anti-corruption-layer.md`)

**Przeciek #1:** `stats/services.py:7` — `from flashcards.models import CardReview`. Domena `stats` zna 4 pola wewnętrzne `flashcards` (`user`, `reviewed_at`, `is_correct`, `related_name='card_reviews'`) i 5 wzorców ORM query. Dotknięte: `stats/services.py` (5 queries) + `stats/tests.py` (3 bezpośrednie create).

**ACL:** `ReviewPort` (ABC) + `ReviewRecord` (VO) + `FlashcardsReviewAdapter`. Kryterium sukcesu: `grep "CardReview" stats/` zwraca tylko `stats/adapters/flashcards_review.py`.

---

## 6. Decyzje, które należą do mnie

1. **Brak StudySession model (plan.md)** — AI zidentyfikowało ryzyko double-submit i brak historii sesji; Ty świadomie wybrałeś session dict dla MVP (`"No StudySession DB model"`). To decyzja prędkości vs. bezpieczeństwa guardrail — właściwa dla 3-tygodniowego sprintu.

2. **Admin role (prd.md Open Question #3)** — AI odnotowało kolizję między "flat user model" a FR-007 (must-have). Decyzja nierozstrzygnięta w artefaktach — blokuje S-03 (admin deck seeding).

3. **Streak i Next Review** — AI odkryło `_compute_streak` i `_compute_next_review` w `stats/services.py` bez żadnego odniesienia w PRD. Czy to zamierzona feature, czy przypadkowy overhead? Nie widać Twojej decyzji w artefaktach.

4. **ACL i StudySession refaktor** — oba plany domenowe (L5) to propozycje AI. Żaden nie trafił jeszcze do `context/changes/` jako zatwierdzony plan. Decyzja: które z tych długów technicznych realizujesz po MVP, a które parkujesz?