from django.urls import path

from .views import LeaderboardView, StatsDashboardView

app_name = 'stats'

urlpatterns = [
    path('', StatsDashboardView.as_view(), name='dashboard'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
]
