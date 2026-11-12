from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Count, Max, Q
from django.utils import timezone

from flashcards.models import CardReview

from .types import StudyStats

_CACHE_KEY_LEADERBOARD = 'leaderboard_top10'


def get_leaderboard():
    cached = cache.get(_CACHE_KEY_LEADERBOARD)
    if cached is not None:
        return cached

    User = get_user_model()
    result = list(
        User.objects.annotate(
            total_correct=Count('card_reviews', filter=Q(card_reviews__is_correct=True))
        ).order_by('-total_correct', 'username')[:10]
    )
    cache.set(_CACHE_KEY_LEADERBOARD, result, timeout=settings.CACHE_TTL_LEADERBOARD)
    return result


def get_timed_leaderboard():
    """Top 10 rekordów trybu na czas. Bez cache — nowy rekord ma być widoczny od razu."""
    User = get_user_model()
    return list(
        User.objects.annotate(best_timed=Max('timed_runs__score'))
        .filter(best_timed__gt=0)
        .order_by('-best_timed', 'username')[:10]
    )


def compute_study_stats(user) -> StudyStats:
    today = timezone.localdate()

    today_qs = CardReview.objects.filter(user=user, reviewed_at__date=today)
    today_count = today_qs.count()

    if today_count:
        correct_count = today_qs.filter(is_correct=True).count()
        correct_pct = round(correct_count / today_count * 100)
    else:
        correct_pct = None

    last_review = (
        CardReview.objects.filter(user=user)
        .order_by('-reviewed_at')
        .values_list('reviewed_at', flat=True)
        .first()
    )
    last_reviewed = last_review.date() if last_review else None
    next_review = _compute_next_review(last_reviewed, today)

    return StudyStats(
        today_count=today_count,
        correct_pct=correct_pct,
        streak=_compute_streak(user, today),
        last_reviewed=last_reviewed,
        next_review=next_review,
    )


def _compute_next_review(last_reviewed: date | None, today: date) -> date:
    if last_reviewed is None:
        return today
    if last_reviewed >= today:
        return today + timedelta(days=1)
    return today


def _compute_streak(user, today: date) -> int:
    reviewed_dates = set(
        CardReview.objects.filter(user=user).dates('reviewed_at', 'day')
    )

    streak = 0
    current = today
    while current in reviewed_dates:
        streak += 1
        current -= timedelta(days=1)
    return streak


# ── Panel postępów ──────────────────────────────────────────────────────────

SECONDS_PER_CARD = 20          # szacunek do „to około N minut”
ACCURACY_WINDOW_DAYS = 14
HEATMAP_WEEKS = 12
CHART_W, CHART_H = 720, 220    # układ współrzędnych SVG wykresu dziennego
CHART_PAD_L, CHART_PAD_R, CHART_PAD_T, CHART_PAD_B = 40, 12, 12, 28


def _longest_streak(dates) -> int:
    best = run = 0
    prev = None
    for d in sorted(dates):
        run = run + 1 if prev is not None and d - prev == timedelta(days=1) else 1
        best = max(best, run)
        prev = d
    return best


def _daily_counts(user, since: date):
    """{data: (wszystkie, poprawne)} od `since` włącznie, w strefie czasowej projektu."""
    from django.db.models.functions import TruncDate

    rows = (
        CardReview.objects.filter(user=user, reviewed_at__date__gte=since)
        .annotate(day=TruncDate('reviewed_at'))
        .values('day')
        .annotate(total=Count('id'), correct=Count('id', filter=Q(is_correct=True)))
    )
    return {r['day']: (r['total'], r['correct']) for r in rows}


