---
title: Invariant Aggregate Refactor — StudySession Score Integrity
created: 2026-06-25
type: refactor-plan
sources:
  - context/foundation/prd.md
  - context/domain/01-domain-distillation.md
  - flashcards/models.py
  - flashcards/views.py
  - flashcards/session.py
  - flashcards/tests.py
scope: plan-only — no production code modified
---

# Invariant Aggregate Refactor — StudySession Score Integrity

---

## KROK 0 — Kontekst

**Stack:** Django 6.0, Python ≥ 3.14, SQLite (dev) / PostgreSQL (prod).

**Warstwy logiki biznesowej:**

| Warstwa | Lokalizacja | Rola dziś |
|---------|-------------|-----------|
| HTTP routing | `config/urls.py` | entry points |
| Business logic + CRUD | `flashcards/views.py` (God View, 201 ln) | **tu żyje cała logika sesji** |
| Session state | `flashcards/session.py` (SK dict) | ephemeral — Django session |
| Persistence | `flashcards/models.py` (CardReview) | jedyny zapis do DB |
| Analytics (readonly) | `stats/services.py` | agreguje CardReview |

**Kluczowy dokument:** `prd.md` — sekcja Guardrails: *"Score accuracy: the final score must reflect the user's actual answers. A wrong score breaks the only feedback loop the app provides."*

---

## KROK 1 — Inwentarz niezmienników biznesowych

| # | Niezmiennik | Źródło | Gdzie egzekwowany w kodzie |
|---|-------------|--------|---------------------------|
| **INV-1** | **Wynik sesji musi równać się liczbie is_correct=True CardReview z tej sesji** | prd.md Guardrails: "score must reflect actual answers" | NIE egzekwowany — SK.SCORE (session dict) i CardReview records to dwa niezależne liczniki bez transakcji |
| INV-2 | Każde POST musi dotyczyć karty aktualnej w sekwencji (card_id == cards[index]) | implied by US-01 ("flip through the deck") | EGZEKWOWANY — `views.py:175-176` — ale cicho (redirect, brak błędu domenowego) |
| INV-3 | Sesja może się rozpocząć tylko gdy talia ma ≥ 1 kartę | FR-003 (implied), FR-002 | EGZEKWOWANY — `views.py:38-40` |
| INV-4 | study_card wymaga obecności kluczy sesji (CARDS, INDEX, SCORE, WRONG_IDS) | implied by session flow | EGZEKWOWANY — `views.py:161-163` — ale cicho (redirect) |
| INV-5 | Każda karta jest oceniana dokładnie raz per sesja (brak duplikatu) | implied by US-01 "complete a deck" | **NIE egzekwowany** — brak unique constraint na (session, card); double-submit POST może stworzyć dwa CardReview dla tej samej karty |
| INV-6 | Spaced repetition review liczy się tak samo do Lifetime Total jak normalna sesja | prd.md Business Logic: "correct answers from review sessions count equally" | EGZEKWOWANY (przez przypadek) — ten sam `CardReview.objects.create()` niezależnie od typu sesji |

---

## KROK 2 — Klasyfikacja i wybór #1

| Niezmiennik | (a) Rdzeniowość | (b) Rozsmarowanie | (c) Egzekucja |
|-------------|----------------|-------------------|---------------|
| **INV-1 Score accuracy** | **CORE** — jedyny guardrail w PRD; "wrong score breaks the only feedback loop" | `session.py:10` (SK.SCORE) + `views.py:179,182` — dwa niezależne stany w dwóch warstwach | **NARUSZALNY** — brak transakcji; brak synchronizacji między SK.SCORE a CardReview count |
| INV-2 Card sequence | CORE (session integrity) | `views.py:175-176` (1 miejsce) | EGZEKWOWANY — cicho (redirect bez błędu) |
| INV-3 Deck non-empty | SUPPORTING | `views.py:38-40` (1 miejsce) | EGZEKWOWANY — poprawnie |
| INV-4 Session keys present | GENERIC (session hygiene) | `views.py:161-163` (1 miejsce) | EGZEKWOWANY — cicho |
| INV-5 No double-review | CORE (consequence of INV-1) | Brak — nigdzie | **IGNOROWANY** — naruszenie INV-1 przez brak unique constraint |

