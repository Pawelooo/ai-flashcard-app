from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class Topic(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=8, blank=True, default='🧠', help_text='Emoji wyświetlane na kafelku tematu.')
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Card(models.Model):
    topic = models.ForeignKey(
        Topic,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cards',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_cards',
    )
    question = models.TextField()
    answer = models.TextField()
    # 3 błędne odpowiedzi do quizu ABCD — generowane przez AI przy pierwszym użyciu
    distractors = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question[:80]


class CardReview(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='card_reviews',
    )
    card = models.ForeignKey(
        Card,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviews',
    )
    reviewed_at = models.DateTimeField(default=timezone.now)
    is_correct = models.BooleanField()

    class Meta:
        ordering = ['-reviewed_at']
        indexes = [
            models.Index(fields=['user', 'reviewed_at']),
        ]


class TimedRun(models.Model):
    """Jedna rozgrywka trybu na czas. Wynik liczy serwer, odpowiedź po czasie się nie liczy."""

    DURATION_SECONDS = 60
    # Zapas na opóźnienie sieci przy odpowiedzi wysłanej w ostatniej chwili.
    GRACE_SECONDS = 2

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='timed_runs',
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='timed_runs',
    )
    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)
    score = models.PositiveIntegerField(default=0)
    answered = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', '-score']),
        ]

    def __str__(self):
        return f'{self.user} — {self.score} pkt ({self.started_at:%Y-%m-%d %H:%M})'

    @property
    def deadline(self):
        return self.started_at + timedelta(seconds=self.DURATION_SECONDS)

    def seconds_left(self, now=None):
        now = now or timezone.now()
        return max(0.0, (self.deadline - now).total_seconds())

    def accepts_answers(self, now=None):
        now = now or timezone.now()
        return (
            self.finished_at is None
            and now <= self.deadline + timedelta(seconds=self.GRACE_SECONDS)
        )

    def finish(self, now=None):
        if self.finished_at is None:
            now = now or timezone.now()
            self.finished_at = min(now, self.deadline)
            self.save(update_fields=['finished_at'])
