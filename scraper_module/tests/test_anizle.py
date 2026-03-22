import unittest
from unittest.mock import patch, MagicMock
import json

from scraper_module.adapters.anizle import (
    search_anizle,
    get_anime_episodes,
    _get_episode_translators,
    _get_translator_videos,
    AnizleAnime,
    AnizleEpisode,
)

class TestAnizleAdapter(unittest.TestCase):

    @patch('scraper_module.adapters.anizle.load_anime_database')
    def test_search_anizle(self, mock_db):
        mock_db.return_value = [
            {"info_slug": "naruto", "info_title": "Naruto"},
            {"info_slug": "one-piece", "info_title": "One Piece"},
        ]

        res = search_anizle("naruto")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0], ("naruto", "Naruto"))

    @patch('scraper_module.adapters.anizle.load_anime_database')
    @patch('scraper_module.adapters.anizle._http_get')
    def test_get_anime_episodes(self, mock_get, mock_db):
        mock_db.return_value = []
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '''
        <a href="/naruto/1-bolum" data-order="1">1. Bölüm</a>
        <a href="/naruto/2-bolum" data-order="2">2. Bölüm</a>
        '''
        mock_get.return_value = mock_resp

        eps = get_anime_episodes("naruto")
        self.assertEqual(len(eps), 2)
        # Verify the slug part
        self.assertEqual(eps[0], ("naruto/1-bolum", "1. Bölüm"))
        self.assertEqual(eps[1], ("naruto/2-bolum", "2. Bölüm"))

    @patch('scraper_module.adapters.anizle._http_get')
    def test_get_episode_translators(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '''
        <div translator="https://anizle.org/ep1/tr1" data-fansub-name="Fansub1"></div>
        <div translator="https://anizle.org/ep1/tr2" data-fansub-name="Fansub2"></div>
        '''
        mock_get.return_value = mock_resp

        translators = _get_episode_translators("https://anizle.org/naruto/1-bolum")
        self.assertEqual(len(translators), 2)
        self.assertEqual(translators[0]["name"], "Fansub1")
        self.assertEqual(translators[1]["name"], "Fansub2")

    @patch('scraper_module.adapters.anizle._http_get')
    def test_get_translator_videos(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": '''
            <a video="https://vid1" data-video-name="Player 1"></a>
            <a video="https://vid2" data-video-name="Player 2"></a>
            '''
        }
        mock_get.return_value = mock_resp

        videos = _get_translator_videos("https://anizle.org/ep1/tr1")
        self.assertEqual(len(videos), 2)

        self.assertTrue(videos[0]["name"] in ["Player 1", "Player 2"])

    def test_anizle_anime_from_database(self):
        data = {
            "info_slug": "naruto",
            "info_title": "Naruto",
            "categories": [{"tag_title": "Action"}, {"tag_title": "Ninja"}]
        }
        anime = AnizleAnime.from_database(data)
        self.assertEqual(anime.slug, "naruto")
        self.assertEqual(anime.title, "Naruto")
        self.assertEqual(anime.categories, ["Action", "Ninja"])

if __name__ == '__main__':
    unittest.main()
