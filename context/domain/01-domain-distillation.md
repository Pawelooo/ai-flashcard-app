---
title: Domain Distillation — AI Flashcard App
created: 2026-06-25
type: domain-distillation
sources:
  - context/foundation/prd.md
  - context/foundation/shape-notes.md
  - context/foundation/roadmap.md
  - flashcards/models.py
  - flashcards/views.py
  - flashcards/session.py
  - stats/services.py
  - stats/types.py
method: "KROK 0–5: odkrycie → ubiquitous language → subdomeny → agregaty → MODEL vs KOD → ranking"
---

# Domain Distillation — AI Flashcard App

---

## KROK 0 — Kontekst projektu

**Stack:** Django 6.0, Python ≥ 3.14, SQLite (dev) / PostgreSQL (prod, Fly.io). Package manager: `uv`.

**Struktura warstw:**

| Warstwa | Gdzie |
|---------|-------|
| Routing / konfiguracja | `config/urls.py`, `config/settings.py` |
| Logika domenowa + CRUD + sesja | `flashcards/views.py` (God View, 201 ln) |
| Modele domenowe | `flashcards/models.py` |
| Kontrakt sesji HTTP | `flashcards/session.py` (SK class) |
| Analityka (readonly) | `stats/services.py`, `stats/types.py` |
| Szablony | `templates/`, `flashcards/templates/` |

**Dokumenty źródłowe:** `context/foundation/prd.md` (v1, draft), `shape-notes.md`, `roadmap.md`.  
**Ograniczenie:** PRD ma 3 otwarte pytania, w tym **Open Question #3** (model roli Admin) oznaczony jako `Block: yes` — FR-007 jest `must-have` ale nieimplementowalny bez decyzji.

---

## KROK 1 — Ubiquitous Language

> Zasada: cytuj źródło. Nie wymyślaj pojęć — odkrywaj je.

| # | Termin | Definicja (z dokumentu) | Cytat źródłowy | Gdzie w kodzie |
|---|--------|--------------------------|----------------|----------------|
| UL-01 | **Topic** (Temat) | Zagadnienie AI/ML grupujące zbiór fiszek | "pick an AI topic" — prd.md FR-002 | `flashcards/models.py:6` (`class Topic`) |
| UL-02 | **Card** (Fiszka) | Para pytanie/odpowiedź przypisana do tematu | "flip through flashcards" — prd.md FR-003 | `flashcards/models.py:14` (`class Card`) |
| UL-03 | **Deck** (Talia) | Wszystkie karty danego tematu traktowane jako jednostka do przestudiowania | "study a deck of flashcards" — prd.md FR-003; "create topic decks" — FR-007 | BRAK modelu. Realizacja: `topic.cards.values_list()` — `flashcards/views.py:36` |
| UL-04 | **Study Session** (Sesja Nauki) | Przelotna sesja nauki jednej talii od wyboru tematu do wyniku | "complete a deck of flashcards" — prd.md US-01; "a session boundary" — roadmap.md S-01 Unknowns | BRAK modelu. Realizacja: dict w Django session pod kluczami SK — `flashcards/session.py:6-13` |
| UL-05 | **Card Review** (Ocena Karty) | Jednorazowa odpowiedź użytkownika (correct/incorrect) na kartę w ramach sesji | "mark each as correct or incorrect" — prd.md FR-003 | `flashcards/models.py:37` (`class CardReview`), `flashcards/views.py:179` |
| UL-06 | **Session Score** (Wynik Sesji) | Liczba poprawnych odpowiedzi w danej sesji | "score that accurately reflects how many cards they marked correct" — prd.md FR-004; Guardrail: "A wrong score breaks the only feedback loop" — prd.md | `flashcards/session.py:10` (`SK.SCORE`); `flashcards/views.py:63` (percent) |
| UL-07 | **Lifetime Total** (Łączny wynik) | Suma wszystkich is_correct=True ze wszystkich sesji użytkownika | "cumulative total of correct answers across all study sessions" — prd.md Business Logic | Obliczany: `stats/services.py:15` (`Count('card_reviews', filter=Q(is_correct=True))`). Nie persystowany. |
| UL-08 | **Leaderboard** (Tablica liderów) | Ranking wszystkich użytkowników wg Lifetime Total, malejąco | "ranking of all students ordered by score" — prd.md FR-005 | `stats/services.py:12` (`get_leaderboard()`) |
| UL-09 | **Missed Cards** (Błędne karty) | Karty ocenione jako incorrect w danej sesji; wejście do Spaced Repetition Review | "resurfaces cards the user got wrong in a prior session" — prd.md secondary success criteria | `flashcards/session.py:11` (`SK.WRONG_IDS`); `flashcards/views.py:60` |
| UL-10 | **Spaced Repetition Review** (Powtórka słabych kart) | Sesja nauki Missed Cards z poprzedniej sesji; "handoff" przez SK.LAST_WRONG_IDS | "review cards they got wrong in a prior session" — prd.md FR-006 (nice-to-have) | `flashcards/views.py:139` (`study_review`); `flashcards/session.py:12` (`SK.LAST_WRONG_IDS`) |
| UL-11 | **Streak** (Seria) | Liczba kolejnych dni z co najmniej jedną Oceną Karty | BRAK w PRD — nie wymieniony | `stats/services.py:57` (`_compute_streak`); `stats/types.py:8` (`StudyStats.streak`) |
| UL-12 | **Study Stats** (Statystyki nauki) | Agregowane dane aktywności: dzisiaj, % poprawnych, seria, ostatnia/następna powtórka | BRAK wprost w PRD — implied przez leaderboard/analytics context | `stats/types.py:4` (`StudyStats` dataclass); `stats/services.py:19` (`compute_study_stats`) |
| UL-13 | **Next Review** (Następna powtórka) | Data kiedy użytkownik powinien wrócić do nauki | BRAK w PRD | `stats/services.py:49` (`_compute_next_review`): zawsze today lub today+1 — nie jest prawdziwym SRS |
| UL-14 | **Admin** | Rola z uprawnieniami do tworzenia talii i seedowania kart AI | "Admin can create topic decks" — prd.md FR-007; model roli: Open Question #3 UNRESOLVED | De facto: `is_staff` check — `flashcards/views.py:104`. Brak jawnej decyzji o modelu roli. |
| UL-15 | **User** (Użytkownik) | Zarejestrowany learner — deweloper przygotowujący się do rozmowy AI/ML | "Any developer brushing up on AI" — prd.md User & Persona; FR-001 | Django built-in auth — `AUTH_USER_MODEL` references w `flashcards/models.py:22,38` |

