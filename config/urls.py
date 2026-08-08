"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.db import connection as db_connection
from django.http import HttpResponse
from django.urls import include, path
from django.views.generic import TemplateView
from django.shortcuts import redirect
from django_ratelimit.decorators import ratelimit


class HomeView(TemplateView):
    template_name = 'home.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('flashcards:topics')
        return super().dispatch(request, *args, **kwargs)


def _healthz(request):
    try:
        db_connection.ensure_connection()
    except Exception:
        return HttpResponse('db error', status=503)
    return HttpResponse('ok')


def handler429(request, exception=None):
    return HttpResponse('Zbyt wiele prób. Poczekaj chwilę i spróbuj ponownie.', status=429)


_rate_auth = ratelimit(key='ip', rate='10/m', block=True, method=['POST'])

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('healthz/', lambda request: _healthz(request), name='healthz'),
    path('admin/', admin.site.urls),
    path('accounts/login/', _rate_auth(auth_views.LoginView.as_view()), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/', include('accounts.urls')),
    path('flashcards/', include('flashcards.urls')),
    path('stats/', include('stats.urls')),
]
