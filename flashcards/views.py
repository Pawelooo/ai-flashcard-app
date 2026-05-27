import random

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
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

    def get(self, request, *args, **kwargs):
        for key in _SESSION_KEYS:
            request.session.pop(key, None)
        return super().get(request, *args, **kwargs)


@login_required
def session_start(request):
    return redirect('flashcards:topics')


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


@login_required
def study(request):
    if request.method == 'POST':
        card_id = request.POST.get('card_id')
        is_correct = request.POST.get('is_correct') == '1'
        card = get_object_or_404(Card, pk=card_id)
        CardReview.objects.create(user=request.user, card=card, is_correct=is_correct)
        return redirect('flashcards:study')

    cards = list(Card.objects.all())
    if not cards:
        return render(request, 'flashcards/study.html', {'card': None})

    card = random.choice(cards)
    return render(request, 'flashcards/study.html', {'card': card})
