"""
file template picked from django channels documentation
https://channels.readthedocs.io/en/stable/topics/routing.html#routing-configurations

"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.conf import settings
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler  # project-3

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chess_project.settings')

django_asgi_app = get_asgi_application()

if settings.DEBUG:
    django_asgi_app = ASGIStaticFilesHandler(django_asgi_app)  # project-3

from chess_game import routing  # works after get_asgi_application() runs, otherwise settings not configured error

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns
        )
    ),
})
