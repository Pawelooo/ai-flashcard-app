from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Count, Q
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
