from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient
import uuid
import shutil
import os
from django.conf import settings
from .models import Anime, Season, Episode, VideoFile
from .tasks import encode_episode

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


class CacheTests(TestCase):
    def setUp(self):
        self.anime = Anime.objects.create(title="Cache Anime")
        self.season = Season.objects.create(anime=self.anime, number=1, title="Season 1")
        self.episode = Episode.objects.create(season=self.season, number=1, title="Ep 1")
        cache.clear()

    def test_home_cache_usage(self):
        # First request should populate cache
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(cache.get('home_latest_episodes'))

        # Verify content matches
        cached_episodes = cache.get('home_latest_episodes')
        # There might be other episodes from other tests if DB isn't isolated properly,
        # but TestCase wraps in transaction.
        # However, we should check if our episode is in the list.
        episode_ids = [e.id for e in cached_episodes]
        self.assertIn(self.episode.id, episode_ids)

    def test_cache_invalidation(self):
        # Populate cache
        self.client.get(reverse('home'))
        self.assertIsNotNone(cache.get('home_latest_episodes'))

        # Create new episode
        Episode.objects.create(season=self.season, number=2, title="Ep 2")

        # Cache should be cleared
        self.assertIsNone(cache.get('home_latest_episodes'))

        # Next request should repopulate with new data
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        cached_episodes = cache.get('home_latest_episodes')
        # Should now have at least 2 episodes
        self.assertGreaterEqual(len(cached_episodes), 2)

class TaskTests(TestCase):
    def setUp(self):
        self.anime = Anime.objects.create(title="Task Anime")
        self.season = Season.objects.create(anime=self.anime, number=1)
        self.episode = Episode.objects.create(season=self.season, number=1)

    def test_encode_episode_mock(self):
        # Register cleanup first
        output_dir = os.path.join(settings.MEDIA_ROOT, 'videos', str(self.episode.id))

        def cleanup():
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)
        self.addCleanup(cleanup)

        # Ensure we are not using real libtorrent
        # The mock logic in tasks.py should handle this
        result = encode_episode(self.episode.id, "magnet:?xt=urn:btih:dummy")
        self.assertIn("Successfully encoded", result)

        # Check if VideoFile was created
        self.assertTrue(VideoFile.objects.filter(episode=self.episode).exists())
        video = VideoFile.objects.get(episode=self.episode)
        self.assertEqual(video.quality, '1080p')
        self.assertTrue(video.hls_path.endswith('index.m3u8'))
