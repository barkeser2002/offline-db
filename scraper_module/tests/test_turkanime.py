import unittest
from unittest.mock import patch

from scraper_module.adapters.turkanime import (
    search_anime,
    get_anime_details,
    get_anime_episodes,
    get_episode_streams,
    _get_video_sources,
)

class TestTurkanimeAdapter(unittest.TestCase):

    @patch('scraper_module.adapters.turkanime.fetch')
    def test_search_anime(self, mock_fetch):
        mock_fetch.return_value = '''
        <a href="/anime/naruto">Naruto</a>
        <a href="/anime/one-piece">One Piece</a>
        '''
        res = search_anime("naruto")
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0], ("naruto", "naruto", "Naruto"))
        self.assertEqual(res[1], ("one-piece", "one-piece", "One Piece"))

    @patch('scraper_module.adapters.turkanime.fetch')
    def test_get_anime_details(self, mock_fetch):
        mock_fetch.return_value = '''
        <h1 class="detay-baslik">Naruto</h1>
        '''
        anime = get_anime_details("naruto")
        self.assertIsNotNone(anime)
        self.assertEqual(anime.title, "Naruto")

    @patch('scraper_module.adapters.turkanime.fetch')
    def test_get_anime_episodes(self, mock_fetch):
        mock_fetch.return_value = '''
        <a href="/video/naruto-1-bolum"> 1. Bölüm </a>
        <a href="/video/naruto-2-bolum"> 2. Bölüm </a>
        '''
        eps = get_anime_episodes("naruto")
        self.assertEqual(len(eps), 2)
        self.assertEqual(eps[0].episode_number, 1)
        self.assertEqual(eps[1].episode_number, 2)
        self.assertEqual(eps[0].slug, "naruto-1-bolum")

    @patch('scraper_module.adapters.turkanime.fetch')
    @patch('scraper_module.adapters.turkanime._get_video_sources')
    def test_get_episode_streams(self, mock_sources, mock_fetch):
        mock_fetch.return_value = '''
        <div data-fansub="Fansub1" data-video="123"></div>
        '''
        from scraper_module.adapters.turkanime import TurkAnimeStream
        mock_sources.return_value = [TurkAnimeStream(url="url1", quality="720p", fansub="Fansub1", player="player1")]

        streams = get_episode_streams("naruto-1-bolum")
        self.assertEqual(len(streams), 1)
        self.assertEqual(streams[0].url, "url1")

    @patch('scraper_module.adapters.turkanime.fetch')
    @patch('scraper_module.adapters.turkanime.unmask_real_url')
    def test_get_video_sources(self, mock_unmask, mock_fetch):
        mock_fetch.return_value = '''
        <a href="https://turkanime.co/player/123">Player 1</a>
        <a href="http://other.com/video">Player 2</a>
        '''
        mock_unmask.return_value = "https://real-video.mp4"

        sources = _get_video_sources("123", "Fansub1")
        self.assertEqual(len(sources), 2)
        self.assertEqual(sources[0].url, "https://real-video.mp4")
        self.assertEqual(sources[1].url, "http://other.com/video")

if __name__ == '__main__':
    unittest.main()
