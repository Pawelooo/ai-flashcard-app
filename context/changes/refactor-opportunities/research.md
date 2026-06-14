---
date: 2026-06-14T00:00:00+02:00
researcher: Claude Sonnet 4.6
git_commit: a214c2a6509b85a584f04b209eeb0f642f5e0fe3
branch: master
repository: naukaAI
topic: "Refactor opportunities — techniczny dług z analizy session flow"
tags: [research, refactor, session-management, cross-app, technical-debt, flashcards]
status: complete
last_updated: 2026-06-14
last_updated_by: Claude Sonnet 4.6
---

# Research: Refactor opportunities — session flow

**Date**: 2026-06-14  
**Git Commit**: a214c2a6509b85a584f04b209eeb0f642f5e0fe3  
**Branch**: master  
**Repository**: naukaAI

## Research Question

Które problemy zidentyfikowane w `context/changes/complete-study-session/research.md`
(dług techniczny TD-1 – TD-5) warto naprawić, w jakim docelowym kształcie i w jakiej
kolejności? Eksploracja — bez zmian w kodzie, bez projektu docelowej architektury
poza nazwaniem kształtu per kandydat.

---

## Priory

Źródłowy raport: `context/changes/complete-study-session/research.md`
(stan na commit `a214c2a`, ast-grep zweryfikowany).
Repo-map: `context/map/repo-map.md`.

---

## Klasyfikacja kandydatów (do audytu)

### KANDYDACI (zmieniają strukturę kodu)

| ID | Opis | Źródło w raporcie |
|----|------|-------------------|
| K1 | Session key string literals — 21 subskryptów w `views.py`, bez warstwy typów | TD-3 |
| K2 | Cross-app import `stats/services.py → flashcards.models.CardReview` | TD-2 |
| K3 | Dual state: `session_score` (in-memory) vs `CardReview.is_correct` (DB) | TD-1 |

### NIE-KANDYDACI (testy, dokumentacja, UX — wejście do oceny kosztu)

| Opis | Kategoria |
|------|-----------|
| TD-4: brak `StudySession` modelu | przeprojektowanie konceptu biznesowego — out of scope |
| TD-5: race condition przy dwóch kartach | wymaga TD-4 lub distributed locking — zależny od TD-4 |
| luki testowe E2E (spaced repetition path) | brakujące testy, nie struktura kodu |
| 9 miejsc z URL name `flashcards:topics` | coupling przez string constants — niska waga |
| card/topic deletion UX | UX gap, nie dług strukturalny |

---

## K1 — Session key string literals

### Obecny kształt

`flashcards/views.py:16-22` definiuje `_SESSION_KEYS` jako listę 5 stringów:

```python
_SESSION_KEYS = [
    'session_topic_id',
    'session_cards',
    'session_index',
    'session_score',
    'session_wrong_ids',
]
```

Lista jest używana **wyłącznie** w 2 miejscach: pętla `for key in _SESSION_KEYS` w
`TopicsListView.get()` (linie 32-33) i w `session_results()` (linie 80-81). Oba
miejsca wykonują identyczny `request.session.pop(key, None)`.

Wszystkie pozostałe dostępy do kluczy sesji to **bezpośrednie string literały**:
21 subskryptów w `views.py` rozsiane po 5 funkcjach, plus 32 string literały
w `tests.py` (setup bloków i assertionów). Łącznie ~53 punkty dostępu.

Dostępy per widok (evidence — `flashcards/views.py`):

| Widok | Operacje na sesjii | Linie |
|-------|--------------------|-------|
| `TopicsListView.get` | pop ×5 (via loop) | 32-34 |
| `session_start` | write ×5 (inline) | 50-54 |
| `session_results` | issubset check ×4, read ×4, write ×1 (`last_wrong_ids`), pop ×5 | 60-81 |
| `study_review` | pop ×1 (`last_wrong_ids`), write ×5 | 150-161 |
| `study_card` | issubset check ×4, read ×4, write ×2 | 167-193 |

