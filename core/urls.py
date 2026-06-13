from django.urls import path
from . import views
urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('game_validate', views.game_validate, name='game_validate'),
    path('start_game/<int:level>/', views.start_game, name='start_game'),
    ]