from django.urls import path
from . import views

app_name = 'chess_game'

urlpatterns = [
    # project-3
    # Main pages
    path('', views.home_view, name='home'),
    path('play/', views.play_solo_view, name='play_solo'),
    path('join/', views.join_view, name='join'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('history/', views.history_view, name='history'),
    path('rules/', views.rules_view, name='rules'),
    path('about/', views.about_view, name='about'),
    
    # Game functionality
    path('game/', views.game_view, name='game'),
    path('challenge/<int:user_id>/', views.challenge_user, name='challenge_user'),
    path('challenge/<int:challenge_id>/accept/', views.accept_challenge, name='accept_challenge'),
    path('challenge/<int:challenge_id>/decline/', views.decline_challenge, name='decline_challenge'),
    path('move/', views.make_move, name='make_move'),
    path('resign/', views.resign_game, name='resign_game'),
]
