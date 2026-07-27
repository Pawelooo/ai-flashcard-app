from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Topic
from .views import _CACHE_KEY_TOPICS


@receiver(post_save, sender=Topic)
@receiver(post_delete, sender=Topic)
def invalidate_topics_cache(sender, **kwargs):
    cache.delete(_CACHE_KEY_TOPICS)
