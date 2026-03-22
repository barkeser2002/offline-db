import unittest
from unittest.mock import patch, MagicMock
import json

from scraper_module.adapters.animecix import (
    search_animecix,
    _seasons_for_title,
    _episodes_for_title,
    _video_streams,
    CixAnime,
    CixEpisode,
)

class TestAnimecixAdapter(unittest.TestCase):

    @patch('scraper_module.adapters.animecix._http_get')
    def test_search_animecix(self, mock_http_get):
        mock_response = {
            "results": [
                {"name": "Naruto", "id": 123},
                {"name": "One Piece", "id": 456},
                {"missing_id": True},
                {"name": "No ID", "id": None}
            ]
        }
        mock_http_get.return_value = json.dumps(mock_response).encode('utf-8')

        results = search_animecix("ninja")

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], ("123", "Naruto"))
        self.assertEqual(results[1], ("456", "One Piece"))

        # Verify encoding logic inside search
        mock_http_get.assert_called_once()
        args = mock_http_get.call_args[0]
        self.assertTrue("ninja" in args[0])

    @patch('scraper_module.adapters.animecix._http_get')
    def test_seasons_for_title(self, mock_http_get):
        mock_response = {
            "videos": [
                {
                    "title": {
                        "seasons": [{"id": 1}, {"id": 2}]
                    }
                }
            ]
        }
        mock_http_get.return_value = json.dumps(mock_response).encode('utf-8')

        seasons = _seasons_for_title(123)
        self.assertEqual(seasons, [0, 1])

    @patch('scraper_module.adapters.animecix._http_get')
    def test_episodes_for_title(self, mock_http_get):
        # We need to mock multiple calls to _http_get
        # Call 1: _seasons_for_title
        seasons_response = {
            "videos": [
                {
                    "title": {
                        "seasons": [{"id": 1}]
                    }
                }
            ]
        }

        # Call 2: Episodes for season 1
        episodes_response = {
            "videos": [
                {"name": "Ep 1", "url": "http://ep1", "season_num": 1},
                {"name": "Ep 1", "url": "http://ep1", "season_num": 1}, # Duplicate
                {"name": "Ep 2", "url": "http://ep2", "season_num": 1},
                {"no_name": True, "url": "http://ep3"}, # Invalid
            ]
        }

        mock_http_get.side_effect = [
            json.dumps(seasons_response).encode('utf-8'),
            json.dumps(episodes_response).encode('utf-8')
        ]

        episodes = _episodes_for_title("123")
        self.assertEqual(len(episodes), 2)
        self.assertEqual(episodes[0]["name"], "Ep 1")
        self.assertEqual(episodes[1]["name"], "Ep 2")

    @patch('scraper_module.adapters.animecix._http_get')
    @patch('scraper_module.adapters.animecix.urllib.request.urlopen')
    def test_video_streams(self, mock_urlopen, mock_http_get):
        # Mocking the urlopen redirect resolution
        mock_resp = MagicMock()
        mock_resp.geturl.return_value = "https://example.com/embed/123?vid=456"
        mock_urlopen.return_value = mock_resp

        # Mocking the API response
        api_response = {
            "urls": [
                {"label": "720p", "url": "http://720"},
                {"label": "1080p", "url": "http://1080"},
                {"missing": "label"}
            ]
        }
        mock_http_get.return_value = json.dumps(api_response).encode('utf-8')

        streams = _video_streams("some_embed_path")

        self.assertEqual(len(streams), 2)
        self.assertEqual(streams[0]["label"], "720p")
        self.assertEqual(streams[1]["label"], "1080p")

    @patch('scraper_module.adapters.animecix._episodes_for_title')
    def test_cix_anime(self, mock_episodes):
        mock_episodes.return_value = [
            {"name": "Bölüm 1", "url": "http://b1"},
            {"url": "http://b2"} # Fallback to "Bölüm {i+1}"
        ]

        anime = CixAnime(id="123", title="Naruto")
        self.assertEqual(anime.id, "123")
        self.assertEqual(anime.title, "Naruto")

        episodes = anime.episodes
        self.assertEqual(len(episodes), 2)
        self.assertEqual(episodes[0].title, "Bölüm 1")
        self.assertEqual(episodes[0].url, "http://b1")
        self.assertEqual(episodes[1].title, "Bölüm 2")
        self.assertEqual(episodes[1].url, "http://b2")

if __name__ == '__main__':
    unittest.main()
