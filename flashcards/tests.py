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
        # Perfect session leaves no last_wrong_ids in session — same as no history
        self.client.force_login(self.user)
        response = self._post_review()
        self.assertRedirects(response, reverse('flashcards:topics'))
        msgs = list(response.wsgi_request._messages)
        self.assertTrue(any(m.level_tag == 'warning' for m in msgs))

    def test_review_session_happy_path(self):
        self.client.force_login(self.user)
        wrong_cards = self.cards[:2]

        session = self.client.session
        session['last_wrong_ids'] = [card.pk for card in wrong_cards]
        session.save()

        response = self._post_review()
        self.assertRedirects(response, reverse('flashcards:study'))
        self.assertEqual(len(self.client.session['session_cards']), 2)

        # 1.3: first study GET must show "Karta 1 z 2" (N = missed-card count)
        response = self.client.get(reverse('flashcards:study'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Karta 1 z 2')
        card_id = response.context['card'].pk
        self.client.post(reverse('flashcards:study'), {'card_id': card_id, 'is_correct': '1'})

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

    def test_e2e_full_review_flow(self):
        # 2.2: regular session with 1 wrong → review → results: score correct, buttons correct
        self.client.force_login(self.user)

        # regular session: answer card 0 wrong, rest correct
        self.client.post(reverse('flashcards:study_start'), {'topic_id': self.topic.pk})
        wrong_card_id = None
        cards_answered = 0
        while cards_answered < len(self.cards):
            response = self.client.get(reverse('flashcards:study'))
            if response.status_code != 200:
                break
            card_id = response.context['card'].pk
            is_correct = '0' if wrong_card_id is None else '1'
            if wrong_card_id is None:
                wrong_card_id = card_id
            response = self.client.post(
                reverse('flashcards:study'), {'card_id': card_id, 'is_correct': is_correct}
            )
            cards_answered += 1
            if response.status_code == 302 and 'results' in response['Location']:
                break

        # get results — confirms missed_cards has the one wrong card
        results = self.client.get(reverse('flashcards:study_results'))
        self.assertEqual(results.status_code, 200)
        self.assertEqual(len(results.context['missed_cards']), 1)

        # start review session
        response = self.client.post(reverse('flashcards:study_review'))
        self.assertRedirects(response, reverse('flashcards:study'))
        self.assertEqual(len(self.client.session['session_cards']), 1)

        # review card: shows "Karta 1 z 1", is the missed card
        response = self.client.get(reverse('flashcards:study'))
        self.assertContains(response, 'Karta 1 z 1')
        card_id = response.context['card'].pk
        self.assertEqual(card_id, wrong_card_id)
        self.client.post(reverse('flashcards:study'), {'card_id': card_id, 'is_correct': '1'})

        # review results: score=1/1, study-again absent, topics present
        results = self.client.get(reverse('flashcards:study_results'))
        self.assertEqual(results.status_code, 200)
        self.assertEqual(results.context['score'], 1)
        self.assertEqual(results.context['total'], 1)
        self.assertNotIn(reverse('flashcards:study_start').encode(), results.content)
        self.assertIn(reverse('flashcards:topics').encode(), results.content)


class SessionHardeningTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='hardenuser', password='pass')
        self.topic = Topic.objects.create(name='Hardening Topic', slug='hardening-topic')
        self.cards = [
            Card.objects.create(topic=self.topic, question=f'HQ{i}', answer=f'HA{i}')
            for i in range(3)
        ]

    def _start_session(self):
        return self.client.post(
            reverse('flashcards:study_start'),
            {'topic_id': self.topic.pk},
        )

    def test_session_score_matches_cardreview_db(self):
        self.client.force_login(self.user)
        self._start_session()

        for is_correct in ['1', '0', '1']:
            response = self.client.get(reverse('flashcards:study'))
            self.assertEqual(response.status_code, 200)
            card_id = response.context['card'].pk
            self.client.post(
                reverse('flashcards:study'),
                {'card_id': card_id, 'is_correct': is_correct},
            )

        response = self.client.get(reverse('flashcards:study_results'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['score'], 2)
        self.assertEqual(CardReview.objects.count(), 3)
        self.assertEqual(CardReview.objects.filter(is_correct=True).count(), 2)
        self.assertEqual(CardReview.objects.filter(is_correct=False).count(), 1)

    def test_missing_is_correct_field_counts_as_incorrect(self):
        self.client.force_login(self.user)
        self._start_session()

        response = self.client.get(reverse('flashcards:study'))
        self.assertEqual(response.status_code, 200)
        card_id = response.context['card'].pk

        response = self.client.post(
            reverse('flashcards:study'),
            {'card_id': card_id},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(CardReview.objects.last().is_correct)
        self.assertEqual(self.client.session['session_score'], 0)

    def test_cross_card_post_rejected_no_db_write(self):
        self.client.force_login(self.user)
        self._start_session()

        wrong_card_id = self.client.session['session_cards'][1]
        response = self.client.post(
            reverse('flashcards:study'),
            {'card_id': wrong_card_id, 'is_correct': '1'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CardReview.objects.count(), 0)
        self.assertEqual(self.client.session['session_score'], 0)
        self.assertEqual(self.client.session['session_index'], 0)
