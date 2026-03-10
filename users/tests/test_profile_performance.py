from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from users.models import UserBadge, Badge, WatchLog
from content.models import Anime, Episode, Season

User = get_user_model()

class ProfilePerformanceTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='test_user', password='password')
        self.client.force_authenticate(user=self.user)

        badge = Badge.objects.create(name='Test Badge', slug='test')
        UserBadge.objects.create(user=self.user, badge=badge)

        self.anime = Anime.objects.create(title="Test Anime")
        self.season = Season.objects.create(anime=self.anime, number=1)
        self.episode = Episode.objects.create(season=self.season, number=1, title="Test Ep")
        WatchLog.objects.create(user=self.user, episode=self.episode, duration=100)

    def test_profile_query_counts(self):
        url = reverse('user-profile')
        with self.assertNumQueries(2):
            # 1 for user badges
            # 1 for watchlog
            # user query shouldn't exist if auth is mocked right or we'll adjust assertions
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.data['recent_history']), 1)
