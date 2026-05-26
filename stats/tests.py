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
