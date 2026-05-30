from django.urls import path
from . import views

app_name = 'flashcards'

urlpatterns = [
    path('topics/', views.TopicsListView.as_view(), name='topics'),
    path('study/start/', views.session_start, name='study_start'),
    path('study/results/', views.session_results, name='study_results'),
    path('', views.CardListView.as_view(), name='card_list'),
    path('create/', views.CardCreateView.as_view(), name='card_create'),
    path('study/', views.study_card, name='study'),
]