**Wybór #1: INV-1 (Score Accuracy) + INV-5 (No double-review) — traktowane jako jeden niezmiennik złożony.**

**Uzasadnienie:** INV-1 jest jedynym twardym gwarancją jakości w PRD (guardrail, nie nice-to-have). INV-5 jest jego mechanizmem ochrony. Oba są naruszalne dziś przez ten sam scenariusz: POST wysłany dwa razy dla tej samej karty tworzy dwa `CardReview` (INV-5), z czego jeden fałszywie podbija SK.SCORE (INV-1). Wynik widziany przez użytkownika jest niepoprawny — a PRD mówi wprost, że to niszczy jedyne sprzężenie zwrotne produktu.

---

## KROK 3 — Diagnoza INV-1 + INV-5

### Gdzie żyje reguła dziś — mapa warstw

```
prd.md (Guardrail)
  ↓ [tylko deklaracja]
flashcards/views.py:182          ← SK.SCORE += 1 (session dict, warstwa HTTP)
flashcards/views.py:179          ← CardReview.objects.create(...) (DB)
  ↑ brak transakcji łączącej te dwa zapisy
  ↑ brak unique constraint na (user, card, session)
  ↑ brak idempotency guard na POST
```

### Dokładne lokalizacje (file:line)

| Warstwa | Lokalizacja | Co robi | Problem |
|---------|-------------|---------|---------|
| Session dict | `flashcards/session.py:10` — `SCORE = "session_score"` | Definiuje klucz | Stan ulotny — znika po zamknięciu przeglądarki / wygaśnięciu sesji |
| HTTP view (increment) | `flashcards/views.py:182` — `request.session[SK.SCORE] += 1` | Podnosi licznik score | Brak transakcji z CardReview.create; może się wykonać nawet jeśli DB write failuje |
| HTTP view (DB write) | `flashcards/views.py:179` — `CardReview.objects.create(user=request.user, card=card, is_correct=is_correct)` | Persystuje ocenę | Może się wykonać wielokrotnie dla tej samej karty (brak unique constraint) |
| HTTP view (guard) | `flashcards/views.py:175-176` — `if card_id != card_ids[index]: return redirect` | Sprawdza sekwencję kart | Broni przed złą kartą, ale NIE przed powtórnym POST dla tej samej karty (race condition: dwa kliknięcia = card_id == cards[index] obydwa razy, bo index nie zdążył się zaktualizować) |
| Model | `flashcards/models.py:37-57` — `class CardReview` | Persystuje ocenę | Brak `unique_together(user, card, session)` — DB akceptuje duplikaty |
| Results view | `flashcards/views.py:58-59` — czyta `SK.SCORE`, `SK.CARDS` | Wyświetla wynik | **Wynik bierze z session dict, nie z DB** — jeśli session dict i DB się rozjechały, użytkownik widzi zły wynik |
| Stats service | `stats/services.py:15` — `Count('card_reviews', filter=Q(is_correct=True))` | Lifetime Total | Liczy z DB — może być różny od SK.SCORE (dwa źródła prawdy) |

### Scenariusze naruszenia

**S-1 — Double-submit (race condition):**
1. Użytkownik klika "Correct" dwa razy szybko
2. Dwa POST trafiają do `study_card` jednocześnie
3. Oba przechodzą guard `card_id == cards[index]` (index jeszcze nie zaktualizowany)
4. Dwa `CardReview.objects.create()` — dwa rekordy dla tej samej karty
5. SK.SCORE podnoszone dwukrotnie
6. Wynik sesji: zawyżony; Lifetime Total: zawyżony

**S-2 — Session dict / DB divergence:**
1. CardReview.create() succeeds
2. Serwer rzuca wyjątek przed `request.session[SK.SCORE] += 1`
3. DB ma ocenę, session dict jej nie liczy
4. Wynik sesji: zaniżony

**S-3 — Session expiry mid-session:**
1. Sesja wygasa (Django default: 2 tygodnie, ale może być krócej przy GC)
2. CardReview records zostają w DB
3. SK dict (SCORE, CARDS, INDEX, WRONG_IDS) — utracone
4. Niemożliwe odtworzenie stanu sesji z DB

---

## KROK 4 — Projekt agregatu-strażnika: `StudySession`

### Model agregatu

