from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from .services import compute_dashboard, compute_study_stats, get_leaderboard, get_timed_leaderboard


class StatsDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'stats/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['stats'] = compute_study_stats(self.request.user)
        range_days = 14 if self.request.GET.get('range') == '14' else 30
        ctx['dash'] = compute_dashboard(self.request.user, range_days)
        user = self.request.user
        ctx['greeting_name'] = user.first_name or user.username or (user.email or '').split('@')[0]
        return ctx


class LeaderboardView(LoginRequiredMixin, TemplateView):
    template_name = 'stats/leaderboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tab = 'timed' if self.request.GET.get('tab') == 'timed' else 'total'
        ctx['tab'] = tab
        ctx['leaderboard'] = get_timed_leaderboard() if tab == 'timed' else get_leaderboard()
        return ctx