Każda z 5 funkcji miesza logikę sesyjną z logiką biznesową (zapytania DB,
przetasowanie, obliczenia, render) — brak izolowanej warstwy session management. (evidence)

Jedyna typowana precedencja w projekcie: `stats/types.py:5-11`:
```python
@dataclass(frozen=True)
class StudyStats:
    today_count: int
    correct_pct: int | None
    streak: int
    last_reviewed: date | None
    next_review: date
```
Frozen dataclass (immutable) — projekt zna ten wzorzec, ale w `flashcards/` nie istnieje
żaden odpowiednik. (evidence)

### Intencjonalność

`_SESSION_KEYS` lista to **świadoma, nieukończona próba konsolidacji** — sygnał, że
autor wiedział o problemie, ale zatrzymał się na połowie drogi: lista istnieje
dla cleanup, lecz nie służy jako single-source-of-truth dla typowanych dostępów. (inference)

Rozproszony string-literal pattern jest **accidental complexity** — brak decyzji
projektowej, która tłumaczyłaby dlaczego dostępy mają być literałami zamiast
referencjami do stałej lub atrybutów obiektu.

Werdykt: **accidental complexity**.

### Wykonalność

- Brak CI/CD (`.github/` pusty) — jedyna sieć bezpieczeństwa to Django test suite
- Blast radius: 5 widoków w jednym pliku, 13 metod testowych (~60 linii testów)
- Zero ryzyka cross-app (sesja jest wewnętrzna, nigdy nie trafia do klienta)
- Brak migracji DB
- Existing scaffold: `_SESSION_KEYS` to gotowy trzon pod `TypedDict` lub `dataclass`
- Pierwszym krokiem prerekewizytem: `flashcards/session_types.py` z definicją
  `SessionState` (TypedDict lub dataclass); następnie refactor widoków i testów
- Wszystkie 53 punkty dostępu można zaktualizować mechanicznie bez zmiany logiki

---

## K2 — Cross-app import `stats → flashcards`

### Obecny kształt

Jedyne przekroczenie granicy między appkami w kodzie produkcyjnym:
`stats/services.py:7` — `from flashcards.models import CardReview`

Użycia w `stats/services.py`:
- linia 22: `CardReview.objects.filter(user=user, reviewed_at__date=today)` (compute_study_stats)
- linia 32: `CardReview.objects.filter(user=user)` (compute_study_stats)
- linia 59: `CardReview.objects.filter(user=user).dates()` (_compute_streak)
- linie 14-16: `Count('card_reviews', ...)` przez related name (nie wymaga importu, ale zakłada schemat)

`stats/tests.py:5` importuje `CardReview` do `_add_review()` helpera używanego przez
22 z 27 metod testowych (81% stats tests). (evidence)

Kierunek zależności: `stats → flashcards` — jednostronny, poprawny.
`flashcards` nie importuje z `stats` nigdzie w kodzie produkcyjnym. (evidence — pydeps)

### Intencjonalność

Import istniał od **pierwszego commita scaffoldu** `stats/services.py`
(commit `5da449185e5dd6e944f67a549f9a9604a6b4e337`, maj 2026). Nie ma commita,
który by ten import dodał jako refactoring lub workaround — to baseline design. (evidence)

Plan `context/changes/leaderboard/plan.md §Current State Analysis:9` traktuje
`CardReview` jako fakt kontekstu, nie problem do rozwiązania: *"CardReview model
has user FK + is_correct (boolean). A single annotated query yields all user totals."*
(evidence)

Wzorzec `stats reads flashcards data` jest semantycznie koherentny: stats jest
**read app** (agreguje), flashcards jest **write app** (tworzy CardReview).
Kierunek zależności jest poprawny. (inference)

Werdykt: **deliberate constraint** (decyzja nośna od dnia 1).

### Wykonalność

- Blast radius: 2 moduły (`services.py`, `tests.py`), 22 z 27 metod testowych
- Abstrakcja wymagana: Protocol lub Repository layer — żaden z tych wzorców
  nie istnieje w projekcie; byłoby to pierwsze wprowadzenie
