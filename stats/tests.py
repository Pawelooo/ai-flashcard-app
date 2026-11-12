from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone

from flashcards.models import CardReview

from .services import compute_study_stats
from .types import StudyStats

User = get_user_model()


class StudyStatsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', email='tester@example.com', password='pass')

    def _add_review(self, days_ago=0, is_correct=True):
        return CardReview.objects.create(
            user=self.user,
            reviewed_at=timezone.now() - timedelta(days=days_ago),
            is_correct=is_correct,
        )

    def test_no_reviews_returns_zero_stats(self):
        stats = compute_study_stats(self.user)
        self.assertEqual(stats.today_count, 0)
        self.assertIsNone(stats.correct_pct)
        self.assertEqual(stats.streak, 0)
        self.assertIsNone(stats.last_reviewed)

    def test_today_count_only_counts_today(self):
        self._add_review(days_ago=0)
        self._add_review(days_ago=0)
        self._add_review(days_ago=1)
        stats = compute_study_stats(self.user)
        self.assertEqual(stats.today_count, 2)

    def test_correct_pct_all_correct(self):
        self._add_review(is_correct=True)
        self._add_review(is_correct=True)
        stats = compute_study_stats(self.user)
        self.assertEqual(stats.correct_pct, 100)

    def test_correct_pct_half_correct(self):
        self._add_review(is_correct=True)
        self._add_review(is_correct=False)
        stats = compute_study_stats(self.user)
        self.assertEqual(stats.correct_pct, 50)

    def test_correct_pct_none_when_no_reviews_today(self):
        self._add_review(days_ago=1, is_correct=True)
        stats = compute_study_stats(self.user)
        self.assertIsNone(stats.correct_pct)

    def test_streak_one_day(self):
        self._add_review(days_ago=0)
        stats = compute_study_stats(self.user)
        self.assertEqual(stats.streak, 1)

    def test_streak_consecutive_days(self):
        self._add_review(days_ago=0)
        self._add_review(days_ago=1)
        self._add_review(days_ago=2)
        stats = compute_study_stats(self.user)
        self.assertEqual(stats.streak, 3)

    def test_streak_breaks_on_gap(self):
        self._add_review(days_ago=0)
        self._add_review(days_ago=2)
        stats = compute_study_stats(self.user)
        self.assertEqual(stats.streak, 1)

    def test_streak_zero_when_missed_today(self):
        self._add_review(days_ago=1)
        stats = compute_study_stats(self.user)
        self.assertEqual(stats.streak, 0)

    def test_last_reviewed_reflects_most_recent_review(self):
        self._add_review(days_ago=2)
        self._add_review(days_ago=0)
        stats = compute_study_stats(self.user)
        self.assertEqual(stats.last_reviewed, timezone.localdate())

    def test_last_reviewed_none_when_no_reviews(self):
        stats = compute_study_stats(self.user)
        self.assertIsNone(stats.last_reviewed)

    def test_next_review_is_today_when_never_reviewed(self):
        stats = compute_study_stats(self.user)
        self.assertEqual(stats.next_review, timezone.localdate())

    def test_next_review_is_tomorrow_after_review_today(self):
        self._add_review(days_ago=0)
        stats = compute_study_stats(self.user)
        self.assertEqual(stats.next_review, timezone.localdate() + timedelta(days=1))

    def test_next_review_is_today_when_last_review_was_yesterday(self):
        self._add_review(days_ago=1)
        stats = compute_study_stats(self.user)
        self.assertEqual(stats.next_review, timezone.localdate())

    def test_stats_isolated_per_user(self):
        other = User.objects.create_user(username='other', email='other@example.com', password='pass')
        self._add_review(days_ago=0)
        stats = compute_study_stats(other)
        self.assertEqual(stats.today_count, 0)
        self.assertEqual(stats.streak, 0)
        self.assertIsNone(stats.last_reviewed)

    def test_returns_study_stats_type(self):
        stats = compute_study_stats(self.user)
        self.assertIsInstance(stats, StudyStats)


class LeaderboardViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='viewer', email='viewer@example.com', password='pass')

    def _make_user(self, username):
        return User.objects.create_user(username=username, email=f'{username}@example.com', password='pass')

    def _add_correct_reviews(self, user, count):
        for _ in range(count):
            CardReview.objects.create(user=user, reviewed_at=timezone.now(), is_correct=True)

    def test_leaderboard_order(self):
        u1 = self._make_user('alice')
        u2 = self._make_user('bob')
        u3 = self._make_user('carol')
        self._add_correct_reviews(u1, 5)
        self._add_correct_reviews(u2, 3)
        self._add_correct_reviews(u3, 1)
        self.client.force_login(self.user)
        response = self.client.get('/stats/leaderboard/')
        lb = list(response.context['leaderboard'])
        self.assertEqual(lb[0].total_correct, 5)
        self.assertEqual(lb[1].total_correct, 3)
        self.assertEqual(lb[2].total_correct, 1)

    def test_leaderboard_tie_broken_alphabetically(self):
        bravo = self._make_user('bravo')
        alpha = self._make_user('alpha')
        self._add_correct_reviews(bravo, 2)
        self._add_correct_reviews(alpha, 2)
        self.client.force_login(self.user)
        response = self.client.get('/stats/leaderboard/')
        lb = list(response.context['leaderboard'])
        usernames = [e.username for e in lb]
        self.assertLess(usernames.index('alpha'), usernames.index('bravo'))

    def test_leaderboard_unauthenticated_redirects(self):
        response = self.client.get('/stats/leaderboard/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_leaderboard_top_10_limit(self):
        for i in range(11):
            u = self._make_user(f'user{i:02d}')
            self._add_correct_reviews(u, 1)
        self.client.force_login(self.user)
        response = self.client.get('/stats/leaderboard/')
        self.assertEqual(len(list(response.context['leaderboard'])), 10)


class LeaderboardHTMLTests(TestCase):
    """Verify rendered HTML for manual-verification criteria 2.2–2.5."""

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='htmluser', email='htmluser@example.com', password='pass')
        self.client.force_login(self.user)

    def _add_correct_reviews(self, user, count):
        for _ in range(count):
            CardReview.objects.create(user=user, reviewed_at=timezone.now(), is_correct=True)

    def test_navbar_ranking_link_present(self):
        # 2.2 — Navbar shows "Ranking" link pointing to /stats/leaderboard/
        response = self.client.get('/stats/leaderboard/')
        self.assertContains(response, '/stats/leaderboard/')
        self.assertContains(response, 'Ranking')

    def test_table_columns_present(self):
        # 2.3 — Table shows #, Użytkownik, Poprawne odpowiedzi columns
        response = self.client.get('/stats/leaderboard/')
        self.assertContains(response, 'Użytkownik')
        self.assertContains(response, 'Poprawne odpowiedzi')

    def test_current_user_row_highlighted(self):
        # 2.4 — Current user's row gets class="table-primary"
        self._add_correct_reviews(self.user, 2)
        response = self.client.get('/stats/leaderboard/')
        self.assertContains(response, 'table-primary')

    def test_navbar_active_on_leaderboard_page(self):
        # 2.5 — Navbar active state applied when on /stats/leaderboard/
        response = self.client.get('/stats/leaderboard/')
        content = response.content.decode()
        # Tylko zakładka Ranking jest aktywna (podkreślenie w nowym navbarze)
        header = content[:content.index('</header>')]
        self.assertIn('class="nav-link active" href="/stats/leaderboard/"', header)
        self.assertEqual(header.count('class="nav-link active"'), 1)


class LeaderboardRedisDownTests(TestCase):
    """Redis unreachable + IGNORE_EXCEPTIONS must fail open (plan Phase 1 desired end state)."""

    _unreachable_redis_caches = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://localhost:6399/0',
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'IGNORE_EXCEPTIONS': True,
                'SOCKET_CONNECT_TIMEOUT': 0.5,
                'SOCKET_TIMEOUT': 0.5,
            },
        }
    }

    def setUp(self):
        self.user = User.objects.create_user(username='redisdownviewer', email='redisdownviewer@example.com', password='pass')
        self.client.force_login(self.user)

    @override_settings(CACHES=_unreachable_redis_caches)
    def test_leaderboard_returns_200_when_redis_unavailable(self):
        response = self.client.get('/stats/leaderboard/')
        self.assertEqual(response.status_code, 200)


class StatsDashboardViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='viewer', email='statsviewer@example.com', password='pass')
        self.client.force_login(self.user)

    def test_page_returns_200(self):
        response = self.client.get('/stats/')
        self.assertEqual(response.status_code, 200)

    def test_redirects_unauthenticated_user(self):
        self.client.logout()
        response = self.client.get('/stats/')
        self.assertEqual(response.status_code, 302)

    def test_stats_present_in_context(self):
        response = self.client.get('/stats/')
        self.assertIn('stats', response.context)
        self.assertIsInstance(response.context['stats'], StudyStats)


