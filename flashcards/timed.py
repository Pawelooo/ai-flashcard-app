"""Tryb na czas: 60 sekund, ile zdążysz. Czas i wynik pilnuje serwer."""
import random

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import F, Max
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django_ratelimit.decorators import ratelimit

from .models import Card, CardReview, TimedRun, Topic
from .session import SK


def _clear_timed_session(request):
    for key in SK.TIMED_ALL:
        request.session.pop(key, None)


def _current_run(request):
    run_id = request.session.get(SK.TIMED_RUN)
    if run_id is None:
        return None
    return TimedRun.objects.filter(pk=run_id, user=request.user).first()


@login_required
@ratelimit(key='user', rate='30/h', block=True, method=['POST'])
def timed_start(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    topic = None
    cards = Card.objects.filter(topic__isnull=False)
    if request.POST.get('topic_id'):
        topic = get_object_or_404(Topic, pk=request.POST['topic_id'])
        cards = topic.cards.all()
    card_ids = list(cards.values_list('id', flat=True))

    if not card_ids:
        messages.warning(request, 'Ten temat nie ma jeszcze fiszek.')
        return redirect('flashcards:topics')

    random.shuffle(card_ids)
    run = TimedRun.objects.create(user=request.user, topic=topic)
    request.session[SK.TIMED_RUN] = run.pk
    request.session[SK.TIMED_CARDS] = card_ids
    request.session[SK.TIMED_INDEX] = 0
    return redirect('flashcards:timed_play')


@login_required
def timed_play(request):
    run = _current_run(request)
    if run is None or run.finished_at is not None:
        _clear_timed_session(request)
        return redirect('flashcards:topics')

    if not run.accepts_answers():
        return redirect('flashcards:timed_results', pk=run.pk)

    card_ids = request.session[SK.TIMED_CARDS]
    index = request.session[SK.TIMED_INDEX]

    if request.method == 'POST':
        try:
            card_id = int(request.POST.get('card_id', ''))
        except ValueError:
            return redirect('flashcards:timed_play')
        # Odpowiedź na inną kartę niż bieżąca = podwójne kliknięcie albo stara karta
        if card_id != card_ids[index]:
            return redirect('flashcards:timed_play')

        is_correct = request.POST.get('is_correct') == '1'
        card = Card.objects.filter(pk=card_id).first()
        if card is not None:
            CardReview.objects.create(user=request.user, card=card, is_correct=is_correct)
        TimedRun.objects.filter(pk=run.pk).update(
            answered=F('answered') + 1,
            score=F('score') + (1 if is_correct else 0),
        )

        index += 1
        if index >= len(card_ids):
            # Koniec talii przed końcem czasu — tasujemy i lecimy od nowa
            random.shuffle(card_ids)
            request.session[SK.TIMED_CARDS] = card_ids
            index = 0
        request.session[SK.TIMED_INDEX] = index
        return redirect('flashcards:timed_play')

    card = Card.objects.filter(pk=card_ids[index]).first()
    if card is None:
        # Fiszkę usunięto w trakcie gry — przeskocz ją
        request.session[SK.TIMED_INDEX] = (index + 1) % len(card_ids)
        return redirect('flashcards:timed_play')

    return render(request, 'flashcards/timed.html', {
        'run': run,
        'card': card,
        # Liczby całkowite w ms — float w szablonie z polskim locale dostałby przecinek
        'ms_left': int(run.seconds_left() * 1000),
        'duration_ms': TimedRun.DURATION_SECONDS * 1000,
    })


@login_required
def timed_results(request, pk):
    run = get_object_or_404(TimedRun, pk=pk, user=request.user)
    run.finish(timezone.now())
    if request.session.get(SK.TIMED_RUN) == run.pk:
        _clear_timed_session(request)

    previous_best = (
        TimedRun.objects.filter(user=request.user)
        .exclude(pk=run.pk)
        .aggregate(best=Max('score'))['best']
    ) or 0
    best = max(previous_best, run.score)

    User = get_user_model()
    better_players = (
        User.objects.annotate(best=Max('timed_runs__score'))
        .filter(best__gt=best)
        .count()
    )

    return render(request, 'flashcards/timed_results.html', {
        'run': run,
        'accuracy': round(run.score / run.answered * 100) if run.answered else 0,
        'best': best,
        'is_record': run.score > previous_best and run.score > 0,
        'rank': better_players + 1 if best > 0 else None,
    })
