from django.urls import path
from . import views

app_name = 'flashcards'

urlpatterns = [
    path('topics/', views.TopicsListView.as_view(), name='topics'),
    path('study/start/', views.session_start, name='study_start'),
    path('study/results/', views.session_results, name='study_results'),
    path('study/review/', views.study_review, name='study_review'),
    path('', views.CardListView.as_view(), name='card_list'),
    path('create/', views.CardCreateView.as_view(), name='card_create'),
    path('study/', views.study_card, name='study'),
    path('<int:pk>/', views.CardDetailView.as_view(), name='card_detail'),
    path('<int:pk>/edit/', views.CardUpdateView.as_view(), name='card_edit'),
    path('<int:pk>/delete/', views.CardDeleteView.as_view(), name='card_delete'),
]
