from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from content.models import Anime, Season, Episode

User = get_user_model()

class WatchPartySecurityTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.user = User.objects.create_user(username='spammer', password='password')
        self.anime = Anime.objects.create(title="Test Anime")
        self.season = Season.objects.create(anime=self.anime, number=1)
        self.episode = Episode.objects.create(season=self.season, number=1)
        self.url = reverse('create_watch_party', args=[self.episode.id])

    def test_create_watch_party_rate_limit(self):
        self.client.login(username='spammer', password='password')

        # Limit is 5 per 300 seconds
        for i in range(5):
            response = self.client.get(self.url)
            # Should redirect to the created party
            self.assertEqual(response.status_code, 302, f"Request {i+1} failed with {response.status_code}")

        # 6th request should fail with 403 Forbidden
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_create_watch_party_rate_limit_unauthenticated(self):
        # Even unauthenticated requests should count towards the IP limit
        # This prevents unauthenticated users from spamming the server even if they get 302s
        cache.clear() # Reset cache for this test

        for i in range(5):
            response = self.client.get(self.url)
            # Should redirect to login
            self.assertEqual(response.status_code, 302, f"Request {i+1} failed with {response.status_code}")
            self.assertIn('/accounts/login/', response.url)

        # 6th request should fail with 403 Forbidden because rate limit is per IP
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
