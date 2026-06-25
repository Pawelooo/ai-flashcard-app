---
title: Anti-Corruption Layer — stats → flashcards.CardReview
created: 2026-06-25
type: refactor-plan
sources:
  - context/foundation/prd.md
  - context/foundation/tech-stack.md
  - pyproject.toml
  - stats/services.py
  - stats/types.py
  - stats/views.py
  - stats/tests.py
  - flashcards/models.py
  - config/urls.py
scope: plan-only — no production code modified
---

# Anti-Corruption Layer — stats → flashcards.CardReview

---

## KROK 0 — Kontekst

**Stack:** Django 6.0, Python ≥ 3.14. Zależności zewnętrzne z `pyproject.toml`:

| Pakiet | Rola | Warstwa gdzie używany |
|--------|------|----------------------|
| `django` | framework — ORM, views, auth, admin | wszystkie warstwy |
| `dj-database-url` | parse DATABASE_URL → Django DB config | `config/settings.py:7,83` — tylko settings |
| `python-dotenv` | ładowanie `.env` | `config/settings.py:6,9` — tylko settings |
| `psycopg` | PostgreSQL driver | runtime — nie importowany wprost w kodzie domenowym |
| `whitenoise` | static files middleware | `config/settings.py:50` — tylko settings |
| `gunicorn` | WSGI server | CLI — nie importowany w kodzie |

**Deklaracja z tech-stack.md:** *"The leaderboard (FR-005) and session scoring (FR-004) map cleanly to Django's ORM aggregation and queryset API."* — tech-stack.md nie deklaruje wymienialności komponentów; brak explicite "will be swappable".

**Struktura bounded contexts (zidentyfikowane w domain-distillation):**

| Kontekst | Katalog | Rola |
|----------|---------|------|
| `flashcards` | `flashcards/` | Domena — karty, tematy, sesja nauki, oceny |
| `stats` | `stats/` | Analityka — agregacje, statystyki, leaderboard |
| `config` | `config/` | Routing + konfiguracja infrastruktury |

---

## KROK 1 — Identyfikacja przeciekających zależności

### LEAK-1: `flashcards.models.CardReview` przecieka do bounded context `stats`

**Wszystkie pliki znające `CardReview`:**

| Plik | Linia | Typ użycia | Oczekiwany? |
|------|-------|-----------|-------------|
| `flashcards/models.py` | 37 | definicja | ✅ — własna domena |
| `flashcards/admin.py` | 2 | rejestracja w panelu | ✅ — własna domena |
| `flashcards/views.py` | 13, 179 | import + `CardReview.objects.create()` | ✅ — własna domena |
| `flashcards/management/commands/verify_manual_checks.py` | 15, 66-68, 104, 134 | import + creates | ✅ — własna domena |
| **`stats/services.py`** | **7** | **import CardReview z obcej domeny** | ❌ — przeciek |
| **`stats/services.py`** | **22, 32, 59** | **`CardReview.objects.filter(...)` — bezpośrednie ORM queries** | ❌ — przeciek |
| **`stats/tests.py`** | **7** | **import CardReview z obcej domeny** | ❌ — przeciek |
| **`stats/tests.py`** | **20-24, 126, 176** | **`CardReview.objects.create(...)` — bezpośrednie creates** | ❌ — przeciek |

**Pola `CardReview` wprost używane w `stats/services.py`:**

```python
# stats/services.py:22  — field: reviewed_at, user
today_qs = CardReview.objects.filter(user=user, reviewed_at__date=today)

# stats/services.py:26  — field: is_correct
correct_count = today_qs.filter(is_correct=True).count()

# stats/services.py:32-34  — fields: user, reviewed_at
CardReview.objects.filter(user=user).order_by('-reviewed_at').values_list('reviewed_at', flat=True)

# stats/services.py:59  — fields: user, reviewed_at
CardReview.objects.filter(user=user).dates('reviewed_at', 'day')

# stats/services.py:14-16  — related_name: card_reviews, field: is_correct
Count('card_reviews', filter=Q(card_reviews__is_correct=True))
```

**Suma:** `stats` zna 4 pola wewnętrzne `CardReview` (`user`, `reviewed_at`, `is_correct`, `related_name='card_reviews'`) i 2 rodzaje ORM query patterns (filter+count, dates).

