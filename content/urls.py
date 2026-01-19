from django.urls import path
from .views import KeyServeView, player_view, home_view

urlpatterns = [
    path('', home_view, name='home'),
    path('watch/<int:episode_id>/', player_view, name='watch'),
    path('api/key/<str:key_token>/', KeyServeView.as_view(), name='video-key'),
]
