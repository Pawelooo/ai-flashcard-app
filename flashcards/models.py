from django.conf import settings
from django.db import models
from django.utils import timezone


class Card(models.Model):
    question = models.TextField()
    answer = models.TextField()
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