---

### LEAK-2: Logika biznesowa w warstwie routingu (`config/urls.py`)

**Pliki:**

| Plik | Linia | Co przecieka |
|------|-------|-------------|
| `config/urls.py` | 17-22 | `from django.contrib.auth.forms import UserCreationForm` — form domenowy w routingu |
| `config/urls.py` | 23 | `from django.contrib.auth import login` — wywołanie auth w routingu |
| `config/urls.py` | 24-30 | `class RegisterView(CreateView)` z `form_valid` → `login()` + `redirect('flashcards:topics')` — logika post-rejestracji w warstwie konfiguracyjnej |
| `config/urls.py` | 32-37 | `class HomeView.dispatch` → `redirect('flashcards:topics')` — logika nawigacji w routingu |

---

### LEAK-3: `django.db.models.Count, Q` w warstwie serwisów

`stats/services.py:4` — `from django.db.models import Count, Q`. Używane bezpośrednio w `get_leaderboard()` (line 15). To jest ORM aggregation API przekrojowo z logiką serwisową — mniejszy problem niż LEAK-1 (Django ORM w serwisach to konwencja Django), ale wzmacnia coupling.

---

## KROK 2 — Klasyfikacja i wybór #1

| Leak | (a) Liczba warstw/plików | (b) Koszt wymiany dziś | (c) Rozjazd intencja-vs-kod |
|------|--------------------------|----------------------|---------------------------|
| **LEAK-1: `CardReview` w `stats`** | 2 pliki w obcym bounded context (`services.py`, `tests.py`); 4 pola schematu; 5 query patterns | **WYSOKI** — zmiana `CardReview` schema (np. `is_correct → score: int`) wymaga zmiany `stats/services.py`, `stats/tests.py` i wszystkich consumers; brak sygnału typecheckera | Tech-stack.md nie deklaruje wymienialności, ale `artifact-2-structure.md` (context/map) zidentyfikował to jako jedyne cross-app sprzężenie i strefę ryzyka #2. `repo-map.md` wprost: *"zmiana schematu CardReview ma ukryty blast radius w stats bez sygnału typecheckera"* |
| LEAK-2: logika w `config/urls.py` | 1 plik (`config/urls.py`), 2 klasy | NISKI — move to `flashcards/views.py` | `artifact-2-structure.md`: "naruszenie granicy warstw" (strefa ryzyka #4) |
| LEAK-3: ORM w services | Konwencja Django — akceptowalny | N/A | Brak dokumentu deklarującego wymienialność |

**Wybór #1: LEAK-1 — `flashcards.models.CardReview` przeciekający do bounded context `stats`.**

**Uzasadnienie:** Największa liczba dotknięć (4 pola, 5 query patterns, 2 pliki w obcej domenie). Koszt wymiany dziś jest najwyższy spośród wszystkich leaków — zmiana dowolnego pola `CardReview` wymaga edycji `stats/` bez ostrzeżenia kompilatora. `context/map/repo-map.md` (artifact-2) wprost identyfikuje to jako ukryty blast radius i strefę ryzyka #2. Brak ACL tu = brak granicy między bounded contexts w modelu domenowym.

---

## KROK 3 — Diagnoza LEAK-1

### Mapa przecieku

```
flashcards/ (bounded context)        stats/ (bounded context)
────────────────────────────         ──────────────────────────────
models.py:37                         services.py:7
  class CardReview:           ──────▶  from flashcards.models import CardReview
    user FK                           services.py:22
    reviewed_at DateTimeField  ──────▶  CardReview.objects.filter(user=user, reviewed_at__date=today)
    is_correct BooleanField    ──────▶  today_qs.filter(is_correct=True).count()
    related_name='card_reviews'──────▶  Count('card_reviews', filter=Q(card_reviews__is_correct=True))

                                      tests.py:7
                               ──────▶  from flashcards.models import CardReview
                                      tests.py:20-24, 126, 176
                               ──────▶  CardReview.objects.create(...)
```

### Gdzie reguła granicy nie jest dotrzymana

**`stats/services.py:7`** — bezpośredni import modelu ORM z obcej domeny:
```python
from flashcards.models import CardReview   # ← stats zna persistence model flashcards
```

**`stats/services.py:22`** — `stats` zna nazwę pola `reviewed_at` i jego typ:
```python
today_qs = CardReview.objects.filter(user=user, reviewed_at__date=today)
```

**`stats/services.py:15`** — `stats` zna `related_name='card_reviews'` ustawiony w modelu `flashcards`:
```python
Count('card_reviews', filter=Q(card_reviews__is_correct=True))
```
Jeśli `related_name` w `CardReview` zostanie zmienione (np. `reviews`), `get_leaderboard()` rzuca `FieldError` bez żadnej kompilacyjnej wskazówki.

**`stats/tests.py:7, 20-24, 126, 176`** — testy `stats` tworzą bezpośrednio obiekty ORM `flashcards`:
```python
from flashcards.models import CardReview   # ← test stats zależy od schematu flashcards
CardReview.objects.create(user=user, reviewed_at=..., is_correct=True)
```
Zmiana schematu `CardReview` psuje testy `stats` — brak izolacji między bounded contexts.

### Scenariusz naruszenia

```
Zmiana: is_correct: BooleanField → outcome: CharField('correct'|'incorrect'|'skip')

Pliki które się łamią NATYCHMIASTOWO:
  flashcards/models.py         ← zmiana definicji (oczekiwana)
  flashcards/views.py          ← zmiana logiki oceniania (oczekiwana)

Pliki które się łamią CICHO (bez błędu importu):
  stats/services.py:26         ← .filter(is_correct=True) → zwróci 0 zamiast błędu
  stats/services.py:15         ← Q(card_reviews__is_correct=True) → idem
  stats/tests.py:20            ← CardReview.objects.create(is_correct=True) → TypeError w runtime
  
Sygnał: BRAK (żaden import nie failuje; błąd pojawia się tylko w runtime lub w testach)
```

---

## KROK 4 — Projekt ACL

### Value Object: `ReviewRecord` (domaine stats)

```python
# stats/domain/review_record.py — nowe

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class ReviewRecord:
    """Domenowy value object dla stats — jedyne co stats wie o ocenie karty.
    NIE zna CardReview, NIE zna ORM, NIE zna pól flashcards."""
    user_id: int
    reviewed_at: datetime
    is_correct: bool        # semantyczny bool — ACL tłumaczy cokolwiek ma flashcards

    @property
    def reviewed_date(self) -> date:
        return self.reviewed_at.date()
```

### Port (interfejs domenowy)

```python
# stats/ports/review_port.py — nowe

from abc import ABC, abstractmethod
from datetime import date


class ReviewPort(ABC):
    """Wąski port — jedyne co stats/services.py potrzebuje od danych ocen."""

    @abstractmethod
    def get_today_reviews(self, user_id: int, today: date) -> list['ReviewRecord']:
        """Wszystkie oceny użytkownika z dnia today."""
        ...

    @abstractmethod
    def get_last_review_date(self, user_id: int) -> date | None:
        """Data ostatniej oceny. None jeśli nigdy nie oceniał."""
        ...

    @abstractmethod
    def get_reviewed_dates(self, user_id: int) -> set[date]:
        """Zbiór dat (bez czasu) wszystkich ocen — do obliczenia streak."""
        ...

    @abstractmethod
    def get_total_correct_by_user(self) -> list[tuple[int, int]]:
        """[(user_id, total_correct), ...] — do leaderboardu."""
        ...
```

### Adapter (ACL — jedyne miejsce znajomości CardReview)

```python
# stats/adapters/flashcards_review.py — nowe

from datetime import date

from django.contrib.auth import get_user_model

from flashcards.models import CardReview          # ← JEDYNE miejsce importu w stats/
from stats.ports.review_port import ReviewPort
from stats.domain.review_record import ReviewRecord


class FlashcardsReviewAdapter(ReviewPort):
    """ACL: tłumaczy CardReview (ORM flashcards) → ReviewRecord (domena stats)."""

    def get_today_reviews(self, user_id: int, today: date) -> list[ReviewRecord]:
        qs = CardReview.objects.filter(user_id=user_id, reviewed_at__date=today)
        return [ReviewRecord(user_id=r.user_id, reviewed_at=r.reviewed_at,
                             is_correct=r.is_correct) for r in qs]

    def get_last_review_date(self, user_id: int) -> date | None:
        last = (CardReview.objects.filter(user_id=user_id)
                .order_by('-reviewed_at')
                .values_list('reviewed_at', flat=True)
                .first())
        return last.date() if last else None

    def get_reviewed_dates(self, user_id: int) -> set[date]:
        return set(CardReview.objects.filter(user_id=user_id)
                   .dates('reviewed_at', 'day'))

    def get_total_correct_by_user(self) -> list[tuple[int, int]]:
        from django.db.models import Count, Q
        User = get_user_model()
        rows = User.objects.annotate(
            total_correct=Count('card_reviews', filter=Q(card_reviews__is_correct=True))
        ).order_by('-total_correct', 'username').values_list('id', 'total_correct')[:10]
        return list(rows)
```

### Serwis po refaktorze (zna tylko port)

```python
# stats/services.py — AFTER (pseudokod sygnatur)

from stats.ports.review_port import ReviewPort
from stats.types import StudyStats


def compute_study_stats(user, *, reviews: ReviewPort) -> StudyStats:
    """reviews jest wstrzykiwany — services.py nie wie co go implementuje."""
    today = ...
    today_records = reviews.get_today_reviews(user.pk, today)
    correct_count = sum(1 for r in today_records if r.is_correct)
    ...

def get_leaderboard(*, reviews: ReviewPort) -> list:
    return reviews.get_total_correct_by_user()
```

### Wstrzykiwanie adaptera — cienki widok

```python
# stats/views.py — AFTER

from stats.adapters.flashcards_review import FlashcardsReviewAdapter

_REVIEWS = FlashcardsReviewAdapter()    # singleton — adapter jest bezstanowy

class StatsDashboardView(LoginRequiredMixin, TemplateView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['stats'] = compute_study_stats(self.request.user, reviews=_REVIEWS)
        return ctx
```

---

## KROK 5 — Dowód izolacji + Before/After

### Dowód: wymiana implementacji dotyka TYLKO adaptera

Jeśli `CardReview` zmienia `is_correct: bool` → `outcome: str`:

| Plik | BEFORE (dziś) | AFTER (po ACL) |
|------|--------------|----------------|
| `flashcards/models.py` | zmiana pola | zmiana pola (oczekiwana) |
| `flashcards/views.py` | zmiana logiki | zmiana logiki (oczekiwana) |
| **`stats/adapters/flashcards_review.py`** | — (nie istnieje) | **JEDYNA zmiana w stats**: `is_correct=r.is_correct` → `is_correct=(r.outcome == 'correct')` |
| `stats/services.py` | `is_correct=True` w query → cichy błąd | BEZ ZMIAN — operuje na `ReviewRecord.is_correct: bool` |
| `stats/tests.py` | `CardReview.objects.create(is_correct=True)` → TypeError | BEZ ZMIAN — testuje port z test-double, bez CardReview |
| `stats/views.py` | BEZ ZMIAN | BEZ ZMIAN |
| `stats/types.py` | BEZ ZMIAN | BEZ ZMIAN |

### Before/After dla każdego miejsca reguły

**`stats/services.py:7`**
```python
# BEFORE
from flashcards.models import CardReview

# AFTER
from stats.ports.review_port import ReviewPort  # ← port, nie implementacja
```

**`stats/services.py:22`**
```python
# BEFORE
today_qs = CardReview.objects.filter(user=user, reviewed_at__date=today)
correct_count = today_qs.filter(is_correct=True).count()

# AFTER
today_records = reviews.get_today_reviews(user.pk, today)
correct_count = sum(1 for r in today_records if r.is_correct)
```

**`stats/services.py:14-16`**
```python
# BEFORE
User.objects.annotate(
    total_correct=Count('card_reviews', filter=Q(card_reviews__is_correct=True))
).order_by('-total_correct', 'username')[:10]

# AFTER
reviews.get_total_correct_by_user()   # ← semantyczna metoda, bez ORM w services
```

**`stats/tests.py`**
```python
# BEFORE
from flashcards.models import CardReview
CardReview.objects.create(user=user, reviewed_at=..., is_correct=True)

# AFTER — test-double implementujący ReviewPort
class FakeReviewPort(ReviewPort):
    def __init__(self, records): self._records = records
    def get_today_reviews(self, user_id, today): return self._records
    ...

stats = compute_study_stats(user, reviews=FakeReviewPort([
    ReviewRecord(user_id=user.pk, reviewed_at=now, is_correct=True)
]))
```

### Warstwa UI dostaje gotowe dane domenowe

```python
# stats/views.py — template context
ctx['stats'] = compute_study_stats(user, reviews=_REVIEWS)
# ctx['stats'] jest StudyStats dataclass — bez żadnego ORM obiektu
# template stats/dashboard.html: {{ stats.streak }}, {{ stats.correct_pct }}
# template NIE wie co to CardReview
```

---

## KROK 6 — Weryfikacja i plan

### Kryterium sukcesu

```bash
# Po refaktorze — grep po "CardReview" w katalogu stats/ zwraca TYLKO:
grep -rn "CardReview" stats/
# Oczekiwany wynik:
#   stats/adapters/flashcards_review.py:5:from flashcards.models import CardReview
#   stats/adapters/flashcards_review.py:16:  qs = CardReview.objects.filter(...)
#   (wszystkie inne pliki stats/ — zero wyników)
```

**Pliki znające `CardReview` DZIŚ → PO refaktorze:**

| Plik | Dziś | Po ACL |
|------|------|--------|
| `stats/services.py` | ❌ zna CardReview (import + 5 queries) | ✅ zna tylko ReviewPort |
| `stats/tests.py` | ❌ zna CardReview (import + 3 creates) | ✅ używa FakeReviewPort |
| `stats/adapters/flashcards_review.py` | nie istnieje | ✅ jedyne miejsce wiedzy |
| `stats/ports/review_port.py` | nie istnieje | ✅ kontrakt domenowy |
| `stats/domain/review_record.py` | nie istnieje | ✅ value object |

### Plan faz

**Faza 1 — Port + Value Object** *(bez zmiany zachowania)*
- Utwórz `stats/ports/review_port.py` (`ReviewPort` ABC)
- Utwórz `stats/domain/review_record.py` (`ReviewRecord` dataclass)
- Testy: brak (pure Python, no Django)

**Faza 2 — Adapter** *(test-first)*
- Utwórz `stats/adapters/flashcards_review.py` (`FlashcardsReviewAdapter`)
- Testy adaptera: integracyjne (wymagają DB) — weryfikują że adapter produkuje poprawne `ReviewRecord` dla danych `CardReview`

**Faza 3 — Przepięcie services.py** *(test-first)*
- Zrefaktoruj `compute_study_stats` i `get_leaderboard` do przyjmowania `ReviewPort`
- Testy serwisów: używają `FakeReviewPort` — eliminacja `CardReview.objects.create()` z `stats/tests.py`
- Weryfikacja: `grep "CardReview" stats/services.py` → zero wyników

**Faza 4 — Przepięcie views.py + cleanup tests**
- `StatsDashboardView` i `LeaderboardView` wstrzykują `FlashcardsReviewAdapter`
- Usuń `from flashcards.models import CardReview` z `stats/tests.py`
- Finalna weryfikacja: `grep "CardReview" stats/ -r` → tylko `stats/adapters/flashcards_review.py`

### Nowe "load-bearing" nazwy

| Nazwa | Typ | Opis |
|-------|-----|------|
| `ReviewPort` | Abstract Base Class (port) | Kontrakt między stats a źródłem danych ocen |
| `ReviewRecord` | Value Object | Domenowa reprezentacja oceny w kontekście stats |
| `FlashcardsReviewAdapter` | Adapter (ACL) | Jedyne miejsce importu CardReview w stats/ |
| `FakeReviewPort` | Test Double | In-memory implementacja ReviewPort dla testów units |

---

## Separacja dowodów

**EVIDENCE (file:line zweryfikowane):** wszystkie cytaty kodu opierają się na odczytach z tej sesji (`stats/services.py`, `stats/tests.py`, `flashcards/models.py`, `config/urls.py`, `pyproject.toml`).

**INFERENCE:** Scenariusz "is_correct → outcome" jest hipotetyczny — ilustruje koszt braku ACL; żadna taka zmiana nie jest planowana.

**LEAK-2 (config/urls.py)** — poza zakresem tego planu; odnotowany jako strefa ryzyka #4 w `context/map/repo-map.md`. Refaktor: przenieść `RegisterView` i `HomeView` do `flashcards/views.py` lub dedykowanego `accounts/views.py`.