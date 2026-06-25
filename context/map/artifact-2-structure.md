# Artifact 2 — Struktura: zależności, entry pointy, cykle, granice warstw

> Narzędzie: analiza AST Python (odpowiednik dependency-cruiser dla Django/Python).  
> Wychodzi z: `context/map/artifact-1-territory.md`.  
> Graf: `context/map/deps/app-dependency-graph.dot` (render: `dot -Tsvg app-dependency-graph.dot -o app-dependency-graph.svg`).

---

## Konfiguracja narzędzia

dependency-cruiser to narzędzie Node.js — nie ma zastosowania w projekcie Django/Python. Ekwiwalent: `ast.parse()` (stdlib) + analiza `ImportFrom`/`Import` nodes. Uruchomiono w-sesji bez instalacji zewnętrznych pakietów.

**Top 3 pytania eksploracyjne (ekwiwalent "top 3 ideas"):**
1. **Cykle importów** — czy `flashcards ↔ stats` tworzą pętlę? (najczęstszy problem przy wydzielaniu serwisów)
2. **Fan-out `views.py`** — ile modułów zewnętrznych ciągnie najgorętszy plik? (proxy testowalności)
3. **Granica warstw** — czy `stats` sięga tylko do `flashcards.models`, czy też do logiki widoków?

---

## Cykle w aktywnych obszarach

**5 kluczowych obserwacji:**
1. **Brak cykli** — graf importów to DAG. Potwierdzone pełnym przeszukaniem DFS po wszystkich plikach `.py` w `flashcards/`, `stats/`, `config/`.
2. `flashcards` nie importuje z `stats` — zależność jest jednostronna.
3. Wewnątrz `flashcards/` brak cykli między `views.py`, `models.py`, `session.py`, `forms.py`.
4. `stats/tests.py` importuje bezpośrednio z `flashcards.models` — testy nie izolują się za serwisem.
5. Management commands (`seed_cards.py`, `verify_manual_checks.py`) importują z `flashcards.models` — to akceptowalne (narzędzia adminowe, nie logika biznesowa).

| Obszar | Co znalazłem | Dowód (AST) | Dlaczego ważne | Związek z artifact-1 | Co sprawdzić dalej |
|--------|-------------|-------------|----------------|----------------------|-------------------|
| `flashcards/` | Brak cykli wewnętrznych | DFS: 0 cykli | Refaktoring wewnętrzny jest bezpieczny | Najaktywniejszy obszar (45 commitów) | Monitorować przy wydzielaniu serwisów z `views.py` |
| `stats/ → flashcards` | Jedyne cross-app sprzężenie: `stats.services → flashcards.models.CardReview` | `stats/services.py:7` | Zmiana `CardReview` łamie `stats` bez sygnału typecheckera | `stats` (17 commitów) zmienia się rzadziej | Czy `CardReview` ma stabilne API? Sprawdź migracje. |
| `stats/tests.py` | Importuje `flashcards.models` bezpośrednio (nie przez serwis) | `stats/tests.py:3` | Testy `stats` są sprzężone z modelem `flashcards` | `stats/tests.py` — 7 importów, 35 testów | Rozważyć fixtures lub factory zamiast bezpośredniego importu |

---

## Granice warstw

**Oczekiwana architektura:**
```
config/          ← warswa konfiguracji / routing
flashcards/      ← warstwa domenowa (modele, logika sesji, CRUD)
stats/           ← warstwa analityczna (tylko czyta z flashcards)
```

**5 kluczowych obserwacji:**
1. `stats` respektuje granicę — importuje wyłącznie `flashcards.models`, nie `flashcards.views` ani `flashcards.session`.
2. `config/urls.py` zawiera logikę biznesową (`HomeView.dispatch` redirect) — naruszenie warstwy konfiguracji.
3. `flashcards/views.py` jest monolitem — CRUD, logika sesji i guard clauses w jednym pliku (201 linii, 7 klas, 10 funkcji).
4. `templates/base.html` to ukryty hub cross-cutting — 5 commitów, zmienia się z każdą nawigacyjną feature.
5. `stats/models.py` — pusty (2 linie). `stats` nie ma własnego modelu domenowego; całkowicie zależy od `flashcards`.

