
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Card, CardReview, Topic
from .session import SK

User = get_user_model()


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
        self.assertNotIn(SK.CARDS, session)

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
        session[SK.CARDS] = [1, 2, 3]
        session[SK.INDEX] = 1
        session[SK.SCORE] = 1
        session[SK.WRONG_IDS] = []
        session[SK.TOPIC_ID] = self.topic.pk
        session.save()

        self.client.get(reverse('flashcards:topics'))
        session = self.client.session
        self.assertNotIn(SK.CARDS, session)
        self.assertNotIn(SK.INDEX, session)
        self.assertNotIn(SK.SCORE, session)
        self.assertNotIn(SK.WRONG_IDS, session)
        self.assertNotIn(SK.TOPIC_ID, session)


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
        session[SK.LAST_WRONG_IDS] = [card.pk for card in wrong_cards]
        session.save()

        response = self._post_review()
        self.assertRedirects(response, reverse('flashcards:study'))
        self.assertEqual(len(self.client.session[SK.CARDS]), 2)

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
        session[SK.TOPIC_ID] = None
        session[SK.CARDS] = [self.cards[0].pk]
        session[SK.INDEX] = len(self.cards[:1])
        session[SK.SCORE] = 0
        session[SK.WRONG_IDS] = []
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
        session[SK.TOPIC_ID] = None
        session[SK.CARDS] = [self.cards[0].pk]
        session[SK.INDEX] = 1
        session[SK.SCORE] = 1
        session[SK.WRONG_IDS] = []
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
        self.assertEqual(self.client.session[SK.SCORE], 0)

    def test_cross_card_post_rejected_no_db_write(self):
        self.client.force_login(self.user)
        self._start_session()

        wrong_card_id = self.client.session[SK.CARDS][1]
        response = self.client.post(
            reverse('flashcards:study'),
            {'card_id': wrong_card_id, 'is_correct': '1'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CardReview.objects.count(), 0)
        self.assertEqual(self.client.session[SK.SCORE], 0)
        self.assertEqual(self.client.session[SK.INDEX], 0)

    def test_partial_session_missing_index_gets_redirect_not_500(self):
        self.client.force_login(self.user)
        session = self.client.session
        session[SK.CARDS] = [self.cards[0].pk]
        session.save()
        response = self.client.get(reverse('flashcards:study'))
        self.assertEqual(response.status_code, 302)

    def test_partial_session_missing_score_post_gets_redirect_not_500(self):
        self.client.force_login(self.user)
        session = self.client.session
        session[SK.CARDS] = [self.cards[0].pk]
        session[SK.INDEX] = 0
        session[SK.WRONG_IDS] = []
        session.save()
        response = self.client.post(
            reverse('flashcards:study'),
            {'card_id': self.cards[0].pk, 'is_correct': '1'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CardReview.objects.count(), 0)

    def test_session_index_out_of_bounds_get_redirects_to_results(self):
        self.client.force_login(self.user)
        session = self.client.session
        session[SK.CARDS] = [self.cards[0].pk]
        session[SK.INDEX] = 1
        session[SK.SCORE] = 0
        session[SK.WRONG_IDS] = []
        session.save()
        response = self.client.get(reverse('flashcards:study'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('study/results', response['Location'])

    def test_session_results_partial_keys_redirects(self):
        self.client.force_login(self.user)
        session = self.client.session
        session[SK.CARDS] = [self.cards[0].pk]
        session[SK.SCORE] = 1
        session[SK.WRONG_IDS] = []
        session.save()
        response = self.client.get(reverse('flashcards:study_results'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('topics', response['Location'])


@override_settings(CACHES={
    'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
})
class SessionStartRateLimitTests(TestCase):
    """session_start is rate-limited to 20/h per user (plan Phase 3).

    Forces LocMemCache so the counter works regardless of whether a local
    Redis is reachable — django-ratelimit's counter store is the same
    cache backend django-redis uses, and RATELIMIT_FAIL_OPEN would silently
    let every request through if the configured Redis were unreachable.
    """

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='ratelimituser', password='pass')
        self.topic = Topic.objects.create(name='Rate Limit Topic', slug='rate-limit-topic')
        Card.objects.create(topic=self.topic, question='Q', answer='A')
        self.client.force_login(self.user)

    def _start_session(self):
        return self.client.post(
            reverse('flashcards:study_start'),
            {'topic_id': self.topic.pk},
        )

    def test_21st_session_start_within_hour_returns_429(self):
        for _ in range(20):
            response = self._start_session()
            self.assertEqual(response.status_code, 302)

        response = self._start_session()
        self.assertEqual(response.status_code, 429)


class CardPermissionTests(TestCase):

    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='pass')
        self.other = User.objects.create_user(username='other', password='pass')
        self.staff = User.objects.create_user(username='staff', password='pass', is_staff=True)
        self.topic = Topic.objects.create(name='Perm Topic', slug='perm-topic')
        self.card = Card.objects.create(
            topic=self.topic, question='Owner Q', answer='Owner A', created_by=self.owner,
        )
        self.orphan = Card.objects.create(
            topic=self.topic, question='Orphan Q', answer='Orphan A', created_by=None,
        )

    def test_owner_can_get_edit(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('flashcards:card_edit', args=[self.card.pk]))
        self.assertEqual(response.status_code, 200)

    def test_owner_can_post_edit(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse('flashcards:card_edit', args=[self.card.pk]),
            {'topic': self.topic.pk, 'question': 'Updated Q', 'answer': 'Updated A'},
        )
        self.assertEqual(response.status_code, 302)
        self.card.refresh_from_db()
        self.assertEqual(self.card.question, 'Updated Q')

    def test_owner_can_get_delete(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('flashcards:card_delete', args=[self.card.pk]))
        self.assertEqual(response.status_code, 200)

    def test_owner_can_post_delete(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse('flashcards:card_delete', args=[self.card.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Card.objects.filter(pk=self.card.pk).exists())

    def test_non_owner_edit_returns_403(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse('flashcards:card_edit', args=[self.card.pk]))
        self.assertEqual(response.status_code, 403)

    def test_non_owner_delete_returns_403(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse('flashcards:card_delete', args=[self.card.pk]))
        self.assertEqual(response.status_code, 403)

    def test_staff_can_edit_others_card(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('flashcards:card_edit', args=[self.card.pk]))
        self.assertEqual(response.status_code, 200)

    def test_staff_can_delete_others_card(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('flashcards:card_delete', args=[self.card.pk]))
        self.assertEqual(response.status_code, 200)

    def test_non_staff_gets_403_on_orphan_edit(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse('flashcards:card_edit', args=[self.orphan.pk]))
        self.assertEqual(response.status_code, 403)

    def test_non_staff_gets_403_on_orphan_delete(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse('flashcards:card_delete', args=[self.orphan.pk]))
        self.assertEqual(response.status_code, 403)

    def test_staff_can_edit_orphan(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('flashcards:card_edit', args=[self.orphan.pk]))
        self.assertEqual(response.status_code, 200)

    def test_staff_can_delete_orphan(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('flashcards:card_delete', args=[self.orphan.pk]))
        self.assertEqual(response.status_code, 200)


class CardDetailViewTests(TestCase):

    def setUp(self):
        self.owner = User.objects.create_user(username='det_owner', password='pass')
        self.other = User.objects.create_user(username='det_other', password='pass')
        self.staff = User.objects.create_user(username='det_staff', password='pass', is_staff=True)
        self.topic = Topic.objects.create(name='Detail Topic', slug='detail-topic')
        self.card = Card.objects.create(
            topic=self.topic, question='Detail Q', answer='Detail A', created_by=self.owner,
        )

    def test_authenticated_user_gets_200(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse('flashcards:card_detail', args=[self.card.pk]))
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_user_is_redirected(self):
        response = self.client.get(reverse('flashcards:card_detail', args=[self.card.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_can_edit_true_for_owner(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('flashcards:card_detail', args=[self.card.pk]))
        self.assertTrue(response.context['can_edit'])

    def test_can_edit_true_for_staff(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('flashcards:card_detail', args=[self.card.pk]))
        self.assertTrue(response.context['can_edit'])

    def test_can_edit_false_for_non_owner(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse('flashcards:card_detail', args=[self.card.pk]))
        self.assertFalse(response.context['can_edit'])


class CardUpdateViewTests(TestCase):

    def setUp(self):
        self.owner = User.objects.create_user(username='upd_owner', password='pass')
        self.topic = Topic.objects.create(name='Update Topic', slug='update-topic')
        self.card = Card.objects.create(
            topic=self.topic, question='Original Q', answer='Original A', created_by=self.owner,
        )

    def test_get_prefills_form_with_existing_data(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('flashcards:card_edit', args=[self.card.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].initial.get('question') or
                         response.context['form']['question'].value(), 'Original Q')

    def test_valid_post_updates_and_redirects_to_detail(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse('flashcards:card_edit', args=[self.card.pk]),
            {'topic': self.topic.pk, 'question': 'New Q', 'answer': 'New A'},
        )
        self.assertRedirects(
            response, reverse('flashcards:card_detail', args=[self.card.pk])
        )
        self.card.refresh_from_db()
        self.assertEqual(self.card.question, 'New Q')

    def test_invalid_post_returns_200_with_form_errors(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse('flashcards:card_edit', args=[self.card.pk]),
            {'topic': self.topic.pk, 'question': '', 'answer': 'A'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)


class CardDeleteViewTests(TestCase):

    def setUp(self):
        self.owner = User.objects.create_user(username='del_owner', password='pass')
        self.topic = Topic.objects.create(name='Delete Topic', slug='delete-topic')
        self.card = Card.objects.create(
            topic=self.topic, question='Delete Q', answer='Delete A', created_by=self.owner,
        )

    def test_post_deletes_card_and_redirects_to_list(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse('flashcards:card_delete', args=[self.card.pk]))
        self.assertRedirects(response, reverse('flashcards:card_list'))

    def test_card_no_longer_exists_after_delete(self):
        self.client.force_login(self.owner)
        card_pk = self.card.pk
        self.client.post(reverse('flashcards:card_delete', args=[card_pk]))
        self.assertFalse(Card.objects.filter(pk=card_pk).exists())