---

## KROK 2 — Subdomeny: Core / Supporting / Generic

> Rdzeń = to, co stanowi przewagę i sens produktu. Kryterium: success criteria i guardrails z prd.md.

| Subdomena | Kategoria | Uzasadnienie (cytat PRD) |
|-----------|-----------|--------------------------|
| Study Session + Card Review + Session Score | **CORE** | Primary success criterion: "User can pick an AI topic, study a deck of flashcards, and receive a score that accurately reflects which cards they marked correct. This flow working end-to-end = the product works." Guardrail: "A wrong score breaks the only feedback loop." |
| Spaced Repetition Review | **CORE** (secondary) | Secondary success criterion: "app resurfaces cards the user got wrong in a prior session, automatically prioritizing weak spots." Nice-to-have FR-006 — but directly tied to product differentiator. |
| Leaderboard / Lifetime Total | **SUPPORTING** | FR-005 (must-have) ale "adoption signal" — nie przewaga produktu, lecz mechanizm motywacyjny. "With few early users the leaderboard will be empty and useless" — acknowledged risk. |
| Topic / Deck discovery | **SUPPORTING** | FR-002, FR-007 — infrastruktura treści; prerequisite for Core, but content management is commodity. |
| Study Stats / Streak / Next Review | **SUPPORTING** | Nie w PRD success criteria. Streak i next_review nie są wymienione w PRD w ogóle. |
| Authentication | **GENERIC** | FR-001 — rozwiązane przez Django built-in auth. "Login is required for the ranking feature" — prereq, nie differentiator. |
| Admin / CMS | **GENERIC** | FR-007 + Django admin panel — commodity CMS. Blocked przez Open Question #3. |

---

## KROK 3 — Kandydaci na agregaty i ich niezmienniki

### AG-1: StudySession (brak modelu — stan w Django session)

**Niezmiennik:** Każda karta w talii musi być oceniona dokładnie raz per sesja. Score musi być wyliczany z tych samych odpowiedzi co CardReview records.

> Cytat: "Score accuracy: the final score must reflect the user's actual answers. A wrong score breaks the only feedback loop the app provides." — prd.md Guardrails

**Status w kodzie:**
- `flashcards/session.py:6-13` — stan sesji to `dict` w `request.session` (Django cookie/DB backend). **NIE persystowany jako model.**
- `flashcards/views.py:179` — `CardReview.objects.create(...)` jedyny zapis do DB, bez transakcji otaczającej sesję
- **Niezmiennik IGNOROWANY:** double-submit (szybkie podwójne kliknięcie POST) może utworzyć dwa `CardReview` dla tej samej karty; `SK.SCORE` byłby rozsynchronizowany z `CardReview` records