```python
# flashcards/models.py — nowe

class StudySession(models.Model):
    """Agregat-root dla niezmiennika score accuracy (INV-1 + INV-5)."""

    class Status(models.TextChoices):
        ACTIVE   = 'active',   'Active'
        COMPLETE = 'complete', 'Complete'
        REVIEW   = 'review',   'Spaced Repetition Review'

    user        = models.ForeignKey(AUTH_USER_MODEL, on_delete=CASCADE,
                                    related_name='study_sessions')
    topic       = models.ForeignKey('Topic', on_delete=SET_NULL,
                                    null=True, blank=True,
                                    related_name='study_sessions')
    card_ids    = models.JSONField()          # ordered list — deck snapshot at start
    status      = models.CharField(max_length=10, choices=Status,
                                   default=Status.ACTIVE)
    is_review   = models.BooleanField(default=False)  # odróżnia spaced-rep od normalnej
    started_at  = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=['user', 'status'])]

    # --- właściwości pochodne (nie persystowane) ---

    @property
    def score(self) -> int:
        """Jedyne źródło prawdy dla wyniku — liczy z CardReview."""
        return self.session_reviews.filter(is_correct=True).count()

    @property
    def total(self) -> int:
        return len(self.card_ids)

    @property
    def current_index(self) -> int:
        return self.session_reviews.count()

    # --- metody domenowe (z preconditions, fail-fast) ---

    def record_answer(self, card_id: int, is_correct: bool) -> 'SessionCardReview':
        """
        Preconditions:
          1. session.status == ACTIVE
          2. card_id == self.card_ids[current_index]  (właściwa karta w kolejności)
          3. Karta nie była jeszcze oceniona w tej sesji

        Raises:
          SessionNotActive     jeśli status != ACTIVE
          WrongCardInSequence  jeśli card_id != expected
          CardAlreadyReviewed  jeśli duplicate (unique constraint backup)
        """
        if self.status != self.Status.ACTIVE:
            raise SessionNotActive(f"Session {self.pk} is {self.status}")

        expected = self.card_ids[self.current_index]
        if card_id != expected:
            raise WrongCardInSequence(
                f"Expected card {expected}, got {card_id} at index {self.current_index}"
            )

        # DB-level unique constraint jest ostatnim strażnikiem (patrz SessionCardReview)
        review = SessionCardReview.objects.create(
            session=self,
            card_id=card_id,
            is_correct=is_correct,
        )

        if self.current_index >= self.total:
            self._complete()

        return review

    def _complete(self):
        """Prywatne — wywoływane przez record_answer gdy wszystkie karty ocenione."""
        self.status = self.Status.COMPLETE
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])


class SessionCardReview(models.Model):
    """Ocena jednej karty w ramach konkretnej sesji."""
    session    = models.ForeignKey(StudySession, on_delete=CASCADE,
                                   related_name='session_reviews')
    card       = models.ForeignKey('Card', on_delete=SET_NULL,
                                   null=True, blank=True)
    is_correct = models.BooleanField()
    reviewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('session', 'card')]  # ← DB-level guard INV-5
        # CardReview (legacy) pozostaje — SessionCardReview to nowy byt


# Błędy domenowe (nie wyjątki HTTP — mapowane w warstwie view)
class SessionNotActive(Exception): pass
class WrongCardInSequence(Exception): pass
class CardAlreadyReviewed(Exception): pass  # IntegrityError z unique_together
```

### Repozytorium

```python
# flashcards/repositories.py — nowe

class StudySessionRepository:
    @staticmethod
    def create(user, topic, card_ids: list[int], is_review: bool = False) -> StudySession:
        return StudySession.objects.create(
            user=user, topic=topic, card_ids=card_ids, is_review=is_review
        )

    @staticmethod
    def get_active(user) -> StudySession | None:
        return StudySession.objects.filter(
            user=user, status=StudySession.Status.ACTIVE
        ).select_related('topic').first()

    @staticmethod
    def get_by_id(session_id: int, user) -> StudySession:
        return get_object_or_404(StudySession, pk=session_id, user=user)
```

### Cienkie widoki (po refaktorze)

