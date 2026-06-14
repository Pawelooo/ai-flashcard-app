import logging
import random

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.core.exceptions import PermissionDenied
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.urls import reverse_lazy

from .models import Card, CardReview, Topic
from .forms import CardForm
from .session import SK, get_session


class TopicsListView(LoginRequiredMixin, ListView):
    model = Topic
    template_name = 'flashcards/topics.html'
    context_object_name = 'topics'
    ordering = ['name']

    def get(self, request, *args, **kwargs):
        for key in SK.ALL:
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
    request.session[SK.TOPIC_ID] = topic.pk
    request.session[SK.CARDS] = card_ids
    request.session[SK.INDEX] = 0
    request.session[SK.SCORE] = 0
    request.session[SK.WRONG_IDS] = []
    return redirect('flashcards:study')


@login_required
def session_results(request):
    required = {SK.CARDS, SK.SCORE, SK.WRONG_IDS, SK.TOPIC_ID}
    if not required.issubset(request.session.keys()):
        return redirect('flashcards:topics')

    state = get_session(request)
    score = state[SK.SCORE]
    total = len(state[SK.CARDS])
    wrong_ids = state[SK.WRONG_IDS]
    topic_id = state[SK.TOPIC_ID]
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
        request.session[SK.LAST_WRONG_IDS] = wrong_ids
    for key in SK.ALL:
        request.session.pop(key, None)
    return response


class CardListView(LoginRequiredMixin, ListView):
    model = Card
    template_name = 'flashcards/card_list.html'
    context_object_name = 'cards'
    ordering = ['-created_at']

    def get_queryset(self):
        return super().get_queryset().select_related('topic', 'created_by')


class CardCreateView(LoginRequiredMixin, CreateView):
    model = Card
    form_class = CardForm
    template_name = 'flashcards/card_form.html'
    success_url = reverse_lazy('flashcards:card_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class CardEditPermissionMixin:
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # None != any User, so cards without an owner are staff-only
        if obj.created_by != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied
        return obj


class CardUpdateView(LoginRequiredMixin, CardEditPermissionMixin, UpdateView):
    model = Card
    form_class = CardForm
    template_name = 'flashcards/card_form.html'

    # success_url can't be a class attribute here — URL requires self.object.pk
    def get_success_url(self):
        return reverse_lazy('flashcards:card_detail', kwargs={'pk': self.object.pk})


class CardDeleteView(LoginRequiredMixin, CardEditPermissionMixin, DeleteView):
    model = Card
    template_name = 'flashcards/card_delete_confirm.html'
    success_url = reverse_lazy('flashcards:card_list')


class CardDetailView(LoginRequiredMixin, DetailView):
    model = Card
    template_name = 'flashcards/card_detail.html'
    context_object_name = 'card'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        card = self.object
        ctx['can_edit'] = (
            card.created_by == self.request.user or self.request.user.is_staff
        )
        return ctx


@login_required
def study_review(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    wrong_ids = request.session.pop(SK.LAST_WRONG_IDS, None)

    if not wrong_ids:
        messages.warning(request, 'Brak błędnych kart — najpierw ukończ sesję.')
        return redirect('flashcards:topics')

    random.shuffle(wrong_ids)
    request.session[SK.TOPIC_ID] = None
    request.session[SK.CARDS] = wrong_ids
    request.session[SK.INDEX] = 0
    request.session[SK.SCORE] = 0
    request.session[SK.WRONG_IDS] = []
    return redirect('flashcards:study')


@login_required
def study_card(request):
    required = {SK.CARDS, SK.INDEX, SK.SCORE, SK.WRONG_IDS}
    if not required.issubset(request.session.keys()):
        return redirect('flashcards:topics')

    state = get_session(request)
    card_ids = state[SK.CARDS]
    index = state[SK.INDEX]

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
            request.session[SK.SCORE] += 1
        else:
            wrong = state[SK.WRONG_IDS]
            wrong.append(card_id)
            request.session[SK.WRONG_IDS] = wrong

        request.session[SK.INDEX] = index + 1

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
