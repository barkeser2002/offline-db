from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/watch-party/(?P<room_name>[0-9a-f-]+)/$', consumers.WatchPartyConsumer.as_asgi()),
]
