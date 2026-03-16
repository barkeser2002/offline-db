from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from content.models import Anime, Genre, Season, Episode, VideoFile

User = get_user_model()

class ContentViewsPerformanceTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='password')

        # Create genres
        self.genre1, _ = Genre.objects.get_or_create(name="Action", slug="action")
        self.genre2, _ = Genre.objects.get_or_create(name="Adventure", slug="adventure")

        # Create anime entries
        for i in range(15):
            anime = Anime.objects.create(title=f"Anime {i}")
            anime.genres.add(self.genre1, self.genre2)

            season = Season.objects.create(anime=anime, number=1, title="Season 1")
            episode = Episode.objects.create(season=season, number=1, title="Ep 1")
            VideoFile.objects.create(episode=episode, quality='720p', hls_path=f"path/to/video{i}.m3u8", encryption_key="dummy_key")

    def test_anime_list_queries(self):
        url = reverse('anime-list')
        self.client.get(url) # warmup

        with self.assertNumQueries(3):
            self.client.get(url)

    def test_anime_detail_queries(self):
        anime = Anime.objects.first()
        url = reverse('anime-detail', args=[anime.id])
        self.client.get(url) # warmup

        with self.assertNumQueries(7):
            self.client.get(url)

    def test_episode_list_queries(self):
        url = reverse('episode-list')
        self.client.get(url) # warmup

        with self.assertNumQueries(4):
            self.client.get(url)

    def test_episode_detail_queries(self):
        episode = Episode.objects.first()
        url = reverse('episode-detail', args=[episode.id])
        self.client.get(url) # warmup

        with self.assertNumQueries(3):
            self.client.get(url)

    def test_home_view_queries(self):
        url = reverse('home-list')
        self.client.get(url) # warmup

        with self.assertNumQueries(6):
            self.client.get(url)
