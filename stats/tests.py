from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from flashcards.models import CardReview

from .services import compute_study_stats
from .types import StudyStats

User = get_user_model()


class StudyStatsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='pass')

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
        other = User.objects.create_user(username='other', password='pass')
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
        self.user = User.objects.create_user(username='viewer', password='pass')

    def _make_user(self, username):
        return User.objects.create_user(username=username, password='pass')

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
        self.user = User.objects.create_user(username='htmluser', password='pass')
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
        # The active class block wraps the Ranking link on this path
        self.assertIn('bg-primary bg-opacity-25', content[:content.find('bi-trophy') + 500])


class StatsDashboardViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='viewer', password='pass')
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
