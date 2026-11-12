from django.urls import path
from . import quiz, timed, views, written

app_name = 'flashcards'

urlpatterns = [
    path('topics/', views.TopicsListView.as_view(), name='topics'),
    path('study/start/', views.session_start, name='study_start'),
    path('study/results/', views.session_results, name='study_results'),
    path('study/review/', views.study_review, name='study_review'),
    path('study/all/', views.study_all, name='study_all'),
    path('quiz/start/', quiz.quiz_start, name='quiz_start'),
    path('quiz/', quiz.quiz_play, name='quiz_play'),
    path('written/start/', written.written_start, name='written_start'),
    path('written/', written.written_play, name='written_play'),
    path('timed/start/', timed.timed_start, name='timed_start'),
    path('timed/', timed.timed_play, name='timed_play'),
    path('timed/<int:pk>/results/', timed.timed_results, name='timed_results'),
    path('', views.CardListView.as_view(), name='card_list'),
    path('create/', views.CardCreateView.as_view(), name='card_create'),
    path('study/', views.study_card, name='study'),
    path('<int:pk>/', views.CardDetailView.as_view(), name='card_detail'),
    path('<int:pk>/edit/', views.CardUpdateView.as_view(), name='card_edit'),
    path('<int:pk>/delete/', views.CardDeleteView.as_view(), name='card_delete'),
]