**Ryzyko:** WYSOKIE — naruszenie guardrail "score accuracy" bez sygnału

---

### AG-2: CardReview (model istnieje)

**Niezmiennik:** `CardReview` musi dotyczyć karty z aktualnej sesji użytkownika (card_id == cards[index]).

> Cytat: implied by US-01 — odpowiedź musi być przypisana do właściwej karty w sekwencji

**Status w kodzie:**
- `flashcards/views.py:175-176` — `if card_id != card_ids[index]: return redirect` — **EGZEKWOWANY**
- `flashcards/views.py:179` — `CardReview.objects.create(user=request.user, card=card, is_correct=is_correct)` — **POPRAWNY**
- `flashcards/models.py:43-48` — `card = FK(Card, on_delete=SET_NULL, null=True)` — karta może być usunięta po ocenie; `CardReview` zostaje z `card=NULL`

**Ryzyko:** NISKIE dla rdzenia; ŚREDNIE dla integrity (null card FK po usunięciu karty)

---

### AG-3: Topic/Deck (model Topic istnieje, Deck jako model — brak)

**Niezmiennik:** Sesja nauki może się rozpocząć tylko jeśli temat ma co najmniej jedną kartę.

> Cytat: "User can see available AI topics on the home screen and select one to study" — FR-002 (implied: topic must have cards)

**Status w kodzie:**
- `flashcards/views.py:38-40` — `if not card_ids: messages.warning(...); return redirect('flashcards:topics')` — **EGZEKWOWANY**
- **Koncepcja Deck:** `topic.cards.values_list('id', flat=True)` (views.py:36) — `Deck` jest lazy-evaluated list of IDs, przetasowanych przed sesją. **BRAK dedykowanego modelu.**

**Ryzyko:** NISKIE (niezmiennik egzekwowany), ale brak modelu Deck = brak historii "jaką talię przestudiowano"

---

### AG-4: Leaderboard / Lifetime Total

**Niezmiennik:** `Lifetime Total = SUM(is_correct=True) across all CardReview of user`, włącznie z Spaced Repetition Review sessions.

> Cytat: "Correct answers from spaced-repetition review sessions count equally toward the lifetime total." — prd.md Business Logic

**Status w kodzie:**
- `stats/services.py:14-16` — `Count('card_reviews', filter=Q(card_reviews__is_correct=True))` — obliczany na żądanie, **NIE persystowany**
- `flashcards/views.py:151` — `study_review` ustawia `SK.TOPIC_ID = None` — review session jest nieodróżnialna od normalnej w `CardReview` (brak flagi `is_review=True`)
- **Niezmiennik DEKLAROWANY, obliczany poprawnie** — ale review session nie jest oznaczona w DB

**Ryzyko:** NISKIE (obliczenia poprawne), POTENCJALNIE ŚREDNIE przy dużej skali (pełny scan CardReview per request)

---

## KROK 4 — MODEL vs KOD: rozjazdy

