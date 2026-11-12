from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Card, Topic
from .views import _CACHE_KEY_TOPICS


# Card też, bo cache trzyma teraz card_count każdego tematu
@receiver(post_save, sender=Topic)
@receiver(post_delete, sender=Topic)
@receiver(post_save, sender=Card)
@receiver(post_delete, sender=Card)
def invalidate_topics_cache(sender, **kwargs):
    cache.delete(_CACHE_KEY_TOPICS)
