import pytest
from django.core.cache import cache
from django.urls import reverse
from content.models import Genre, Anime, Season, Episode

@pytest.mark.django_db
class TestCaching:

    def test_genre_signal_clears_cache(self):
        cache.set('all_genres', ['fake_data'])

        # Creating a genre should clear cache
        Genre.objects.create(name='Comedy', slug='comedy')

        assert cache.get('all_genres') is None

    def test_episode_signal_clears_anime_cache(self):
        anime = Anime.objects.create(title='Test Anime 2')
        season = Season.objects.create(anime=anime, number=1)

        cache_key = f'anime_{anime.id}_seasons'
        cache.set(cache_key, ['fake_data'])

        # Creating episode should clear cache
        Episode.objects.create(season=season, number=1)

        assert cache.get(cache_key) is None

    def test_season_signal_clears_anime_cache(self):
        anime = Anime.objects.create(title='Test Anime 3')

        cache_key = f'anime_{anime.id}_seasons'
        cache.set(cache_key, ['fake_data'])

        # Creating season should clear cache
        Season.objects.create(anime=anime, number=2)

        assert cache.get(cache_key) is None
