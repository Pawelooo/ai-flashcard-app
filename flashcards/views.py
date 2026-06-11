import logging
import random

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import CreateView, ListView
from django.urls import reverse_lazy

from .models import Card, CardReview, Topic
from .forms import CardForm

_SESSION_KEYS = [
    'session_topic_id',
    'session_cards',
    'session_index',
    'session_score',
    'session_wrong_ids',
]


class TopicsListView(LoginRequiredMixin, ListView):
    model = Topic
    template_name = 'flashcards/topics.html'
    context_object_name = 'topics'
    ordering = ['name']

    def get(self, request, *args, **kwargs):
        for key in _SESSION_KEYS:
            request.session.pop(key, None)
        return super().get(request, *args, **kwargs)


@login_required
def session_start(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    topic = get_object_or_404(Topic, pk=request.POST.get('topic_id'))
    card_ids = list(topic.cards.values_list('id', flat=True))

    if not card_ids:
        messages.warning(request, 'Ten temat nie ma jeszcze fiszek.')
        return redirect('flashcards:topics')

    random.shuffle(card_ids)
    request.session['session_topic_id'] = topic.pk
    request.session['session_cards'] = card_ids
    request.session['session_index'] = 0
    request.session['session_score'] = 0
    request.session['session_wrong_ids'] = []
    return redirect('flashcards:study')


@login_required
def session_results(request):
    required = {'session_cards', 'session_score', 'session_wrong_ids', 'session_topic_id'}
    if not required.issubset(request.session.keys()):
        return redirect('flashcards:topics')

    score = request.session['session_score']
    total = len(request.session['session_cards'])
    wrong_ids = request.session['session_wrong_ids']
    topic_id = request.session['session_topic_id']
    missed_cards = Card.objects.filter(pk__in=wrong_ids)
    percent = round(score / total * 100) if total else 0

    response = render(request, 'flashcards/session_results.html', {
        'score': score,
        'total': total,
        'percent': percent,
        'missed_cards': missed_cards,
        'topic_id': topic_id,
    })
    if wrong_ids:
        request.session['last_wrong_ids'] = wrong_ids
    for key in _SESSION_KEYS:
        request.session.pop(key, None)
    return response


class CardListView(LoginRequiredMixin, ListView):
    model = Card
    template_name = 'flashcards/card_list.html'
    context_object_name = 'cards'
    ordering = ['-created_at']


class CardCreateView(LoginRequiredMixin, CreateView):
    model = Card
    form_class = CardForm
    template_name = 'flashcards/card_form.html'
    success_url = reverse_lazy('flashcards:card_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


@login_required
def study_review(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    wrong_ids = request.session.pop('last_wrong_ids', None)

    if not wrong_ids:
        messages.warning(request, 'Brak błędnych kart — najpierw ukończ sesję.')
        return redirect('flashcards:topics')

    random.shuffle(wrong_ids)
    request.session['session_topic_id'] = None
    request.session['session_cards'] = wrong_ids
    request.session['session_index'] = 0
    request.session['session_score'] = 0
    request.session['session_wrong_ids'] = []
    return redirect('flashcards:study')


@login_required
def study_card(request):
    required = {'session_cards', 'session_index', 'session_score', 'session_wrong_ids'}
    if not required.issubset(request.session.keys()):
        return redirect('flashcards:topics')

    card_ids = request.session['session_cards']
    index = request.session['session_index']

    if request.method == 'POST':
        try:
            card_id = int(request.POST.get('card_id', ''))
        except ValueError:
            logging.warning("Invalid card_id in POST: %r", request.POST.get('card_id'))
            return redirect('flashcards:study')
        if card_id != card_ids[index]:
            return redirect('flashcards:study')
        is_correct = request.POST.get('is_correct') == '1'
        card = get_object_or_404(Card, pk=card_id)
        CardReview.objects.create(user=request.user, card=card, is_correct=is_correct)

        if is_correct:
            request.session['session_score'] += 1
        else:
            wrong = request.session['session_wrong_ids']
            wrong.append(card_id)
            request.session['session_wrong_ids'] = wrong

        request.session['session_index'] = index + 1

        if index + 1 >= len(card_ids):
            return redirect('flashcards:study_results')
        return redirect('flashcards:study')

    if index >= len(card_ids):
        return redirect('flashcards:study_results')
    card = get_object_or_404(Card, pk=card_ids[index])
    return render(request, 'flashcards/study.html', {
        'card': card,
        'current': index + 1,
        'total': len(card_ids),
    })
