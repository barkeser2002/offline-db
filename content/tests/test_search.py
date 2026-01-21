from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache
from content.models import Anime, Genre

class SearchTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.genre_action = Genre.objects.create(name="Action", slug="action")
        self.genre_comedy = Genre.objects.create(name="Comedy", slug="comedy")

        self.anime1 = Anime.objects.create(title="Naruto", synopsis="Ninja stuff")
        self.anime1.genres.add(self.genre_action)

        self.anime2 = Anime.objects.create(title="One Piece", synopsis="Pirate stuff")
        self.anime2.genres.add(self.genre_action)
        self.anime2.genres.add(self.genre_comedy)

        self.anime3 = Anime.objects.create(title="Death Note", synopsis="Notebook stuff")
        # No genre for this one in this test setup

    def test_search_view_status_code(self):
        response = self.client.get(reverse('search'))
        self.assertEqual(response.status_code, 200)

    def test_search_by_title(self):
        response = self.client.get(reverse('search'), {'q': 'Naruto'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Naruto")
        self.assertNotContains(response, "One Piece")
        self.assertNotContains(response, "Death Note")

    def test_search_by_partial_title(self):
        response = self.client.get(reverse('search'), {'q': 'Piece'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "One Piece")
        self.assertNotContains(response, "Naruto")

    def test_search_by_genre(self):
        # Assuming we can search by genre name or slug. Let's try name first or query param 'genre'
        response = self.client.get(reverse('search'), {'genre': 'Comedy'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "One Piece")
        self.assertNotContains(response, "Naruto") # Naruto is Action only

    def test_search_no_results(self):
        response = self.client.get(reverse('search'), {'q': 'Bleach'})
        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context['results'], [])
        self.assertContains(response, "No results found")

    def test_search_combined(self):
        # Search for Action anime with "One" in title
        response = self.client.get(reverse('search'), {'q': 'One', 'genre': 'Action'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "One Piece")
        self.assertNotContains(response, "Naruto") # Has Action but not "One"

    def test_search_rate_limit(self):
        # We set limit=20 in views.py
        for i in range(20):
            response = self.client.get(reverse('search'), {'q': 'Naruto'})
            self.assertEqual(response.status_code, 200, f"Request {i+1} failed")

        # 21st request should fail
        response = self.client.get(reverse('search'), {'q': 'Naruto'})
        self.assertEqual(response.status_code, 403)
