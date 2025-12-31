from django.urls import re_path

from . import consumers

# project-3
websocket_urlpatterns = [
    re_path(r'^ws/lobby/$', consumers.LobbyConsumer.as_asgi()),
    re_path(r'^ws/game/(?P<game_id>\d+)/$', consumers.GameConsumer.as_asgi()),
]

