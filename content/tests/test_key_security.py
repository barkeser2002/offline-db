from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
import uuid
from content.models import Anime, Season, Episode, VideoFile

User = get_user_model()

class KeySecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_free = User.objects.create_user(username='free_user', password='password')
        self.user_premium = User.objects.create_user(username='premium_user', password='password', is_premium=True)

        self.anime = Anime.objects.create(title="Test Anime")
        self.season = Season.objects.create(anime=self.anime, number=1, title="Season 1")
        self.episode = Episode.objects.create(season=self.season, number=1, title="Test Ep")

        # Create 1080p video (Premium only)
        self.video_1080p = VideoFile.objects.create(
            episode=self.episode,
            quality='1080p',
            hls_path='test_1080p.m3u8',
            encryption_key=uuid.uuid4().hex
        )

        # Create 720p video (Free)
        self.video_720p = VideoFile.objects.create(
            episode=self.episode,
            quality='720p',
            hls_path='test_720p.m3u8',
            encryption_key=uuid.uuid4().hex
        )

    def test_key_access_unauthenticated(self):
        """Unauthenticated users should get 401 Unauthorized"""
        # Using ID now, not key
        url = reverse('video-key', args=[self.video_720p.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_key_access_authenticated_free_720p(self):
        """Free users should access 720p keys"""
        self.client.force_login(self.user_free)
        # Using ID
        url = reverse('video-key', args=[self.video_720p.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), self.video_720p.encryption_key)

    def test_key_access_authenticated_free_1080p(self):
        """Free users should NOT access 1080p keys"""
        self.client.force_login(self.user_free)
        url = reverse('video-key', args=[self.video_1080p.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertIn('Premium required', response.data['detail'])

    def test_key_access_authenticated_premium_1080p(self):
        """Premium users should access 1080p keys"""
        self.client.force_login(self.user_premium)
        url = reverse('video-key', args=[self.video_1080p.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), self.video_1080p.encryption_key)
