from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Card, Topic


class StudySessionTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.topic = Topic.objects.create(name='Test Topic', slug='test-topic')
        self.cards = [
            Card.objects.create(topic=self.topic, question=f'Q{i}', answer=f'A{i}')
            for i in range(3)
        ]

    def _start_session(self):
        return self.client.post(
            reverse('flashcards:study_start'),
            {'topic_id': self.topic.pk},
        )

    def test_full_session_happy_path(self):
        self.client.force_login(self.user)
        response = self._start_session()
        self.assertRedirects(response, reverse('flashcards:study'))

        # answer all 3 cards: correct, incorrect, correct → score=2, missed=1
        answers = [1, 0, 1]
        for is_correct in answers:
            response = self.client.get(reverse('flashcards:study'))
            self.assertEqual(response.status_code, 200)
            card_id = response.context['card'].pk
            response = self.client.post(
                reverse('flashcards:study'),
                {'card_id': card_id, 'is_correct': str(is_correct)},
            )

        # last POST redirects to results — check without fetching (would clear session)
        self.assertEqual(response.status_code, 302)
        self.assertIn('study/results', response['Location'])

        response = self.client.get(reverse('flashcards:study_results'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['score'], 2)
        self.assertEqual(response.context['total'], 3)
        self.assertEqual(response.context['percent'], 67)
        self.assertEqual(len(response.context['missed_cards']), 1)

        # session keys cleared after results render
        session = self.client.session
        self.assertNotIn('session_cards', session)

    def test_empty_deck_redirects(self):
        self.client.force_login(self.user)
        empty_topic = Topic.objects.create(name='Empty', slug='empty')
        response = self.client.post(
            reverse('flashcards:study_start'),
            {'topic_id': empty_topic.pk},
        )
        self.assertRedirects(response, reverse('flashcards:topics'))
        msgs = list(response.wsgi_request._messages)
        self.assertTrue(any('fiszek' in str(m) for m in msgs))

    def test_study_without_session_redirects(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('flashcards:study'))
        self.assertRedirects(response, reverse('flashcards:topics'))

    def test_results_without_session_redirects(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('flashcards:study_results'))
        self.assertRedirects(response, reverse('flashcards:topics'))

    def test_visiting_topics_clears_session(self):
        self.client.force_login(self.user)
        session = self.client.session
        session['session_cards'] = [1, 2, 3]
        session['session_index'] = 1
        session['session_score'] = 1
        session['session_wrong_ids'] = []
        session['session_topic_id'] = self.topic.pk
        session.save()

        self.client.get(reverse('flashcards:topics'))
        session = self.client.session
        self.assertNotIn('session_cards', session)
        self.assertNotIn('session_index', session)
        self.assertNotIn('session_score', session)
        self.assertNotIn('session_wrong_ids', session)
        self.assertNotIn('session_topic_id', session)