class DashboardServiceTests(TestCase):
    def setUp(self):
        from flashcards.models import Card, Topic
        self.user = User.objects.create_user(username='dash', email='dash@example.com', password='pass')
        self.t1 = Topic.objects.create(name='Alpha', slug='alpha')
        self.t2 = Topic.objects.create(name='Beta', slug='beta')
        self.a = [Card.objects.create(topic=self.t1, question=f'A{i}', answer='x') for i in range(4)]
        self.b = [Card.objects.create(topic=self.t2, question=f'B{i}', answer='x') for i in range(2)]

    def _review(self, card, days_ago=0, ok=True, user=None):
        return CardReview.objects.create(
            user=user or self.user, card=card, is_correct=ok,
            reviewed_at=timezone.now() - timedelta(days=days_ago),
        )

    def _dash(self, days=30):
        from .services import compute_dashboard
        return compute_dashboard(self.user, days)

    def test_empty_user(self):
        d = self._dash()
        self.assertEqual((d['streak'], d['longest_streak'], d['mastered'], d['due']), (0, 0, 0, 6))
        self.assertIsNone(d['accuracy_pct'])
        self.assertEqual(d['chart']['points'], [])
        self.assertEqual(d['due_topics'], 2)

    def test_mastery_due_and_weakest(self):
        self._review(self.a[0])
        self._review(self.a[1])
        self._review(self.a[2], ok=False)
        self._review(self.b[0])
        self._review(self.b[1])
        d = self._dash()
        self.assertEqual((d['mastered'], d['total_cards'], d['due']), (4, 6, 2))
        self.assertEqual(d['due_topics'], 1)
        # Beta jest opanowana w 100% — nie trafia do „co powtórzyć najpierw”
        self.assertEqual([t.name for t in d['weakest']], ['Alpha'])
        self.assertEqual([(t.name, t.mastered_pct) for t in d['topics']], [('Beta', 100), ('Alpha', 50)])

    def test_progress_is_per_user(self):
        other = User.objects.create_user(username='o', email='o@example.com', password='pass')
        for c in self.a:
            self._review(c, user=other)
        self.assertEqual(self._dash()['mastered'], 0)

    def test_longest_streak_and_accuracy_window(self):
        for days in (0, 1, 5, 6, 7, 8):
            self._review(self.a[0], days_ago=days, ok=True)
        self._review(self.a[1], days_ago=20, ok=False)  # poza oknem 14 dni
        self._review(self.a[1], days_ago=0, ok=False)
        d = self._dash()
        self.assertEqual(d['streak'], 2)
        self.assertEqual(d['longest_streak'], 4)
        self.assertEqual(d['accuracy_pct'], round(6 / 7 * 100))

    def test_series_gaps_split_the_line(self):
        self._review(self.a[0], days_ago=0)
        self._review(self.a[0], days_ago=1)
        self._review(self.a[0], days_ago=5, ok=False)
        d = self._dash(14)
        self.assertEqual(len(d['series']), 14)
        self.assertEqual(len(d['chart']['points']), 3)
        self.assertEqual(len(d['chart']['polylines']), 2)  # luka między 5 a 1 dniem temu
        self.assertEqual(d['series'][-1]['pct'], 100)
        self.assertEqual(d['range_avg_pct'], 67)

    def test_svg_coordinates_use_dot_decimal(self):
        self._review(self.a[0])
        point = self._dash()['chart']['points'][0]
        float(point['x'])
        float(point['y'])
        self.assertNotIn(',', point['x'] + point['y'])

    def test_heatmap_shape_levels_and_future(self):
        for _ in range(4):
            self._review(self.a[0], days_ago=0)
        self._review(self.a[1], days_ago=3)
        heat = self._dash()['heatmap']
        self.assertEqual(len(heat), 12)
        self.assertTrue(all(len(week) == 7 for week in heat))
        cells = {c['date']: c for week in heat for c in week}
        today = timezone.localdate()
        self.assertEqual(cells[today]['level'], 4)
        self.assertEqual(cells[today - timedelta(days=3)]['level'], 1)
        self.assertTrue(all(c['future'] for c in cells.values() if c['date'] > today))


class DashboardPageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='paneluser', email='panel@example.com', password='pass')
        self.client.force_login(self.user)

    def test_range_param(self):
        self.assertEqual(self.client.get('/stats/').context['dash']['range_days'], 30)
        self.assertEqual(self.client.get('/stats/?range=14').context['dash']['range_days'], 14)
        self.assertEqual(self.client.get('/stats/?range=999').context['dash']['range_days'], 30)

    def test_greeting_and_active_tab(self):
        content = self.client.get('/stats/').content.decode()
        self.assertIn('Cześć, paneluser', content)
        self.assertIn('class="nav-link active" href="/stats/"', content)
