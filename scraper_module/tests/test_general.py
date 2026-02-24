from django.test import SimpleTestCase, TestCase
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from scraper_module.services.jikan import JikanClient

class JikanClientTests(SimpleTestCase):
    def setUp(self):
        self.client = JikanClient()

    @patch('scraper_module.services.jikan.AsyncSession')
    def test_get_anime_success(self, mock_session_cls):
        async def run_test():
            # Mock session context manager
            mock_session = AsyncMock()
            mock_session_cls.return_value.__aenter__.return_value = mock_session

            # Mock successful response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'data': {
                    'mal_id': 1,
                    'title': 'Cowboy Bebop'
                }
            }
            # .get is async
            mock_session.get.return_value = mock_response

            data = await self.client.get_anime(1)

            self.assertIsNotNone(data)
            self.assertEqual(data['title'], 'Cowboy Bebop')
            self.assertEqual(data['mal_id'], 1)

        asyncio.run(run_test())

    @patch('scraper_module.services.jikan.AsyncSession')
    def test_get_anime_404(self, mock_session_cls):
        async def run_test():
            mock_session = AsyncMock()
            mock_session_cls.return_value.__aenter__.return_value = mock_session

            # Mock 404 response
            mock_response = MagicMock()
            mock_response.status_code = 404

            # Since we handle 404 explicitly, we don't strictly need side_effect on raise_for_status
            # if the code checks status_code first. But good to keep mock clean.

            mock_session.get.return_value = mock_response

            data = await self.client.get_anime(99999)
            self.assertIsNone(data)

            # Ensure raise_for_status was NOT called
            mock_response.raise_for_status.assert_not_called()

        asyncio.run(run_test())

    @patch('scraper_module.services.jikan.cache')
    @patch('scraper_module.services.jikan.AsyncSession')
    def test_rate_limit_retry(self, mock_session_cls, mock_cache):
        async def run_test():
            mock_cache.get.return_value = None
            mock_session = AsyncMock()
            mock_session_cls.return_value.__aenter__.return_value = mock_session

            # Mock 429 then 200
            mock_429 = MagicMock()
            mock_429.status_code = 429
            mock_429.headers = {'Retry-After': '1'}

            mock_200 = MagicMock()
            mock_200.status_code = 200
            mock_200.json.return_value = {'data': {'title': 'Retry Success'}}

            # session.get called multiple times on SAME session
            mock_session.get.side_effect = [mock_429, mock_200]

            # We need to mock asyncio.sleep to avoid waiting
            with patch('scraper_module.services.jikan.asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                data = await self.client.get_anime(1)

                self.assertIsNotNone(data)
                self.assertEqual(data['title'], 'Retry Success')
                # Check sleep called
                mock_sleep.assert_awaited()
                self.assertEqual(mock_session.get.call_count, 2)

        asyncio.run(run_test())

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
