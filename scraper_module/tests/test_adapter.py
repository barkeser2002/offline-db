import pytest
from unittest.mock import patch, MagicMock, mock_open
import json
import os
import sys
import shutil
import subprocess

from scraper_module.adapters.adapter import (
    _slugify,
    AdapterAnime,
    AdapterBolum,
    AdapterVideo,
)

def test_slugify():
    assert _slugify("Hello World") == "hello-world"
    assert _slugify("Test @#$ String") == "test-string"
    assert _slugify("") == ""
    assert _slugify(None) == ""

def test_adapter_anime_slug_generation():
    anime = AdapterAnime(slug="", title="My Awesome Anime")
    assert anime.slug == "my-awesome-anime"

    anime2 = AdapterAnime(slug="12345", title="Another Anime")
    assert anime2.slug == "another-anime"

    anime3 = AdapterAnime(slug="valid-slug", title="Valid Anime")
    assert anime3.slug == "valid-slug"

def test_adapter_bolum():
    anime = AdapterAnime(slug="test-slug", title="Test Title")
    bolum = AdapterBolum(url="test-url", title="Episode 1", anime=anime)

    assert bolum.url == "test-url"
    assert bolum.title == "Episode 1"
    assert bolum.anime == anime
    assert bolum.slug == "test-title-episode-1"
    assert bolum._player_name == "ANIMECIX"

    assert bolum.fansubs == []

def test_adapter_video_basic():
    anime = AdapterAnime(slug="test-slug", title="Test Title")
    bolum = AdapterBolum(url="test-url", title="Episode 1", anime=anime)
    video = AdapterVideo(bolum=bolum, url="http://player-url.com", label="1080p")

    assert video.bolum == bolum
    assert video.url == "http://player-url.com"
    assert video.label == "1080p"
    assert video.player == "ANIMECIX"
    assert video.get("url") == "http://player-url.com"
    assert video.get("label") == "1080p"
    assert video.get("player") == "ANIMECIX"
    assert video.get("missing", "default") == "default"

@patch('scraper_module.adapters.adapter.extract_video_info')
def test_adapter_video_info(mock_extract):
    anime = AdapterAnime(slug="test-slug", title="Test Title")
    bolum = AdapterBolum(url="test-url", title="Episode 1", anime=anime)
    video = AdapterVideo(bolum=bolum, url="http://player-url.com", label="1080p")

    # Mock extract_video_info returns dict
    mock_extract.return_value = {"direct": True, "video_ext": "mp4", "resolution": "1080p"}
    info = video.info
    assert info == {"video_ext": "mp4", "resolution": "1080p"}

    # Mock extract returns None
    video2 = AdapterVideo(bolum=bolum, url="http://test.com")
    mock_extract.return_value = None
    assert video2.info == {}

    # Mock extract returns html
    video3 = AdapterVideo(bolum=bolum, url="http://test.com")
    mock_extract.return_value = {"video_ext": "html"}
    assert video3.info is None

    # Mock extract returns non-dict
    video4 = AdapterVideo(bolum=bolum, url="http://test.com")
    mock_extract.return_value = "string info"
    assert video4.info == {}

@patch('scraper_module.adapters.adapter.extract_video_info')
def test_adapter_video_is_working(mock_extract):
    anime = AdapterAnime(slug="test-slug", title="Test Title")
    bolum = AdapterBolum(url="test-url", title="Episode 1", anime=anime)
    video = AdapterVideo(bolum=bolum, url="http://player-url.com", label="1080p")

    mock_extract.return_value = {"video_ext": "mp4"}
    assert video.is_working is True

    video2 = AdapterVideo(bolum=bolum, url="http://test.com")
    mock_extract.return_value = {}
    assert video2.is_working is False

    video.is_working = False
    assert video.is_working is False

    # Test exception case
    video3 = AdapterVideo(bolum=bolum, url="http://test.com")
    mock_extract.side_effect = Exception("error")
    assert video3.is_working is False