- Korzyść: izolacja `stats` od zmian schematu `CardReview` — ale schemat był
  stabilny przez cały czas istnienia projektu (3 zmiany modelu w historii gita)
- Koszt: nowa abstrakcja (Protocol z querysetem Django to niebanalinny typ),
  przebudowa testów stats

---

## K3 — Dual state: `session_score` vs `CardReview`

### Obecny kształt

`session_score` to licznik poprawnych odpowiedzi przechowywany w sesji Django:
- init: `session_start()` linia 53 — `request.session['session_score'] = 0`
- increment: `study_card()` linia 187 — `request.session['session_score'] += 1`
- read: `session_results()` linia 64 — `score = request.session['session_score']`

`session_score` jest elementem `required` guard w `study_card()` (linia 167):
```python
required = {'session_cards', 'session_index', 'session_score', 'session_wrong_ids'}
if not required.issubset(request.session.keys()):
    return redirect('flashcards:topics')
```

Wartość `session_score` jest niezależnie testowana względem DB w
`test_session_score_matches_cardreview_db` (`flashcards/tests.py:308-326`):
```python
self.assertEqual(response.context['score'], 2)           # z sesji
self.assertEqual(CardReview.objects.filter(is_correct=True).count(), 2)  # z DB
```
Istnienie tego testu potwierdza świadomość dwóch niezależnych reprezentacji. (evidence)

**Czy score jest wyprowadzalny?** Tak — matematycznie:

```python
score = len(session_cards) - len(session_wrong_ids)
```

Brak duplikatów w `session_wrong_ids` jest gwarantowany przez architekturę:
cross-card guard (`views.py:180-181`) wymusza `card_id == card_ids[index]`,
więc każda karta może być odpowiedziana co najwyżej raz per sesja. (evidence — inference)

Sześć metod testowych dotyka `session_score` bezpośrednio lub przez setup:
`test_missing_is_correct_field_counts_as_incorrect` (linia 342),
`test_cross_card_post_rejected_no_db_write` (linia 355),
plus 4 setup bloki. (evidence)

### Intencjonalność

`session_score` pojawił się w commit `fbaec0d` (P2, 27 maja), 9 minut przed
pierwszym renderem wyników (P3, commit `8539c1a`). Nie ma uzasadnienia
w komunikacie commita. (evidence)

Plan `complete-study-session/plan.md §Critical Implementation Details` wymienia
`session_score` jako jeden z 5 wymaganych kluczy z adnotacją `running count of
correct answers`. (evidence)

Hardening plan `testing-score-accuracy-session-hardening` w §Phase 3 celowo
włączył `session_score` do `required` setu i dodał test weryfikujący redirect
przy brakującym kluczu (`test_partial_session_missing_score_post_gets_redirect_not_500`). (evidence)

Argumenty za intencjonalnością są **słabe**:
1. *Running display counter* — brak UI pokazującego score w trakcie sesji (tylko na ekranie wyników)
2. *Resilience* — przy uszkodzeniu `session_wrong_ids` niezależny `session_score` nie ratuje UX; oba muszą być spójne
3. *Explicit contract* — to opis faktu, nie uzasadnienie dla duplikacji

Kontr-argument najsilniejszy: test `test_session_score_matches_cardreview_db`
weryfikuje zgodność dwóch reprezentacji — to klasyczny symptom dual-state problem. (inference)

Werdykt: **genuinely uncertain** — session_score z P2 był convenience variable;
hardening faza uczyniła go load-bearing przez guard. Granica między "tak miało być"
a "tak się skończyło" nie jest jasna z archeologii gita.

### Wykonalność

- Blast radius: 3 widoki (`session_start`, `study_card`, `session_results`),
  6 metod testowych (~40 linii testów)
- Brak migracji DB, brak ryzyka cross-app
- **Uwaga**: usunięcie session_score wymaga aktualizacji `required` guard w
  `study_card()` (linia 167) — to nie tylko uproszczenie, to zmiana semantyki guardu.
  Test `test_partial_session_missing_score_post_gets_redirect_not_500` stałby się
  nieważny (missing session_score nie byłoby już błędem); trzeba go przepisać
  lub usunąć.
