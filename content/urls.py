from django.urls import path
from .views import KeyServeView, player_view, home_view, anime_detail, SubscribeAnimeAPIView, search_view

urlpatterns = [
    path('', home_view, name='home'),
    path('search/', search_view, name='search'),
    path('anime/<int:pk>/', anime_detail, name='anime_detail'),
    path('api/anime/<int:pk>/subscribe/', SubscribeAnimeAPIView.as_view(), name='anime-subscribe'),
    path('watch/<int:episode_id>/', player_view, name='watch'),
    path('api/key/<str:key_token>/', KeyServeView.as_view(), name='video-key'),
]