| # | Dokument mówi X | Kod robi Y | Dowód (plik:linia) |
|---|----------------|------------|---------------------|
| **D-1** | "Study Session" jako koncepcja domenowa (US-01, roadmap S-01: "what constitutes one session") | Brak modelu `StudySession` — stan sesji to ephemeral dict (`SK`) w Django session; po zakończeniu sesji brak rekordu "odbyłem sesję" | `flashcards/session.py:6-13` |
| **D-2** | "Deck" = talia kart jako jednostka (FR-007: "create topic decks", FR-003: "study a deck") | Brak modelu `Deck` — deck = `topic.cards` (relacja ForeignKey). Brak historii "jaką talię w jakim składzie przestudiowano" | `flashcards/views.py:36`; `flashcards/models.py:15-20` |
| **D-3** | "Score accuracy: the final score must reflect the user's actual answers" — Guardrail | Score w `SK.SCORE` (session dict) i `CardReview` records mogą się rozsynchronizować przy double-submit POST (brak transakcji / idempotency guard) | `flashcards/views.py:179,182,188` |
| **D-4** | "Progress and deck state are persisted per account across devices" — prd.md Access Control | `SK` klucze w Django session (domyślnie DB backend, ale powiązane z session_key, nie z user_id). Sesja niedokończona nie jest dostępna z innego urządzenia. | `flashcards/session.py:6-13` |
| **D-5** | "Correct answers from spaced-repetition review sessions count equally toward the lifetime total" — Business Logic (explicit parity) | `CardReview.objects.create(...)` w `study_review` (views.py:179) — identyczne jak normalna sesja. Ale `TOPIC_ID=None` (views.py:151) oznacza brak rozróżnienia review vs normal w danych; analityka nie odróżni tych sesji | `flashcards/views.py:151`; `flashcards/models.py:37-57` |
| **D-6** | FR-007: "Admin can create topic decks" — UNRESOLVED (Open Question #3) | Kod używa `is_staff` check w `CardEditPermissionMixin` (views.py:104) jako de facto admin role — nieudokumentowana decyzja, sprzeczna z "flat user model" z Access Control section | `flashcards/views.py:100-106`; prd.md Open Question #3 |
| **D-7** | Brak wzmianki o **Streak** i **Next Review** w PRD | `_compute_streak` i `_compute_next_review` zaimplementowane i eksponowane w `StudyStats`; `next_review` zawsze = today lub today+1 (brak prawdziwego SRS) | `stats/services.py:49-67`; `stats/types.py:4-11` |
| **D-8** | Spaced Repetition opisana jako "resurfaces cards user got wrong in a **prior** session" (FR-006) | Implementacja przenosi LAST_WRONG_IDS z jednej sesji wyłącznie do następnej review (LIFO, jeden poziom głębokości). Wiele przegranych sesji = tylko ostatnia jest review'owana | `flashcards/session.py:12`; `flashcards/views.py:144` |

---

## KROK 5 — Ranking refaktoru

> Kryterium: **wartość** (jak rdzeniowy niezmiennik) × **ryzyko** (jak słabo egzekwowany dziś)

| Rank | Kandydat | Wartość | Ryzyko | Uzasadnienie |
|------|----------|---------|--------|--------------|
| **#1** | `StudySession` jako agregat (D-1, D-3, D-4) | CORE — primary success criterion | WYSOKIE — brak modelu, brak atomiczności, brak historii sesji | Guardrail "score accuracy" jest zagrożony bez transakcji / idempotency; PRD Open Question w S-01 bezpośrednio sygnalizuje niepewność modelu. Bez `StudySession` niemożliwe: sesja na wielu urządzeniach (D-4), audyt wyniku, replay. |
| **#2** | `Deck` jako koncepcja z historią (D-2) | SUPPORTING CORE — prerequisite flow | ŚREDNIE — action działa, ale nie ma śladu co przestudiowano | Bez modelu `Deck`: brak możliwości "wróć do tej samej talii", brak ewolucji decków (dodanie karty nie zmienia historii), FR-007 admin seeding nie ma granicy zarządzanego obiektu. |
| **#3** | Review session tracking (D-5, D-8) | SUPPORTING CORE — FR-006 | NISKIE-ŚREDNIE — działa poprawnie dla happy path | LAST_WRONG_IDS = jeden poziom głębokości; brak rozróżnienia review vs normal w `CardReview` uniemożliwia analitykę "ile razy karta była review'owana". Gdy FR-006 urośnie do full SRS, brak tej informacji blokuje algorytm. |
| **#4** | Admin role resolution (D-6) | GENERIC (unblocking FR-007) | WYSOKIE — blokuje must-have FR-007 | Nie jest domainowym refaktorem, lecz decyzją organizacyjną. Ale `is_staff` jako de facto admin bez dokumentacji to latający dług. |

### #1 do refaktoru: `StudySession` jako persystowany agregat

**Dlaczego pierwsze?** Guardrail "score accuracy" jest jedynym hard requirement jakości w PRD. Bez persystowanego `StudySession`:
1. Double-submit może zduplikować `CardReview` → rozsynchronizować score (D-3)
2. Niedokończona sesja jest utracona przy zamknięciu przeglądarki (D-4)
3. Niemożliwe odtworzenie "która sesja dała jaki wynik" (D-1)
4. Lifetime Total nie jest przypisywalny do konkretnych sesji (D-5)

Minimalny agregat `StudySession(user, topic, started_at, completed_at, score, cards_snapshot)` rozwiązuje D-1, D-3, D-4 jednocześnie i nie wymaga zmiany `CardReview` schema.

---

## Separacja dowodów

**EVIDENCE (file:line zweryfikowany):** wszystkie cytaty kodu w tym dokumencie.

**INFERENCE:** D-3 (double-submit risk) — warunek możliwy, nie zaobserwowany w produkcji; D-4 (cross-device) — założenie na podstawie Django session mechanics.

**UNKNOWN:** Czy `D-7` (Streak, Next Review) jest zaplanowany do usunięcia lub rozwoju? Brak wzmianki w roadmap.md i PRD — niezidentyfikowana feature.