from django.urls import path
from . import views

app_name = 'flashcards'

urlpatterns = [
    path('', views.CardListView.as_view(), name='card_list'),
    path('create/', views.CardCreateView.as_view(), name='card_create'),
    path('study/', views.study, name='study'),
]