- Pierwszy krok prerekewizytu: modyfikacja `session_results()` — compute inline
  zamiast read; następnie usunięcie z init/increment/guard i update testów

---

## Refactor Opportunities (ranking)

### #1 — K1: Session key string literals → typed session wrapper

**Obecny kształt**: 21 string subscripts w `views.py` + 32 w `tests.py` = ~53 punkty
dostępu; `_SESSION_KEYS` lista tylko dla cleanup; zero typowania.

**Docelowy kształt**: `flashcards/session_types.py` z `SessionState` (TypedDict
lub dataclass z atrybutami odpowiadającymi 5 kluczom) + session helper functions
(`get_session()`, `set_session()`) w tym samym pliku. Widoki operują na obiekcie
zamiast na string dict. Testy używają helpera do setup zamiast ręcznych dictów.

**Dlaczego to miejsce #1:**
- Koszt długu jest wysoki i rośnie: każdy nowy test, który konfiguruje stan sesji,
  musi znać wszystkie nazwy kluczy jako stringi; literówka w teście = fałszywy pass
- Koszt zmiany jest niski: zero ryzyka cross-app, zero migracji, scaffold już istnieje
- Ratio koszt-długu do kosztu-zmiany: najlepszy ze wszystkich trzech kandydatów
- Zmiana jest w pełni mechaniczna i odwracalna

**Blast radius**: `flashcards/views.py` (jeden plik, 5 widoków), `flashcards/tests.py`
(13 metod, ~60 linii). Zero modułów cross-app.

**Inkrementalna ścieżka**:
1. Dodaj `flashcards/session_types.py` z `SessionState` TypedDict i 2-3 helperami
2. Zastąp string literały w `session_start()` i `TopicsListView` (najłatwiejsze widoki)
3. Zastąp kolejno `session_results()`, `study_review()`, `study_card()`
4. Zaktualizuj testy — setup bloki i assertiony

Każdy krok jest osobnym, self-contained commitem. Testy weryfikują poprawność
po każdym kroku.

**Pierwszy krok prerekewizytu**: napisz `flashcards/session_types.py` z TypedDict
i jednym helperem `get_session(request) -> SessionState`. Brak zmian w istniejącym kodzie.

---

### #2 — K3: Dual state `session_score` → derived at render time

**Obecny kształt**: `session_score` inicjalizowany w `session_start()`, inkrementowany
w `study_card()`, odczytywany w `session_results()`. Wartość wyprowadzalna jako
`total - len(wrong_ids)` — gdzie `total = len(session_cards)`.

**Docelowy kształt**: `session_results()` oblicza score inline:
`score = total - len(request.session['session_wrong_ids'])`.
`session_score` usunięty z 4 miejsc w kodzie (init, increment, guard, read)
i z `_SESSION_KEYS` listy. 4 klucze sesji zamiast 5.

**Dlaczego to miejsce #2:**
- Eliminuje invariant który testy muszą weryfikować (test_session_score_matches_cardreview_db)
- Mniejszy blast radius niż K1 (~40 linii vs ~60 linii)
- Ale: intencjonalność jest genuinely uncertain; hardening faza uczyniła session_score
  load-bearing; `required` guard i jego test wymagają przepisania (nie tylko usunięcia)
- K1 jest czytelniejszy w ROI — K3 przynosi mniejszą korzyść długoterminową
  (o jeden mniej invariant) przy realnym ryzyku przeoczenia semantyki guardu

**Blast radius**: `flashcards/views.py` (3 widoki: `session_start`, `study_card`,
`session_results`), `flashcards/tests.py` (6 metod, ~40 linii).

**Inkrementalna ścieżka**:
1. Zmodyfikuj `session_results()`: dodaj `score = total - len(wrong_ids)` zamiast
   czytać z sesji; upewnij się że oba wyniki są identyczne (testy powinny przejść)
