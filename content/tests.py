from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
import uuid
from .models import Anime, Season, Episode, VideoFile

User = get_user_model()

class ContentTests(TestCase):
    def setUp(self):
        self.anime = Anime.objects.create(title="Test Anime")
        self.season = Season.objects.create(anime=self.anime, number=1, title="Season 1")
        self.episode = Episode.objects.create(season=self.season, number=1, title="Test Ep")

    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_watch_view(self):
        response = self.client.get(reverse('watch', args=[self.episode.id]))
        self.assertEqual(response.status_code, 200)

class KeyServeTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.anime = Anime.objects.create(title="Test Anime")
        self.season = Season.objects.create(anime=self.anime, number=1, title="Season 1")
        self.episode = Episode.objects.create(season=self.season, number=1, title="Test Ep")
        self.video = VideoFile.objects.create(
            episode=self.episode,
            quality='1080p',
            hls_path='test.m3u8',
            encryption_key=uuid.uuid4().hex
        )
        # Assuming the URL pattern is /api/key/<str:key_token>/
        # content/urls.py name is 'video-key'
        self.url = reverse('video-key', args=[self.video.encryption_key])

    def test_key_access_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), self.video.encryption_key)

    def test_key_access_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
