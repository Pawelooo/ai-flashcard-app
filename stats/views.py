from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from .services import compute_study_stats


class StatsDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'stats/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['stats'] = compute_study_stats(self.request.user)
        return ctx
