import unittest
from unittest.mock import patch, MagicMock

from scraper_module.adapters.tranime import (
    get_anime_by_slug,
    get_anime_episodes,
    get_episode_details,
    search_anime,
    search_by_letter,
    TRAnimeAnime,
    TRAnimeEpisode,
)

class TestTRAnimeAdapter(unittest.TestCase):

    @patch('scraper_module.adapters.tranime._get_session')
    def test_get_anime_by_slug(self, mock_get_session):
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '''
        <h1>Naruto İzle</h1>
        <img src="https://poster.jpg" class="thumbnail">
        <a href="/naruto-1-bolum-izle">1</a>
        <a href="/naruto-2-bolum-izle">2</a>
        '''
        mock_session.get.return_value = mock_resp
        mock_get_session.return_value = mock_session

        anime = get_anime_by_slug("naruto")
        self.assertIsNotNone(anime)
        self.assertEqual(anime.slug, "naruto")
        self.assertEqual(anime.title, "Naruto")
        self.assertEqual(anime.total_episodes, 2)
        self.assertEqual(anime.poster, "https://poster.jpg")

    @patch('scraper_module.adapters.tranime._get_session')
    def test_get_anime_episodes(self, mock_get_session):
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '''
        <a href="/naruto-1-bolum-izle">1. Bölüm</a>
        <a href="/naruto-2-bolum-izle">2. Bölüm</a>
        '''
        mock_session.get.return_value = mock_resp
        mock_get_session.return_value = mock_session

        eps = get_anime_episodes("naruto")
        self.assertEqual(len(eps), 2)
        self.assertEqual(eps[0].episode_number, 1)
        self.assertEqual(eps[1].episode_number, 2)

    @patch('scraper_module.adapters.tranime._get_session')
    def test_get_episode_details(self, mock_get_session):
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '''
        <input id="EpisodeId" value="1234">
        <li data-fid="1" data-fad="Fansub1"></li>
        <li data-fid="2" data-fad="Fansub2"></li>
        '''
        mock_session.get.return_value = mock_resp
        mock_get_session.return_value = mock_session

        ep = get_episode_details("naruto-5-bolum-izle")
        self.assertIsNotNone(ep)
        self.assertEqual(ep.episode_id, 1234)
        self.assertEqual(ep.episode_number, 5)
        self.assertEqual(len(ep.fansubs), 2)
        self.assertEqual(ep.fansubs[0], ("1", "Fansub1"))

    @patch('scraper_module.adapters.tranime._get_session')
    def test_search_by_letter(self, mock_get_session):
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '''
        <a href="/anime/naruto-izle"><h2>Naruto</h2></a>
        <a href="/anime/naruto-shippuden-izle"><h2>Naruto Shippuden</h2></a>
        '''
        mock_session.get.return_value = mock_resp
        mock_get_session.return_value = mock_session

        res = search_by_letter("n", 1)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0], ("naruto", "Naruto"))
        self.assertEqual(res[1], ("naruto-shippuden", "Naruto Shippuden"))

if __name__ == '__main__':
    unittest.main()
