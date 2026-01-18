from django.test import TestCase
from .models import Anime, Episode
from django.urls import reverse

class ContentTests(TestCase):
    def setUp(self):
        self.anime = Anime.objects.create(title="Test Anime")
        self.episode = Episode.objects.create(anime=self.anime, number=1, title="Test Ep")

    def test_anime_slug(self):
        self.assertEqual(self.anime.slug, "test-anime")

    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_watch_view(self):
        response = self.client.get(reverse('watch', args=[self.episode.id]))
        self.assertEqual(response.status_code, 200)
