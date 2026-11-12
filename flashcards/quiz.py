"""Quiz ABCD: poprawna odpowiedź + 3 błędne wygenerowane przez AI."""
import random

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django_ratelimit.decorators import ratelimit

from .ai import AIError, ensure_distractors
from .models import Card, CardReview, Topic
from .session import SK

# Tyle kart na sesję — wszystkie brakujące dystraktory idą jednym wywołaniem AI,
# które musi się zmieścić w limicie czasu requestu.
QUIZ_SIZE = 10
LETTERS = 'ABCD'


def _clear(request):
    for key in SK.ALL:
        request.session.pop(key, None)


@login_required
@ratelimit(key='user', rate='20/h', block=True, method=['POST'])
def quiz_start(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    topic = get_object_or_404(Topic, pk=request.POST.get('topic_id'))
    card_ids = list(topic.cards.values_list('id', flat=True))
    if not card_ids:
        messages.warning(request, 'Ten temat nie ma jeszcze fiszek.')
        return redirect('flashcards:topics')

    chosen = random.sample(card_ids, min(QUIZ_SIZE, len(card_ids)))
    try:
        ready = ensure_distractors(list(Card.objects.filter(pk__in=chosen)))
    except AIError as exc:
        messages.error(request, f'Nie udało się przygotować quizu: {exc}')
        return redirect('flashcards:topics')
    if not ready:
        messages.error(request, 'Nie udało się przygotować pytań do quizu — spróbuj ponownie.')
        return redirect('flashcards:topics')

    ids = [c.pk for c in ready]
    random.shuffle(ids)
    _clear(request)
    request.session[SK.TOPIC_ID] = topic.pk
    request.session[SK.CARDS] = ids
    request.session[SK.INDEX] = 0
    request.session[SK.SCORE] = 0
    request.session[SK.WRONG_IDS] = []
    return redirect('flashcards:quiz_play')


def _options_for(request, card):
    """Opcje bieżącej karty. Losowane raz i zapamiętane, żeby odświeżenie ich nie tasowało."""
    stored = request.session.get(SK.QUIZ_OPTIONS)
    if stored and stored['card_id'] == card.pk:
        return stored
    options = [card.answer, *card.distractors[:3]]
    random.shuffle(options)
    stored = {
        'card_id': card.pk,
        'options': options,
        'correct': options.index(card.answer),
    }
    request.session[SK.QUIZ_OPTIONS] = stored
    return stored


@login_required
def quiz_play(request):
    required = {SK.CARDS, SK.INDEX, SK.SCORE, SK.WRONG_IDS}
    if not required.issubset(request.session.keys()):
        return redirect('flashcards:topics')

    card_ids = request.session[SK.CARDS]
    index = request.session[SK.INDEX]
    if index >= len(card_ids):
        return redirect('flashcards:study_results')

    card = Card.objects.filter(pk=card_ids[index]).first()
    if card is None or len(card.distractors) < 3:
        # Fiszkę usunięto albo edytowano w trakcie quizu — pomijamy ją
        request.session[SK.INDEX] = index + 1
        request.session.pop(SK.QUIZ_OPTIONS, None)
        return redirect('flashcards:quiz_play')

    quiz = _options_for(request, card)
    context = {
        'card': card,
        'options': list(zip(LETTERS, quiz['options'])),
        'current': index + 1,
        'total': len(card_ids),
    }

    if request.method == 'POST':
        try:
            card_id = int(request.POST.get('card_id', ''))
            choice = int(request.POST.get('choice', ''))
        except ValueError:
            return redirect('flashcards:quiz_play')
        if card_id != card.pk or not 0 <= choice < len(quiz['options']):
            return redirect('flashcards:quiz_play')

        is_correct = choice == quiz['correct']
        CardReview.objects.create(user=request.user, card=card, is_correct=is_correct)
        if is_correct:
            request.session[SK.SCORE] += 1
        else:
            request.session[SK.WRONG_IDS] = [*request.session[SK.WRONG_IDS], card.pk]
        request.session[SK.INDEX] = index + 1
        request.session.pop(SK.QUIZ_OPTIONS, None)

        # Odpowiedź od razu z informacją zwrotną; „Dalej” to zwykły GET
        is_last = index + 1 >= len(card_ids)
        context.update({
            'answered': True,
            'choice': choice,
            'correct': quiz['correct'],
            'is_correct': is_correct,
            'next_url': reverse('flashcards:study_results' if is_last else 'flashcards:quiz_play'),
            'is_last': is_last,
        })

    return render(request, 'flashcards/quiz.html', context)
