"""Postęp użytkownika na tematach — wspólne dla listy tematów i panelu."""
from django.db.models import Count

from .models import Card


def mastered_by_topic(user):
    """{topic_id: liczba opanowanych fiszek}. Opanowana = co najmniej jedna poprawna odpowiedź."""
    return dict(
        Card.objects.filter(reviews__user=user, reviews__is_correct=True, topic__isnull=False)
        .values_list('topic_id')
        .annotate(mastered=Count('pk', distinct=True))
    )


def apply_progress(topics, user):
    """Dopisuje mastered_count / due_count / mastered_pct do tematów z adnotacją card_count."""
    mastered = mastered_by_topic(user)
    for topic in topics:
        done = mastered.get(topic.pk, 0)
        topic.mastered_count = done
        topic.due_count = max(topic.card_count - done, 0)
        topic.mastered_pct = round(done / topic.card_count * 100) if topic.card_count else 0
    return topics
