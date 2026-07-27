from django.apps import AppConfig


class FlashcardsConfig(AppConfig):
    name = 'flashcards'

    def ready(self):
        from . import signals  # noqa: F401