def _chart(series):
    """Punkty SVG dla linii % poprawnych. Dni bez odpowiedzi przerywają linię."""
    n = len(series)
    plot_w = CHART_W - CHART_PAD_L - CHART_PAD_R
    plot_h = CHART_H - CHART_PAD_T - CHART_PAD_B

    # Współrzędne jako tekst z kropką — szablon z polskim locale wstawiłby przecinek i zepsuł SVG
    def x(i):
        return f'{CHART_PAD_L + (plot_w * i / (n - 1) if n > 1 else plot_w / 2):.1f}'

    def y(pct):
        return f'{CHART_PAD_T + plot_h * (1 - pct / 100):.1f}'

    segments, current, points = [], [], []
    for i, day in enumerate(series):
        if day['pct'] is None:
            if current:
                segments.append(current)
                current = []
            continue
        pt = {'x': x(i), 'y': y(day['pct']), **day}
        current.append(pt)
        points.append(pt)
    if current:
        segments.append(current)

    grid = [{'y': y(v), 'label': f'{v}%'} for v in (0, 25, 50, 75, 100)]
    ticks = [{'x': x(i), 'label': series[i]['date'].strftime('%d.%m')} for i in sorted({0, n // 2, n - 1})]
    return {
        'width': CHART_W, 'height': CHART_H,
        'left': CHART_PAD_L, 'right': CHART_W - CHART_PAD_R,
        'bottom': CHART_H - CHART_PAD_B + 18,
        'polylines': [' '.join(f"{p['x']},{p['y']}" for p in seg) for seg in segments],
        'points': points,
        'last': points[-1] if points else None,
        'grid': grid,
        'ticks': ticks,
    }


def _heatmap(counts, today: date):
    """12 tygodni × 7 dni (kolumna = tydzień od poniedziałku), poziomy 0–4 względem maksimum."""
    start = today - timedelta(days=today.weekday()) - timedelta(weeks=HEATMAP_WEEKS - 1)
    peak = max((total for total, _ in counts.values()), default=0)
    weeks = []
    for w in range(HEATMAP_WEEKS):
        days = []
        for d in range(7):
            day = start + timedelta(weeks=w, days=d)
            total = counts.get(day, (0, 0))[0]
            level = 0 if not total else max(1, -(-4 * total // peak))  # sufit, 1–4
            days.append({'date': day, 'total': total, 'level': level, 'future': day > today})
        weeks.append(days)
    return weeks


def compute_dashboard(user, range_days: int = 30) -> dict:
    from flashcards.models import Card, Topic
    from flashcards.progress import apply_progress

    today = timezone.localdate()
    oldest_needed = min(
        today - timedelta(days=range_days - 1),
        today - timedelta(weeks=HEATMAP_WEEKS),
    )
    counts = _daily_counts(user, oldest_needed)

    # Liczby na górze
    review_dates = set(CardReview.objects.filter(user=user).dates('reviewed_at', 'day'))
    window_start = today - timedelta(days=ACCURACY_WINDOW_DAYS - 1)
    w_total = sum(t for d, (t, _) in counts.items() if d >= window_start)
    w_correct = sum(c for d, (_, c) in counts.items() if d >= window_start)

    topics = apply_progress(
        list(Topic.objects.annotate(card_count=Count('cards')).order_by('name')), user
    )
    with_cards = [t for t in topics if t.card_count]
    total_cards = Card.objects.filter(topic__isnull=False).count()
    mastered = sum(t.mastered_count for t in with_cards)
    due = sum(t.due_count for t in with_cards)

    # Wykres dzienny
    series = []
    for i in range(range_days):
        day = today - timedelta(days=range_days - 1 - i)
        total, correct = counts.get(day, (0, 0))
        series.append({
            'date': day, 'total': total, 'correct': correct,
            'pct': round(correct / total * 100) if total else None,
        })
    r_total = sum(d['total'] for d in series)
    r_correct = sum(d['correct'] for d in series)

    return {
        'streak': _compute_streak(user, today),
        'longest_streak': _longest_streak(review_dates),
        'accuracy_pct': round(w_correct / w_total * 100) if w_total else None,
        'accuracy_days': ACCURACY_WINDOW_DAYS,
        'mastered': mastered,
        'total_cards': total_cards,
        'due': due,
        'due_topics': sum(1 for t in with_cards if t.due_count),
        'due_minutes': max(1, -(-due * SECONDS_PER_CARD // 60)) if due else 0,
        'range_days': range_days,
        'series': series,
        'range_avg_pct': round(r_correct / r_total * 100) if r_total else None,
        'chart': _chart(series),
        'weakest': sorted(
            (t for t in with_cards if t.due_count), key=lambda t: (t.mastered_pct, t.name)
        )[:3],
        'topics': sorted(with_cards, key=lambda t: (-t.mastered_pct, t.name)),
        'heatmap': _heatmap(counts, today),
        'heatmap_weeks': HEATMAP_WEEKS,
    }
