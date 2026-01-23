from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from users.models import WatchLog
from content.models import Anime, Season, Episode

User = get_user_model()

class WatchLogAdminPerformanceTest(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'password')
        self.client = Client()
        self.client.force_login(self.admin_user)

        # Create data
        self.anime = Anime.objects.create(title="Test Anime")
        self.season = Season.objects.create(anime=self.anime, number=1)

        # Create 10 WatchLogs
        for i in range(10):
            user = User.objects.create_user(username=f'user{i}', password='password')
            episode = Episode.objects.create(season=self.season, number=i+1, title=f"Ep {i+1}")
            WatchLog.objects.create(user=user, episode=episode, duration=100)

    def test_admin_changelist_performance(self):
        url = reverse('admin:users_watchlog_changelist')

        # Initial request to warm up
        self.client.get(url)

        # We expect efficient querying.
        # 1. Session check
        # 2. User auth
        # 3. Count
        # 4. Count (sometimes duplicate or distinct check)
        # 5. The Main Query with Joins
        # Total around 5-6 queries.
        # Without optimization (or with bad optimization), it would be 25+ queries.
        with self.assertNumQueries(5):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
