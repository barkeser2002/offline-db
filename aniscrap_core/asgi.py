"""
ASGI config for AniScrap project.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aniscrap_core.settings")

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from core.consumers import ChatConsumer
from users.consumers import NotificationConsumer
from content.consumers import WatchPartyConsumer

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("ws/watch-party/<str:room_name>/", WatchPartyConsumer.as_asgi()),
            path("ws/chat/<str:room_name>/", ChatConsumer.as_asgi()),
            path("ws/notifications/", NotificationConsumer.as_asgi()),
        ])
    ),
})