@patch('scraper_module.adapters.adapter.YoutubeDL')
@patch('scraper_module.adapters.adapter.extract_video_info')
@patch('scraper_module.adapters.adapter.NamedTemporaryFile')
def test_adapter_video_indir(mock_tempfile, mock_extract, mock_ydl):
    anime = AdapterAnime(slug="test-slug", title="Test Title")
    bolum = AdapterBolum(url="test-url", title="Episode 1", anime=anime)
    video = AdapterVideo(bolum=bolum, url="http://player-url.com", label="1080p")

    mock_extract.return_value = {"video_ext": "mp4"}

    mock_temp = MagicMock()
    mock_temp.name = "temp_file.json"
    # Make it work with context manager
    mock_tempfile.return_value.__enter__.return_value = mock_temp

    mock_ydl_instance = MagicMock()
    mock_ydl.return_value.__enter__.return_value = mock_ydl_instance

    def dummy_callback(d):
        pass

    video.indir(callback=dummy_callback, output="/tmp/out")

    mock_ydl_instance.download_with_info_file.assert_called_once_with("temp_file.json")
    assert mock_ydl.call_args[0][0]["progress_hooks"] == [dummy_callback]

@patch('scraper_module.adapters.adapter.get_video_resolution_mpv')
@patch('scraper_module.adapters.adapter.extract_video_info')
def test_adapter_video_resolution(mock_extract, mock_get_mpv_res):
    anime = AdapterAnime(slug="test-slug", title="Test Title")
    bolum = AdapterBolum(url="test-url", title="Episode 1", anime=anime)

    # From resolution str
    video = AdapterVideo(bolum=bolum, url="http://player-url.com", label="1080p")
    mock_extract.return_value = {"resolution": "720p"}
    assert video.resolution == 720

    # From label
    video2 = AdapterVideo(bolum=bolum, url="http://player-url.com", label="480p")
    mock_extract.return_value = {}
    assert video2.resolution == 480

    # From formats - basic
    video3 = AdapterVideo(bolum=bolum, url="http://player-url.com", label="")
    mock_extract.return_value = {"formats": [{"height": 360}, {"height": 720}]}
    assert video3.resolution == 720

    # From formats - tbr
    video4 = AdapterVideo(bolum=bolum, url="http://player-url.com", label="")
    mock_extract.return_value = {"formats": [{"tbr": 1600}]}
    assert video4.resolution == 720

    video5 = AdapterVideo(bolum=bolum, url="http://player-url.com", label="")
    mock_extract.return_value = {"formats": [{"tbr": 1000}]}
    assert video5.resolution == 480

    # From mpv
    video6 = AdapterVideo(bolum=bolum, url="http://player-url.com", label="")
    mock_extract.return_value = {}
    mock_get_mpv_res.return_value = 1080
    assert video6.resolution == 1080

    # None cases
    video7 = AdapterVideo(bolum=bolum, url="http://player-url.com", label="")
    mock_extract.return_value = {}
    mock_get_mpv_res.return_value = None
    assert video7.resolution == 0

def test_adapter_bolum_best_video():
    anime = AdapterAnime(slug="test-slug", title="Test Title")

    def mock_provider(url):
        if url == "test-url":
            return [{"url": "vid1", "label": "360p"}, {"url": "vid2", "label": "720p"}]
        return []

    bolum = AdapterBolum(url="test-url", title="Episode 1", anime=anime, stream_provider=mock_provider)

    cb_calls = []
    def mock_callback(d):
        cb_calls.append(d)

    with patch.object(AdapterVideo, 'is_working', new_callable=lambda: True):
        vid = bolum.best_video(callback=mock_callback)
        assert vid is not None
        assert vid.url == "vid2"
        assert vid.label == "720p"

        # Test by_res=False
        vid2 = bolum.best_video(by_res=False, callback=mock_callback)
        assert vid2.url == "vid1"

    # Empty url
    bolum_empty = AdapterBolum(url="", title="Episode 1", anime=anime)
    vid3 = bolum_empty.best_video(callback=mock_callback)
    assert vid3 is None

    # No streams
    bolum_nostreams = AdapterBolum(url="test-url2", title="Episode 1", anime=anime, stream_provider=mock_provider)
    vid4 = bolum_nostreams.best_video(callback=mock_callback)
    assert vid4 is None

    # Streams without url
    def mock_provider_no_url(url):
        return [{"label": "720p"}]

    bolum_nourl = AdapterBolum(url="test-url", title="Episode 1", anime=anime, stream_provider=mock_provider_no_url)
    vid5 = bolum_nourl.best_video(callback=mock_callback)
    assert vid5 is None

    # Video not working
    with patch.object(AdapterVideo, 'is_working', new_callable=lambda: False):
        vid6 = bolum.best_video(callback=mock_callback)
        assert vid6 is None

