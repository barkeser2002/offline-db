import pytest
from scraper_module.adapters.adapter import _slugify, AdapterAnime, AdapterBolum, AdapterVideo

def test_slugify():
    assert _slugify("Hello World") == "hello-world"
    # Testing some basic slugify behaviors
    assert _slugify("Test @#$ String") == "test-string"
    assert _slugify("") == ""
    assert _slugify(None) == ""

def test_adapter_anime_slug_generation():
    # When slug is empty or digit-only, it should generate a slug from the title
    anime = AdapterAnime(slug="", title="My Awesome Anime")
    assert anime.slug == "my-awesome-anime"

    anime2 = AdapterAnime(slug="12345", title="Another Anime")
    assert anime2.slug == "another-anime"

    # When valid slug is provided, it should keep it
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

def test_adapter_video():
    anime = AdapterAnime(slug="test-slug", title="Test Title")
    bolum = AdapterBolum(url="test-url", title="Episode 1", anime=anime)
    video = AdapterVideo(bolum=bolum, url="http://player-url.com", label="1080p")

    assert video.bolum == bolum
    assert video.url == "http://player-url.com"
    assert video.label == "1080p"
    assert video.player == "ANIMECIX"
