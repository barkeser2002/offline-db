import re
from unittest.mock import patch
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from content.models import Anime, Season, Episode
from django.test.utils import CaptureQueriesContext
from django.db import connection

User = get_user_model()

class ImportJikanPerformanceTest(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser('admin_jikan', 'admin@example.com', 'password')
        self.client = Client()
        self.client.force_login(self.admin_user)

    @patch('requests.get')
    @patch('time.sleep', return_value=None)
    def test_import_jikan_queries(self, mock_sleep, mock_get):
        # Mock Anime Info
        mock_get.side_effect = [
            # Anime Info
            type('Response', (), {'status_code': 200, 'json': lambda: {'data': {
                'title': 'Test Anime',
                'synopsis': 'Test Synopsis',
                'images': {'jpg': {'large_image_url': 'http://example.com/image.jpg'}}
            }}}),
            # Episodes Page 1
            type('Response', (), {'status_code': 200, 'json': lambda: {
                'data': [
                    {'url': 'http://example.com/episode/1', 'title': 'Episode 1'},
                    {'url': 'http://example.com/episode/2', 'title': 'Episode 2'},
                    {'url': 'http://example.com/episode/3', 'title': 'Episode 3'},
                    {'url': 'http://example.com/episode/4', 'title': 'Episode 4'},
                    {'url': 'http://example.com/episode/5', 'title': 'Episode 5'},
                ],
                'pagination': {'has_next_page': False}
            }})
        ]

        url = reverse('admin:content_anime_import_jikan')

        with CaptureQueriesContext(connection) as ctx:
            response = self.client.post(url, {'mal_id': '12345'}, follow=True)

        self.assertEqual(response.status_code, 200)

        # Current implementation:
        # 1. Fetch/Create Anime (get_or_create + save) -> ~2-3 queries
        # 2. Get/Create Season -> ~1-2 queries
        # 3. For each episode (5 episodes): Episode.objects.get_or_create -> ~2 queries each (SELECT + INSERT/UPDATE)
        # Total expected queries should be > 10.

        print(f"\nCaptured queries for 5 episodes: {len(ctx.captured_queries)}")
        for i, q in enumerate(ctx.captured_queries):
            print(f"{i+1}: {q['sql'][:100]}...")

        # If we have 5 episodes, get_or_create for each usually takes at least 2 queries if they don't exist.
        # Plus anime and season creation.
