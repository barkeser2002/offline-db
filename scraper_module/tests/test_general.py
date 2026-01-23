from django.test import TestCase
from unittest.mock import patch, MagicMock
from scraper_module.services.jikan import JikanClient

class JikanClientTests(TestCase):
    def setUp(self):
        self.client = JikanClient()

    @patch('scraper_module.services.jikan.requests.get')
    def test_get_anime_success(self, mock_get):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'mal_id': 1,
                'title': 'Cowboy Bebop'
            }
        }
        mock_get.return_value = mock_response

        data = self.client.get_anime(1)

        self.assertIsNotNone(data)
        self.assertEqual(data['title'], 'Cowboy Bebop')
        self.assertEqual(data['mal_id'], 1)

    @patch('scraper_module.services.jikan.requests.get')
    def test_get_anime_404(self, mock_get):
        # Mock 404 response
        mock_response = MagicMock()
        mock_response.status_code = 404
        # requests.raise_for_status() raises HTTPError on 4xx/5xx
        from requests.exceptions import HTTPError

        error = HTTPError()
        error.response = mock_response
        mock_response.raise_for_status.side_effect = error

        mock_get.return_value = mock_response

        data = self.client.get_anime(99999)
        self.assertIsNone(data)

    @patch('scraper_module.services.jikan.requests.get')
    def test_rate_limit_retry(self, mock_get):
        # Mock 429 then 200
        mock_429 = MagicMock()
        mock_429.status_code = 429
        mock_429.headers = {'Retry-After': '1'}

        mock_200 = MagicMock()
        mock_200.status_code = 200
        mock_200.json.return_value = {'data': {'title': 'Retry Success'}}

        # side_effect iterates through the list
        mock_get.side_effect = [mock_429, mock_200]

        # We need to mock time.sleep to avoid waiting in tests
        with patch('scraper_module.services.jikan.time.sleep') as mock_sleep:
            data = self.client.get_anime(1)

            self.assertIsNotNone(data)
            self.assertEqual(data['title'], 'Retry Success')
            self.assertEqual(mock_get.call_count, 2)
            mock_sleep.assert_called()

class TurkAnimeAdapterTests(TestCase):
    def test_dependencies_imported(self):
        """
        Verify that the TurkAnime adapter has all required dependencies installed.
        This ensures AES and curl_cffi are available.
        """
        from scraper_module.adapters import turkanime_bypass

        # Verify AES (pycryptodome) is available
        self.assertIsNotNone(turkanime_bypass.AES, "pycryptodome dependency is missing or failed to import.")

        # Verify curl_requests (curl_cffi) is available
        self.assertIsNotNone(turkanime_bypass.curl_requests, "curl_cffi dependency is missing or failed to import.")
