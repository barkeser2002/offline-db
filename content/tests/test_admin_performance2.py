from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from content.models import Anime, Season, Episode

User = get_user_model()

class EpisodeAdminPerformanceTest(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser('admin_ep_test2', 'admin@example.com', 'password')
        self.client = Client()
        self.client.force_login(self.admin_user)

        self.anime = Anime.objects.create(title="Test Anime")
        self.season = Season.objects.create(anime=self.anime, number=1)

        for i in range(10):
            Episode.objects.create(season=self.season, number=i+1, title=f"Ep {i+1}")

    def test_admin_changelist_performance(self):
        url = reverse('admin:content_episode_changelist')

        self.client.get(url)

        # 1 auth, 1 session, 1 choices for season__anime filter, 2 counts, 1 main fetch = 6
        with self.assertNumQueries(6):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
