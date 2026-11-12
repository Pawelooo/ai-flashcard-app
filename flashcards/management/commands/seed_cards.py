from django.core.management.base import BaseCommand
from django.db import transaction

from flashcards.models import Card, Topic
from flashcards.seed_data import TOPICS


class Command(BaseCommand):
    help = "Seed the database with AI/ML flashcards (idempotent — safe to re-run)"

    @transaction.atomic
    def handle(self, *args, **options):
        total_new = 0
        for spec in TOPICS:
            topic, created = Topic.objects.get_or_create(
                slug=spec['slug'],
                defaults={
                    'name': spec['name'],
                    'icon': spec['icon'],
                    'description': spec['description'],
                },
            )
            if not created and not topic.description:
                # Uzupełnij tylko pusty opis — nie nadpisuj zmian zrobionych w adminie.
                topic.description = spec['description']
                topic.save(update_fields=['description'])

            existing = set(Card.objects.filter(topic=topic).values_list('question', flat=True))
            new_cards = [
                Card(topic=topic, question=q, answer=a)
                for q, a in spec['cards']
                if q not in existing
            ]
            Card.objects.bulk_create(new_cards)
            total_new += len(new_cards)
            self.stdout.write(f"{topic.name}: +{len(new_cards)} (razem {topic.cards.count()})")

        self.stdout.write(self.style.SUCCESS(f"Dodano {total_new} nowych fiszek."))