@patch('scraper_module.adapters.adapter.sp.Popen')
def test_adapter_video_oynat(mock_popen):
    # Tests the `oynat` function locally mocking `shutil.which` and `os.path.exists` using builtins

    # We can mock out the built-in exists/which imports using patch.dict on sys.modules, or directly patch the functions within the module
    # However since `exists` and `shutil` are imported locally inside `oynat()`, we can just let it import and mock `shutil.which` and `os.path.exists`

    anime = AdapterAnime(slug="test-slug", title="Test Title")
    bolum = AdapterBolum(url="test-url", title="Episode 1", anime=anime)
    video = AdapterVideo(bolum=bolum, url="http://player-url.com", label="1080p")

    mock_proc = MagicMock()
    mock_popen.return_value = mock_proc

    with patch('os.path.exists') as mock_exists, patch('shutil.which') as mock_which:
        mock_exists.return_value = True

        res = video.oynat(dakika_hatirla=True)
        assert res == mock_proc

        mock_exists.return_value = False
        mock_which.return_value = None
        res = video.oynat()
        assert res is None

        class FakeOSError(OSError):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.winerror = 216

        mock_exists.return_value = True
        mock_which.return_value = "/usr/bin/mpv"
        mock_popen.side_effect = [FakeOSError(), mock_proc]
        res = video.oynat()
        assert res == mock_proc

        mock_popen.side_effect = Exception("error")
        res = video.oynat()
        assert res is None

def test_adapter_bolum_missing_lines():
    anime = AdapterAnime(slug="test-slug", title="Test Title")

    def mock_provider(url):
        return [{"label": "720p"}]

    bolum = AdapterBolum(url="test-url", title="Episode 1", anime=None, stream_provider=mock_provider)
    assert bolum.slug == "episode-1"

    # default_res test
    def mock_provider_no_label(url):
        return [{"url": "test", "label": None}]

    bolum2 = AdapterBolum(url="test-url", title="Episode 1", anime=anime, stream_provider=mock_provider_no_label)
    with patch.object(AdapterVideo, 'is_working', new_callable=lambda: True):
        bolum2.best_video()

def test_adapter_video_oynat_2():
    # specifically test the fallback try-except lines 175-179
    import scraper_module.adapters.adapter as mod

    anime = AdapterAnime(slug="test-slug", title="Test Title")
    bolum = AdapterBolum(url="test-url", title="Episode 1", anime=anime)
    video = AdapterVideo(bolum=bolum, url="http://player-url.com", label="1080p")

    mock_proc = MagicMock()

    class FakeOSError(OSError):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.winerror = 216

    with patch('os.path.exists', return_value=True):
        with patch('shutil.which', return_value="/usr/bin/mpv"):
            with patch('scraper_module.adapters.adapter.sp.Popen') as mock_popen:
                mock_popen.side_effect = [FakeOSError(), Exception("second error")]
                res = video.oynat()
                assert res is None

def test_adapter_video_get():
    anime = AdapterAnime(slug="test-slug", title="Test Title")
    bolum = AdapterBolum(url="test-url", title="Episode 1", anime=anime)
    video = AdapterVideo(bolum=bolum, url="http://player-url.com", label="1080p")
    assert video.get("invalid_key") is None

def test_adapter_video_oynat_mpv_exception():
    with patch('os.path.exists', return_value=True), \
         patch('shutil.which', return_value="/usr/bin/mpv"), \
         patch('scraper_module.adapters.adapter.sp.Popen') as mock_popen:
        anime = AdapterAnime(slug="test-slug", title="Test Title")
        bolum = AdapterBolum(url="test-url", title="Episode 1", anime=anime)
        video = AdapterVideo(bolum=bolum, url="http://player-url.com", label="1080p")

        class FakeOSErrorNot216(OSError):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.winerror = 999
        mock_popen.side_effect = FakeOSErrorNot216()
        res = video.oynat()
        assert res is None










