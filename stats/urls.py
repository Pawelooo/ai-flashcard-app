from django.urls import path

from .views import StatsDashboardView

app_name = 'stats'

urlpatterns = [
    path('', StatsDashboardView.as_view(), name='dashboard'),
]
