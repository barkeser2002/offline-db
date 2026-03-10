from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from users.models import User
from content.models import Anime, Season, Episode
from django.core.cache import cache
import time

class APIRateLimitTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        cache.clear() # Clear cache to reset rate limits

    def test_login_rate_limit(self):
        url = reverse('token_obtain_pair')
        data = {'username': 'testuser', 'password': 'password123'}

        # login throttle is 5/minute
        for i in range(5):
            response = self.client.post(url, data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 6th should fail
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('Retry-After', response.headers)

    def test_watchlog_create_rate_limit(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('watch-history-list')

        # watchlog throttle is 10/minute
        for i in range(10):
            # Create a new episode for each log to avoid potential unique constraints or 400s
            anime = Anime.objects.create(title=f"Test Anime {i}")
            season = Season.objects.create(anime=anime, number=1)
            episode = Episode.objects.create(season=season, number=1)
            data = {'episode': episode.id, 'watch_time': 100, 'duration': 1200}

            response = self.client.post(url, data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 11th should fail
        anime = Anime.objects.create(title=f"Test Anime 11")
        season = Season.objects.create(anime=anime, number=1)
        episode = Episode.objects.create(season=season, number=1)
        data = {'episode': episode.id, 'watch_time': 100, 'duration': 1200}

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('Retry-After', response.headers)

    def test_review_create_rate_limit(self):
        self.client.force_authenticate(user=self.user)
        url = '/api/content/reviews/'

        # review throttle is 5/hour
        for i in range(5):
            anime = Anime.objects.create(title=f"Test Review Anime {i}")
            data = {'anime': anime.id, 'rating': 8, 'text': 'Good'}

            response = self.client.post(url, data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 6th should be throttled
        anime = Anime.objects.create(title=f"Test Review Anime 6")
        data = {'anime': anime.id, 'rating': 8, 'text': 'Good'}

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('Retry-After', response.headers)
