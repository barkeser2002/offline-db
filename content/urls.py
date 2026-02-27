from django.urls import path
from .views import KeyServeView
# from .views import (
#     player_view, home_view, anime_detail,
#     SubscribeAnimeAPIView, search_view, create_watch_party, watch_party_detail
# )

from django.urls import include

urlpatterns = [
    # API for serving HLS keys securely
    path('api/key/<uuid:pk>/', KeyServeView.as_view(), name='video-key'),

    # Review API routes
    path('api/content/', include('content.api.urls')),

    # The following views are currently missing or broken.
    # We comment them out to prevent ImportError on startup, but keep them for reference.
    # path('', home_view, name='home'),
    # path('search/', search_view, name='search'),
    # path('anime/<int:pk>/', anime_detail, name='anime_detail'),
    # path('api/anime/<int:pk>/subscribe/', SubscribeAnimeAPIView.as_view(), name='anime-subscribe'),
    # path('watch/<int:episode_id>/', player_view, name='watch'),

    # Watch Party
    # path('watch-party/create/<int:episode_id>/', create_watch_party, name='create_watch_party'),
    # path('watch-party/<uuid:uuid>/', watch_party_detail, name='watch_party_detail'),
]
