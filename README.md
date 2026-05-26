# ⚡ NaukaAI

Interaktywna aplikacja do nauki AI/ML przez fiszki — stworzona dla developerów przygotowujących się do rozmów rekrutacyjnych.

🌐 **Live:** [naukaai.fly.dev](https://naukaai.fly.dev)

---

## Co to jest?

NaukaAI to webowa aplikacja flashcard skupiona na pojęciach z uczenia maszynowego i sztucznej inteligencji. Zamiast przeszukiwać dokumentacje, kursy i papery, masz jedno miejsce z ustrukturyzowanymi pytaniami i odpowiedziami — takimi, jakich faktycznie pytają rekruterzy.

**Jak działa sesja nauki:**
1. Widzisz pytanie (np. *"Co to jest backpropagation?"*)
2. Klikasz „Pokaż odpowiedź"
3. Oceniasz siebie — „Wiedziałem" lub „Nie wiedziałem"
4. Aplikacja zapisuje wynik i pokazuje kolejną losową fiszkę

Każda sesja zajmuje mniej niż 5 minut. Statystyki (seria dni, procent poprawnych) motywują do codziennej nauki.

---

## Funkcje

| Funkcja | Status |
|---|---|
| Rejestracja i logowanie | ✅ |
| Sesja nauki z fiszkami | ✅ |
| Samodzielna ocena (wiedziałem / nie wiedziałem) | ✅ |
| Zapis historii powtórek | ✅ |
| Statystyki: seria dni, % poprawnych | ✅ |
| Dodawanie własnych fiszek | ✅ |
| 10 przykładowych fiszek AI/ML | ✅ |
| Panel admina (zarządzanie treścią) | ✅ |

---

## Stack technologiczny

| Warstwa | Technologia |
|---|---|
| Backend | **Django 6.0** (Python ≥ 3.14) |
| Baza danych (dev) | SQLite |
| Baza danych (prod) | PostgreSQL — Supabase |
| Serwer WSGI | Gunicorn |
| Static files | WhiteNoise |
| Frontend | Bootstrap 5.3 + Bootstrap Icons |
| Package manager | `uv` |
| Deployment | **Fly.io** (Docker, region: ARN) |
| CI/CD | GitHub Actions (auto-deploy on merge) |

---

## Uruchomienie lokalnie

**Wymagania:** Python ≥ 3.14, [`uv`](https://docs.astral.sh/uv/)

```bash
git clone https://github.com/twoj-user/naukaai.git
cd naukaai

# Skopiuj przykładowy plik env
cp .env.example .env   # lub ustaw SECRET_KEY ręcznie

# Zainstaluj zależności
uv sync

# Migracje i uruchomienie
uv run python manage.py migrate
uv run python manage.py seed_cards       # opcjonalnie: 10 przykładowych fiszek
uv run python manage.py runserver
```

Aplikacja dostępna pod `http://localhost:8000`.

### Zmienne środowiskowe

| Zmienna | Opis | Wymagana |
|---|---|---|
| `SECRET_KEY` | Django secret key | tak |
| `DEBUG` | `1` = tryb dev, `0` = produkcja | nie (domyślnie `0`) |
| `DATABASE_URL` | URL bazy PostgreSQL | nie (domyślnie SQLite) |
| `ALLOWED_HOSTS` | Lista dozwolonych hostów (CSV) | nie |
| `CSRF_TRUSTED_ORIGINS` | Trusted origins dla CSRF (CSV) | nie |

---

## Komendy

```bash
uv run python manage.py runserver          # serwer dev na localhost:8000
uv run python manage.py migrate            # zastosuj migracje
uv run python manage.py makemigrations     # utwórz nowe migracje
uv run python manage.py seed_cards         # dodaj przykładowe fiszki AI/ML
uv run python manage.py createsuperuser    # utwórz konto administratora
uv run python manage.py test               # uruchom testy
```

---

## Deployment (Fly.io)

```bash
# Pierwsza konfiguracja
fly auth login
fly launch              # generuje fly.toml i Dockerfile (już zawarte w repo)

# Sekrety produkcyjne
fly secrets set \
  SECRET_KEY="..." \
  DATABASE_URL="postgres://..." \
  DEBUG=0 \
  CSRF_TRUSTED_ORIGINS="https://naukaai.fly.dev"

# Deploy
fly deploy

# Dodaj przykładowe fiszki na produkcji
fly ssh console --app naukaai -C "uv run python manage.py seed_cards"

# Logi
fly logs --app naukaai
```

---

## Struktura projektu

```
naukaai/
├── config/              # Konfiguracja Django (settings, urls, wsgi)
├── flashcards/          # Główna aplikacja: modele Card i CardReview, sesja nauki
│   ├── models.py        # Card, CardReview
│   ├── views.py         # Sesja nauki, lista i tworzenie fiszek
│   ├── templates/
│   └── management/commands/seed_cards.py
├── stats/               # Statystyki użytkownika (seria dni, % poprawnych)
│   ├── services.py
│   └── templates/
├── templates/           # Globalny layout (base.html), landing page, auth
│   ├── base.html
│   ├── home.html
│   └── registration/
├── Dockerfile
├── fly.toml
└── pyproject.toml
```

---

## Licencja

MIT