2. Usuń `session_score` z `session_start()` i `study_card()` increment
3. Usuń z `required` set w `study_card()` i z `_SESSION_KEYS`
4. Przepisz `test_partial_session_missing_score_post_gets_redirect_not_500` — zmień
   co testuje (guard na pozostałe 3 klucze, nie session_score)

**Pierwszy krok prerekewizytu**: zmodyfikuj tylko `session_results()` (jeden plik,
jedna linia), uruchom testy — wszystkie powinny przejść bez innych zmian.
Reszta kroków jest bezpieczna dopiero po tym potwierdzeniu.

**Uwaga**: K3 można wziąć przed K1 lub po K1; nie ma zależności między nimi.
Jeśli K1 jest zrealizowane najpierw, K3 będzie prostszy (mniejsza liczba
punktów dostępu do update po usunięciu session_score z TypedDict).

---

## Kandydaci rozważeni i odrzuceni

### K2 — Cross-app import `stats → flashcards` — **ODRZUCONY**

Werdykt intencjonalności: deliberate constraint. Kierunek zależności jest
semantycznie poprawny (stats czyta dane flashcards, nie odwrotnie). Import istnieje
od scaffoldu — nie ma commita dodającego go jako workaround lub quick fix.

Koszt długu: niski. Schemat `CardReview` był stabilny przez całą historię projektu.
Zmiana schematu propaguje się przez pydeps-widoczny import, nie przez ukrytą magię.

Koszt zmiany: wysoki. Protocol lub Repository layer — wzorzec nieobecny w projekcie,
22 z 27 metod testowych musiałoby być przebudowanych.

Proporcja kosztu: negatywna. Więcej do stracenia niż zyskania przy obecnej stabilności schematu.

Decyzja: jeśli `CardReview` schemat zacznie się zmieniać często i powodować
cascade w `stats/`, warto wrócić do K2. Teraz — defer.

### TD-4 / TD-5 — Brak `StudySession` modelu + race condition — **ODRZUCONE**

TD-4 był dokumentowany w `complete-study-session/plan.md §What We're NOT Doing`
jako świadoma decyzja MVP. Race condition przy dwóch kartach (TD-5) wymaga TD-4
lub distributed locking — to przeprojektowanie konceptu biznesowego, nie refaktor struktury kodu.
Zatrzymuję się tu zgodnie z boundary z instrukcji badania.

---

## Otwarte pytania

1. **TypedDict vs frozen dataclass dla K1**: TypedDict jest mutowalny (sessions są mutowalne z natury),
   frozen dataclass jest immutable. Sesja Django jest z definicji mutowalnym słownikiem.
   TypedDict lepiej oddaje naturę sesji; dataclass wymagałby rebuildu obiektu przy każdej mutacji.
   Decyzja należy do etapu planowania.

2. **K3 guard semantics**: Po usunięciu `session_score` z `required` setu, guard w `study_card()`
   chroni 3 klucze zamiast 4. Czy to wystarczy? Test `test_partial_session_missing_index_gets_redirect_not_500`
   (pozostaje) dowodzi że guard na `session_index` jest kluczowy — `session_score` był
   defensywnym dodatkiem. Weryfikacja po kroku 1 (modification of session_results only)
   powinna odpowiedzieć.

3. **Session persistence**: Django session backend to domyślnie DB (`django.contrib.sessions.backends.db`).
   Typed wrapper nie zmienia backend, ale testy integracyjne (`self.client.session`)
   muszą nadal działać z Django test client session API. To nie jest blocker —
   tylko punkt do weryfikacji przy setup K1.

---

## Powiązane artefakty

- `context/changes/complete-study-session/research.md` — źródłowy raport z TD-1 – TD-5
- `context/map/repo-map.md` — graf importów i strefy ryzyka
- `flashcards/views.py` — epicentrum K1/K3
- `stats/services.py:7` — punkt K2
- `stats/types.py:5-11` — jedyna typowana precedencja w projekcie