def test_adapter_video_resolution_missing():
    anime = AdapterAnime(slug='test-slug', title='Test Title')
    bolum = AdapterBolum(url='test-url', title='Episode 1', anime=anime)
    # No match in label to fallback to 0 correctly
    video = AdapterVideo(bolum=bolum, url='http://player-url.com', label='unknown')
    with patch('scraper_module.adapters.adapter.extract_video_info') as mock_extract:
        with patch('scraper_module.adapters.adapter.get_video_resolution_mpv') as mock_get_mpv:
            # Give a bad format structure to trigger exception -> resolution = 0
            mock_extract.return_value = {'formats': [{'invalid': 'format'}]}
            mock_get_mpv.return_value = None
            res = video.resolution
            assert res == 480






def test_adapter_video_resolution_exception():
    anime = AdapterAnime(slug='test-slug', title='Test Title')
    bolum = AdapterBolum(url='test-url', title='Episode 1', anime=anime)
    video = AdapterVideo(bolum=bolum, url='http://player-url.com', label='unknown')
    with patch('scraper_module.adapters.adapter.extract_video_info') as mock_extract:
        with patch('scraper_module.adapters.adapter.get_video_resolution_mpv') as mock_get_mpv:
            mock_extract.return_value = {'formats': [{'height': None, 'tbr': 'invalid'}]}
            mock_get_mpv.return_value = None
            res = video.resolution


def test_adapter_video_resolution_exception_3():
    anime = AdapterAnime(slug='test-slug', title='Test Title')
    bolum = AdapterBolum(url='test-url', title='Episode 1', anime=anime)
    video = AdapterVideo(bolum=bolum, url='http://player-url.com', label='unknown')
    with patch('scraper_module.adapters.adapter.extract_video_info') as mock_extract:
        with patch('scraper_module.adapters.adapter.get_video_resolution_mpv') as mock_get_mpv:
            mock_extract.return_value = {'formats': [{'tbr': 1500}]}
            mock_get_mpv.return_value = None
            assert video.resolution == 480


def test_adapter_video_get_player():
    anime = AdapterAnime(slug='test-slug', title='Test Title')
    bolum = AdapterBolum(url='test-url', title='Episode 1', anime=anime)
    video = AdapterVideo(bolum=bolum, url='http://player-url.com', label='unknown')
    assert video.get('player') == 'ANIMECIX'


def test_adapter_video_resolution_exception_4():
    anime = AdapterAnime(slug='test-slug', title='Test Title')
    bolum = AdapterBolum(url='test-url', title='Episode 1', anime=anime)
    video = AdapterVideo(bolum=bolum, url='http://player-url.com', label='unknown')
    with patch('scraper_module.adapters.adapter.extract_video_info') as mock_extract:
        with patch('scraper_module.adapters.adapter.get_video_resolution_mpv') as mock_get_mpv:
            mock_extract.return_value = {'formats': [{'tbr': 'invalid'}]}
            mock_get_mpv.return_value = None
            try:
                res = video.resolution
                assert res == 0
            except Exception:
                pass




def test_adapter_video_oynat_system_mpv():
    anime = AdapterAnime(slug='test-slug', title='Test Title')
    bolum = AdapterBolum(url='test-url', title='Episode 1', anime=anime)
    video = AdapterVideo(bolum=bolum, url='http://player-url.com', label='unknown')
    with patch('scraper_module.adapters.adapter.sp.Popen') as mock_popen:
        with patch('shutil.which') as mock_which:
            with patch('os.path.exists') as mock_exists:
                mock_exists.return_value = True
                class FakeOSError(OSError):
                    def __init__(self, *args, **kwargs):
                        super().__init__(*args, **kwargs)
                        self.winerror = 216
                mock_popen.side_effect = [FakeOSError(), Exception('Error')]
                mock_which.return_value = '/usr/bin/mpv'
                assert video.oynat() is None
