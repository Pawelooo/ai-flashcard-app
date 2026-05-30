from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Card, CardReview, Topic


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


class SpacedRepetitionTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='sruser', password='pass')
        self.topic = Topic.objects.create(name='SR Topic', slug='sr-topic')
        self.cards = [
            Card.objects.create(topic=self.topic, question=f'SRQ{i}', answer=f'SRA{i}')
            for i in range(3)
        ]

    def _post_review(self):
        return self.client.post(reverse('flashcards:study_review'))

    def test_review_start_no_history_redirects(self):
        self.client.force_login(self.user)
        response = self._post_review()
        self.assertRedirects(response, reverse('flashcards:topics'))
        msgs = list(response.wsgi_request._messages)
        self.assertTrue(any(m.level_tag == 'warning' for m in msgs))

    def test_review_start_no_wrong_cards_redirects(self):
        self.client.force_login(self.user)
        now = timezone.now()
        for card in self.cards:
            CardReview.objects.create(user=self.user, card=card, is_correct=True, reviewed_at=now)
        response = self._post_review()
        self.assertRedirects(response, reverse('flashcards:topics'))
        msgs = list(response.wsgi_request._messages)
        self.assertTrue(any(m.level_tag == 'info' for m in msgs))

    def test_review_session_happy_path(self):
        self.client.force_login(self.user)
        now = timezone.now()
        wrong_cards = self.cards[:2]
        for card in wrong_cards:
            CardReview.objects.create(user=self.user, card=card, is_correct=False, reviewed_at=now)
        CardReview.objects.create(user=self.user, card=self.cards[2], is_correct=True, reviewed_at=now)

        response = self._post_review()
        self.assertRedirects(response, reverse('flashcards:study'))
        self.assertEqual(len(self.client.session['session_cards']), 2)

        # answer both review cards
        for _ in range(2):
            response = self.client.get(reverse('flashcards:study'))
            self.assertEqual(response.status_code, 200)
            card_id = response.context['card'].pk
            response = self.client.post(
                reverse('flashcards:study'),
                {'card_id': card_id, 'is_correct': '1'},
            )

        self.assertEqual(response.status_code, 302)
        self.assertIn('study/results', response['Location'])

    def test_review_results_hides_study_again_button(self):
        self.client.force_login(self.user)
        session = self.client.session
        session['session_topic_id'] = None
        session['session_cards'] = [self.cards[0].pk]
        session['session_index'] = len(self.cards[:1])
        session['session_score'] = 0
        session['session_wrong_ids'] = []
        session.save()

        response = self.client.get(reverse('flashcards:study_results'))
        self.assertEqual(response.status_code, 200)
        study_start_url = reverse('flashcards:study_start')
        self.assertNotIn(study_start_url.encode(), response.content)

    def test_review_button_visible_when_missed_cards_exist(self):
        self.client.force_login(self.user)
        # start a regular session and answer one wrong
        self.client.post(reverse('flashcards:study_start'), {'topic_id': self.topic.pk})
        response = self.client.get(reverse('flashcards:study'))
        card_id = response.context['card'].pk
        self.client.post(reverse('flashcards:study'), {'card_id': card_id, 'is_correct': '0'})

        # answer remaining cards correctly to reach results
        while True:
            response = self.client.get(reverse('flashcards:study'))
            if response.status_code == 302:
                break
            card_id = response.context['card'].pk
            response = self.client.post(
                reverse('flashcards:study'), {'card_id': card_id, 'is_correct': '1'}
            )
            if response.status_code == 302 and 'results' in response['Location']:
                break

        response = self.client.get(reverse('flashcards:study_results'))
        study_review_url = reverse('flashcards:study_review')
        self.assertIn(study_review_url.encode(), response.content)

    def test_perfect_session_hides_review_button(self):
        # 1.4: After a perfect session the review button must be absent
        self.client.force_login(self.user)
        self.client.post(reverse('flashcards:study_start'), {'topic_id': self.topic.pk})
        while True:
            response = self.client.get(reverse('flashcards:study'))
            if response.status_code != 200:
                break
            card_id = response.context['card'].pk
            response = self.client.post(
                reverse('flashcards:study'), {'card_id': card_id, 'is_correct': '1'}
            )
            if response.status_code == 302 and 'results' in response['Location']:
                break

        response = self.client.get(reverse('flashcards:study_results'))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(reverse('flashcards:study_review').encode(), response.content)

    def test_topics_button_present_on_regular_and_review_results(self):
        # 1.6: Wybierz temat always visible on results — regular session
        self.client.force_login(self.user)
        self.client.post(reverse('flashcards:study_start'), {'topic_id': self.topic.pk})
        while True:
            response = self.client.get(reverse('flashcards:study'))
            if response.status_code != 200:
                break
            card_id = response.context['card'].pk
            response = self.client.post(
                reverse('flashcards:study'), {'card_id': card_id, 'is_correct': '1'}
            )
            if response.status_code == 302 and 'results' in response['Location']:
                break

        response = self.client.get(reverse('flashcards:study_results'))
        topics_url = reverse('flashcards:topics')
        self.assertIn(topics_url.encode(), response.content)

        # 1.6: Wybierz temat visible on review-session results too
        session = self.client.session
        session['session_topic_id'] = None
        session['session_cards'] = [self.cards[0].pk]
        session['session_index'] = 1
        session['session_score'] = 1
        session['session_wrong_ids'] = []
        session.save()

        response = self.client.get(reverse('flashcards:study_results'))
        self.assertIn(topics_url.encode(), response.content)
