from django.urls import path

from config.urls import _rate_auth

from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', _rate_auth(views.RegisterView.as_view()), name='register'),
    path('verify/<str:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    path('complete-email/', views.complete_email, name='complete_email'),
]