```python
# flashcards/views.py — sygnatury AFTER (pseudokod)

@login_required
def session_start(request):
    # parse
    topic = get_object_or_404(Topic, pk=request.POST.get('topic_id'))
    card_ids = list(topic.cards.values_list('id', flat=True))
    if not card_ids:
        messages.warning(request, 'Ten temat nie ma jeszcze fiszek.')
        return redirect('flashcards:topics')

    random.shuffle(card_ids)

    # domain — jedyna linia biznesowa
    session = StudySessionRepository.create(user=request.user, topic=topic,
                                            card_ids=card_ids)

    # SK przechowuje tylko ID — nie stan
    request.session[SK.SESSION_ID] = session.pk
    return redirect('flashcards:study')


@login_required
def study_card(request):
    session = StudySessionRepository.get_active(request.user)
    if not session:
        return redirect('flashcards:topics')

    if request.method == 'POST':
        try:
            card_id = int(request.POST.get('card_id', ''))
            session.record_answer(card_id, request.POST.get('is_correct') == '1')
        except (ValueError, WrongCardInSequence) as e:
            logging.warning("study_card bad POST: %s", e)
            return redirect('flashcards:study')
        except CardAlreadyReviewed:
            # idempotent — ignore duplicate, don't increment score
            return redirect('flashcards:study')
        except SessionNotActive:
            return redirect('flashcards:study_results')

        if session.status == StudySession.Status.COMPLETE:
            return redirect('flashcards:study_results')
        return redirect('flashcards:study')

    # GET
    idx = session.current_index
    if idx >= session.total:
        return redirect('flashcards:study_results')
    card = get_object_or_404(Card, pk=session.card_ids[idx])
    return render(request, 'flashcards/study.html', {
        'card': card, 'current': idx + 1, 'total': session.total
    })


@login_required
def session_results(request):
    session = StudySession.objects.filter(
        user=request.user, status=StudySession.Status.COMPLETE
    ).order_by('-completed_at').first()
    if not session:
        return redirect('flashcards:topics')

    wrong_ids = list(
        session.session_reviews.filter(is_correct=False).values_list('card_id', flat=True)
    )
    # score pochodzi z DB — jedyne źródło prawdy
    score = session.score
    total = session.total
    ...
```

### Atomowość

`record_answer()` tworzy `SessionCardReview` w jednej operacji DB. `unique_together = [('session', 'card')]` blokuje duplikat na poziomie DB — nawet przy równoległych żądaniach. `session.score` jest computed z tych samych rekordów co wyświetlany wynik — zero rozbieżności między "co widzi użytkownik" a "co jest w DB".

---

## KROK 5 — Before/After, plan, testy

### Before/After dla każdego miejsca reguły

| Lokalizacja | BEFORE | AFTER |
|-------------|--------|-------|
| `session.py:10` | `SCORE = "session_score"` — mutable counter w session dict | Usunięty — score pochodzi z `session.score` (DB) |
| `views.py:179` | `CardReview.objects.create(user, card, is_correct)` — bez kontekstu sesji | `session.record_answer(card_id, is_correct)` — metoda agregatu |
| `views.py:182` | `request.session[SK.SCORE] += 1` — nieatomowy increment | Usunięty — score = `session.session_reviews.filter(is_correct=True).count()` |
| `views.py:175-176` | `if card_id != card_ids[index]: return redirect` — cicha ścieżka | `raise WrongCardInSequence(...)` w `record_answer()` — named error, mapowany w view |
| `models.py` | `CardReview` bez constraint na unikalność (user, card, session) | `SessionCardReview` z `unique_together = [('session', 'card')]` |
| `session_results view` | Czyta `SK.SCORE` z session dict | Czyta `session.score` z DB |
| `stats/services.py:15` | `Count('card_reviews', ...)` — wszystkie CardReview łącznie | Może filtrować po `SessionCardReview.session.is_review` — odróżnia typy sesji |

### Plan faz (test-first gdzie zaznaczono)

**Faza 1 — Model + migracja** *(bez zmiany zachowania)*
- Dodaj `StudySession`, `SessionCardReview` do `models.py`
- Dodaj `unique_together` i indeksy
- `makemigrations && migrate`
- Testy: model-level unit testy (nie wymagają Django client)

**Faza 2 — Błędy domenowe + `record_answer()`** *(test-first)*
- Dodaj `SessionNotActive`, `WrongCardInSequence`, `CardAlreadyReviewed`
- Zaimplementuj `record_answer()` z preconditions
- Testy (przed implementacją): patrz lista przypadków testowych poniżej

