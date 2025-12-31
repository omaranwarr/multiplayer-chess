from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'games', api_views.GameViewSet, basename='game')
router.register(r'challenges', api_views.GameChallengeViewSet, basename='challenge')

urlpatterns = [
    path('auth/register/', api_views.api_register, name='api-register'),
    path('auth/login/', api_views.api_login, name='api-login'),
    path('auth/logout/', api_views.api_logout, name='api-logout'),
    path('auth/current-user/', api_views.api_current_user, name='api-current-user'),
    
    path('players/available/', api_views.api_available_players, name='api-available-players'),
    path('games/history/', api_views.api_game_history, name='api-game-history'),
    path('solo/', api_views.api_solo_play, name='api-solo-play'),
    
    path('', include(router.urls)),
]

