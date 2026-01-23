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
from apps.watchparty.consumers import WatchPartyConsumer

from apps.watchparty import routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns + [
                path("ws/chat/<str:room_name>/", ChatConsumer.as_asgi()), # Keeping legacy chat for now if needed, or remove? 
                # Better to keep existing routes to avoid breaking other parts if any.
                # However, the user asked for apps/watchparty as "The" module.
            ]
        )
    ),
})
