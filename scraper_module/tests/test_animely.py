import unittest
from unittest.mock import patch, MagicMock
import json

from scraper_module.adapters.animely import (
    get_anime_list,
    search_anime,
    search_animely,
    get_anime_episodes,
    get_episode_streams,
    get_anime_by_slug,
    get_anime_by_id,
    get_anime_url,
    AnimelyAnime,
    AnimelyEpisode,
    AnimelyVideo,
)

class TestAnimelyAdapter(unittest.TestCase):

    @patch('scraper_module.adapters.animely._get_cached_anime_list')
    @patch('scraper_module.adapters.animely.SESSION.get')
    def test_get_anime_list(self, mock_get, mock_cache):
        # 1. Test cache hit
        mock_cache.return_value = [{"SLUG": "cached"}]
        self.assertEqual(get_anime_list(use_cache=True)[0]["SLUG"], "cached")

        # 2. Test API fetch
        mock_cache.return_value = None
        mock_resp = MagicMock()
        mock_resp.json.return_value = [{"SLUG": "fetched"}]
        mock_get.return_value = mock_resp

        with patch('scraper_module.adapters.animely._save_anime_list_to_cache') as mock_save:
            res = get_anime_list(use_cache=True)
            self.assertEqual(res[0]["SLUG"], "fetched")
            mock_save.assert_called_once()

        # 3. Test API failure
        mock_get.side_effect = Exception("API error")
        self.assertEqual(get_anime_list(use_cache=False), [])

    @patch('scraper_module.adapters.animely.get_anime_list')
    def test_search_anime(self, mock_list):
        mock_list.return_value = [
            {"NAME": "Naruto", "OTHER_NAMES": ["Shippuden"], "SLUG": "naruto", "FIRST_IMAGE": "img1", "TOTAL_EPISODES": 500},
            {"NAME": "One Piece", "OTHER_NAMES": [], "SLUG": "one-piece", "FIRST_IMAGE": "img2", "TOTAL_EPISODES": 1000},
        ]

        # Exact match
        res = search_anime("Naruto")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].slug, "naruto")

        # Partial match
        res2 = search_anime("Piece")
        self.assertEqual(len(res2), 1)
        self.assertEqual(res2[0].slug, "one-piece")

    @patch('scraper_module.adapters.animely.SESSION.post')
    def test_get_anime_episodes(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "episodes": [
                {
                    "id": 1,
                    "episode_number": 2,
                    "backblaze_link": "link1",
                    "watch_link_1": "link2"
                },
                {
                    "id": 2,
                    "episode_number": 1,
                    "backblaze_link": "link3"
                }
            ]
        }
        mock_post.return_value = mock_resp

        eps = get_anime_episodes("naruto")
        self.assertEqual(len(eps), 2)
        # Verify sorting by episode_number
        self.assertEqual(eps[0].episode_number, 1)
        self.assertEqual(eps[1].episode_number, 2)
        self.assertEqual(eps[1].url, "link1")

    def test_animely_episode(self):
        ep = AnimelyEpisode(id=1, episode_number=1, name="1. Bölüm", ep_type="tv", fansub="Animely", _links=["", "link1"])
        self.assertEqual(ep.title, "1. Bölüm")
        self.assertEqual(ep.url, "link1")

        streams = ep.get_streams()
        self.assertEqual(len(streams), 1)
        self.assertEqual(streams[0].url, "link1")
        self.assertEqual(streams[0].quality, "Link 1") # HD for i=0, Link 1 for i=1

    @patch('scraper_module.adapters.animely.SESSION.get')
    def test_get_anime_by_id(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "slug": "naruto",
            "name": "Naruto"
        }
        mock_get.return_value = mock_resp

        anime = get_anime_by_id(1)
        self.assertIsNotNone(anime)
        self.assertEqual(anime.slug, "naruto")

    def test_get_anime_url(self):
        self.assertEqual(get_anime_url("naruto"), "https://animely.net/anime/naruto")
        self.assertEqual(get_anime_url("naruto", 1), "https://animely.net/anime/naruto/izle/1")

if __name__ == '__main__':
    unittest.main()
