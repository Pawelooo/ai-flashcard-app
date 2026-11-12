from django.core.management.base import BaseCommand, CommandError

from flashcards.ai import DISTRACTORS_PER_CARD, AIError, ensure_distractors
from flashcards.models import Card
from flashcards.quiz import QUIZ_SIZE


class Command(BaseCommand):
    help = 'Generuje przez AI błędne odpowiedzi do quizu ABCD dla fiszek, które ich nie mają.'

    def add_arguments(self, parser):
        parser.add_argument('--topic', help='slug tematu (domyślnie: wszystkie tematy)')
        parser.add_argument('--dry-run', action='store_true', help='tylko policz, bez wywołań AI')

    def handle(self, *args, **options):
        cards = Card.objects.filter(topic__isnull=False).order_by('pk')
        if options['topic']:
            cards = cards.filter(topic__slug=options['topic'])
        missing = [c for c in cards if len(c.distractors) < DISTRACTORS_PER_CARD]
        self.stdout.write(f'Fiszek bez odpowiedzi do quizu: {len(missing)}')
        if options['dry_run'] or not missing:
            return

        done = 0
        for start in range(0, len(missing), QUIZ_SIZE):
            batch = missing[start:start + QUIZ_SIZE]
            try:
                done += len(ensure_distractors(batch))
            except AIError as exc:
                raise CommandError(f'Przerwano po {done} fiszkach: {exc}') from exc
            self.stdout.write(f'  {done}/{len(missing)}')
        self.stdout.write(self.style.SUCCESS(f'Gotowe: {done} z {len(missing)} fiszek.'))