| Sprawdzana granica | Wynik | Dowód | Dlaczego ważne | Związek z artifact-1 | Co sprawdzić dalej |
|-------------------|-------|-------|----------------|----------------------|-------------------|
| `stats` → tylko modele, nie widoki `flashcards` | ✅ PASS | `stats/services.py`: `from flashcards.models import CardReview` | Granica respektowana | `stats` zmienia się rzadziej niż `flashcards` | Utrzymywać przy dodawaniu nowych serwisów |
| `config/urls.py` jako czysta konfiguracja | ⚠️ PARTIAL | `config/urls.py:34,40`: redirect logic w `HomeView.dispatch` i `RegisterView.form_valid` | Logika biznesowa przecieka do routingu | `config/` — 8 commitów | Przenieść redirect do middleware lub `flashcards/views.py` |
| `flashcards/views.py` jako cienka warstwa | ❌ FAIL | 201 linii, 7 klas, 10 funkcji, 13 importów | God View — każda feature ląduje tutaj | Najczęściej zmieniany plik (15 commitów) | Wydzielić `session_logic.py` i `card_crud.py` |

---

## Ryzyka testowalności

### Podsumowanie

Projekt ma 87 testów (52 w `flashcards/tests.py`, 35 w `stats/tests.py`). Pokrycie jest integracyjne (Django test client) — żadnych unit testów w izolacji. `views.py` jako God View jest najtrudniejszy do testowania selektywnie.

### Lista ryzyk testowych

| Moduł | Ryzyko | Typ testu który zadziała |
|-------|--------|--------------------------|
| `flashcards/views.py` | 13 importów, 7 klas, 10 funkcji — każdy test wymaga pełnego Django stacku | integracyjny (obecny) |
| `stats/services.py → flashcards.models` | Serwis nie może być testowany bez bazy `flashcards` | integracyjny z fixtures |
| `stats/tests.py` | Bezpośredni import `flashcards.models` — testy `stats` zepsują się przy rename w `flashcards` | integracyjny; rozważyć factory |
| `config/urls.py` (redirect logic) | Logika w `dispatch()` testowana tylko przez pełny request cycle | e2e / integracyjny |
| `flashcards/session.py` | SK constants — prosta klasa, łatwo testowalny w izolacji | ✅ unit test możliwy |

### Najbardziej podejrzane moduły

1. **`flashcards/views.py`** (13 importów, 201 linii) — każda zmiana może nieoczekiwanie dotknąć 3-4 widoków. Test suite ma 52 testy ale wszystkie przechodzą przez pełny HTTP cycle.
2. **`stats/services.py`** (6 importów, zależność od zewnętrznego modelu) — zmiana `CardReview.reviewed_at` lub `is_correct` łamie `compute_study_stats` bez sygnału typecheckera.
3. **`stats/tests.py`** — 35 testów importuje bezpośrednio `flashcards.models`; refaktor modelu `flashcards` wymaga aktualizacji testów `stats`.

### Co sprawdzić dalej

- Czy `CardReview` ma stabilne pola? Sprawdź migracje: `flashcards/migrations/`.
- Czy `session.py` (SK constants) ma własne testy? (Powinien — to kontrakt shared przez 3 widoki.)
- Kandydat do unit testów: `stats/services.py:compute_study_stats` — czysta funkcja, da się przetestować z mock queryset.

### Opcjonalny kolejny krok: graf

Plik DOT wygenerowany: `context/map/deps/app-dependency-graph.dot`

Render lokalnie (po instalacji graphviz):
```bash
dot -Tsvg context/map/deps/app-dependency-graph.dot -o context/map/deps/app-dependency-graph.svg
```

Lub wklej zawartość `.dot` na: https://dreampuf.github.io/GraphvizOnline/