"""Wpisz odpowiedź: AI porównuje ją z odpowiedzią wzorcową i mówi, czego brakuje."""
import random

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django_ratelimit.decorators import ratelimit

from .ai import MAX_ANSWER_CHARS, AIError, grade_answer
from .models import Card, CardReview, Topic
from .session import SK

SESSION_SIZE = 10

VERDICTS = {
    'correct': ('Dobrze!', 'badge-done', 'bi-check2'),
    'partial': ('Prawie dobrze', 'badge-due', 'bi-dash-circle'),
    'incorrect': ('Źle', 'badge-wrong', 'bi-x-lg'),
    'skipped': ('Pominięte', 'badge-wrong', 'bi-skip-forward'),
}


@login_required
@ratelimit(key='user', rate='20/h', block=True, method=['POST'])
def written_start(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    topic = get_object_or_404(Topic, pk=request.POST.get('topic_id'))
    card_ids = list(topic.cards.values_list('id', flat=True))
    if not card_ids:
        messages.warning(request, 'Ten temat nie ma jeszcze fiszek.')
        return redirect('flashcards:topics')

    chosen = random.sample(card_ids, min(SESSION_SIZE, len(card_ids)))
    for key in SK.ALL:
        request.session.pop(key, None)
    request.session[SK.TOPIC_ID] = topic.pk
    request.session[SK.CARDS] = chosen
    request.session[SK.INDEX] = 0
    request.session[SK.SCORE] = 0
    request.session[SK.WRONG_IDS] = []
    return redirect('flashcards:written_play')


@login_required
# Limit na ocenianie (każda ocena to wywołanie AI) — osobno od startu sesji
@ratelimit(key='user', rate='120/h', block=True, method=['POST'])
def written_play(request):
    required = {SK.CARDS, SK.INDEX, SK.SCORE, SK.WRONG_IDS}
    if not required.issubset(request.session.keys()):
        return redirect('flashcards:topics')

    card_ids = request.session[SK.CARDS]
    index = request.session[SK.INDEX]
    if index >= len(card_ids):
        return redirect('flashcards:study_results')

    card = Card.objects.filter(pk=card_ids[index]).first()
    if card is None:
        request.session[SK.INDEX] = index + 1
        return redirect('flashcards:written_play')

    context = {
        'card': card,
        'current': index + 1,
        'total': len(card_ids),
        'max_chars': MAX_ANSWER_CHARS,
    }
    if request.method != 'POST':
        return render(request, 'flashcards/written.html', context)

    try:
        card_id = int(request.POST.get('card_id', ''))
    except ValueError:
        return redirect('flashcards:written_play')
    if card_id != card.pk:
        # Odświeżenie po ocenie albo podwójne wysłanie — nie oceniamy drugi raz
        return redirect('flashcards:written_play')

    user_answer = request.POST.get('answer', '').strip()[:MAX_ANSWER_CHARS]
    if request.POST.get('action') == 'skip' or not user_answer:
        verdict, grade = 'skipped', None
    else:
        try:
            grade = grade_answer(card, user_answer)
        except AIError as exc:
            # Nie przesuwamy karty — użytkownik może spróbować ponownie, tekst zostaje
            context.update({'error': str(exc), 'user_answer': user_answer})
            return render(request, 'flashcards/written.html', context)
        verdict = grade.verdict

    is_correct = verdict == 'correct'
    CardReview.objects.create(user=request.user, card=card, is_correct=is_correct)
    if is_correct:
        request.session[SK.SCORE] += 1
    else:
        request.session[SK.WRONG_IDS] = [*request.session[SK.WRONG_IDS], card.pk]
    request.session[SK.INDEX] = index + 1

    is_last = index + 1 >= len(card_ids)
    label, badge, icon = VERDICTS[verdict]
    context.update({
        'answered': True,
        'verdict': verdict,
        'verdict_label': label,
        'verdict_badge': badge,
        'verdict_icon': icon,
        'grade': grade,
        'user_answer': user_answer,
        'is_last': is_last,
        'next_url': reverse('flashcards:study_results' if is_last else 'flashcards:written_play'),
    })
    return render(request, 'flashcards/written.html', context)