**Faza 3 — Repozytorium + cienkie widoki**
- `StudySessionRepository.create()`, `get_active()`, `get_by_id()`
- Przepisz `session_start`, `study_card`, `session_results`, `study_review`
- SK.SESSION_ID jako jedyny klucz w session dict
- Testy: istniejące integracyjne w `flashcards/tests.py` muszą przejść bez zmian

**Faza 4 — Migracja istniejących danych (opcjonalna)**
- Stwórz `StudySession` retroaktywnie dla istniejących `CardReview` (best-effort, MVP może pominąć)
- Usuń stare SK keys z session dict istniejących sesji (graceful fallback)

**Faza 5 — Cleanup**
- Usuń `SK.SCORE`, `SK.CARDS`, `SK.INDEX`, `SK.WRONG_IDS` z `session.py`
- Zostaw `SK.SESSION_ID`, `SK.LAST_WRONG_IDS` (cross-session handoff)
- Aktualizuj `stats/services.py` — opcjonalnie filtruj po `is_review`

### Przypadki testowe dla INV-1 + INV-5

**Legalne przejścia (muszą przejść):**
```
T-L1: pełna sesja (N kart) → score = liczba is_correct=True → session.status=COMPLETE
T-L2: sesja z 1 kartą → score = 0 lub 1 → poprawna
T-L3: sesja spaced-repetition review → score liczy się tak samo jak normalna (is_review=True, ten sam count)
T-L4: record_answer(correct=False) → WRONG_IDS zaktualizowane, score niezmieniony
T-L5: results po zakończeniu → score == session.session_reviews.filter(is_correct=True).count()
```

**Nielegalne operacje (muszą rzucić błąd domenowy):**
```
T-I1: record_answer dla zamkniętej sesji (status=COMPLETE) → SessionNotActive
T-I2: record_answer(card_id=wrong_card) → WrongCardInSequence
T-I3: double-submit (dwa identyczne POST) → CardAlreadyReviewed (IntegrityError za unique_together) — score NIE zmienia się po pierwszym
T-I4: study_card GET bez aktywnej sesji → redirect topics (nie 500)
T-I5: session_results bez completed session → redirect topics
```

**Przejścia stanu (automaton):**
```
T-S1: ACTIVE → COMPLETE po record_answer ostatniej karty (current_index == total)
T-S2: ACTIVE → ACTIVE po record_answer karty pośredniej (current_index < total)
T-S3: COMPLETE → brak przejścia (terminal state)
```

### Nowe "load-bearing" nazwy do zarejestrowania

| Nazwa | Typ | Opis |
|-------|-----|------|
| `StudySession` | Aggregate Root | Egzekwuje INV-1 + INV-5 |
| `SessionCardReview` | Entity (child of StudySession) | Zastępuje bezpośrednie `CardReview` w flow sesji |
| `StudySessionRepository` | Repository | Jedyna brama do studySession persistence |
| `record_answer(card_id, is_correct)` | Domain Method | Jedyne miejsce zapisu oceny karty w sesji |
| `SessionNotActive` | Domain Error | Sesja zamknięta lub nieistniejąca |
| `WrongCardInSequence` | Domain Error | POST dla złej karty w sekwencji |
| `CardAlreadyReviewed` | Domain Error | Double-submit guard |
| `SK.SESSION_ID` | Session Key | Jedyny klucz sesji po refaktorze (zastępuje SK.SCORE, SK.CARDS, SK.INDEX, SK.WRONG_IDS) |

---

## Separacja dowodów

**EVIDENCE (zweryfikowane file:line):** wszystkie cytaty kodu w tym dokumencie opierają się na odczytach z tej sesji (`flashcards/views.py`, `models.py`, `session.py`, `stats/services.py`, `prd.md`).

**INFERENCE:** Scenariusz S-1 (double-submit race condition) jest możliwy przy standardowym HTTP — nie zaobserwowany w produkcji, ale niechroniony strukturalnie. Scenariusz S-2 (session dict / DB divergence) możliwy przy wyjątkach serwera między `.create()` a session increment.

**OUT OF SCOPE tego planu:** CardReview (legacy model) — pozostaje dla historycznych danych i stats. Migracja istniejących danych (Faza 4) — best-effort, nie blokuje bezpieczeństwa INV-1 w nowych sesjach.