from django.test import TestCase, Client
from django.urls import reverse
from content.models import Anime

class SeoTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.anime = Anime.objects.create(
            title="Test Anime",
            synopsis="This is a test anime synopsis.",
            cover_image="http://example.com/cover.jpg",
            type="TV"
        )

    def test_robots_txt(self):
        url = '/robots.txt'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertContains(response, "User-agent: *")
        self.assertContains(response, "Sitemap: https://aniscrap.com/sitemap.xml")

    def test_anime_detail_meta_tags(self):
        url = reverse('anime_detail', args=[self.anime.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'<meta property="og:title" content="{self.anime.title}"')
        self.assertContains(response, f'<meta property="og:image" content="{self.anime.cover_image}"')
        self.assertContains(response, '<meta property="og:type" content="video.tv_show"')
