from django.test import TestCase
from django.urls import reverse
from content.models import Anime, Season, Episode, Genre

class SitemapTests(TestCase):
    def setUp(self):
        self.genre = Genre.objects.create(name="Action", slug="action")
        self.anime = Anime.objects.create(title="Test Anime")
        self.anime.genres.add(self.genre)
        self.season = Season.objects.create(anime=self.anime, number=1)
        self.episode = Episode.objects.create(season=self.season, number=1, title="Test Episode")

    def test_sitemap_status_code(self):
        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)

    def test_sitemap_content(self):
        response = self.client.get('/sitemap.xml')
        content = response.content.decode('utf-8')

        # Check if Anime URL is present
        self.assertIn(self.anime.get_absolute_url(), content)

        # Check if Episode URL is present
        self.assertIn(self.episode.get_absolute_url(), content)

        # Check if Genre URL is present
        self.assertIn(self.genre.get_absolute_url(), content)

    def test_sitemap_structure(self):
        response = self.client.get('/sitemap.xml')
        content = response.content.decode('utf-8')

        # Check for standard XML sitemap tags
        self.assertIn('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"', content)
        self.assertIn('<loc>', content)
