import pytest
from django.core.cache import cache
from django.urls import reverse
from content.models import Genre, Anime, Season, Episode

@pytest.mark.django_db
class TestCaching:

    def test_search_view_caches_genres(self, client):
        # Clear cache first
        cache.delete('all_genres')

        # Create some genres
        Genre.objects.create(name='Action', slug='action')
        Genre.objects.create(name='Adventure', slug='adventure')

        # First request should populate cache
        response = client.get(reverse('search'))
        assert response.status_code == 200

        # Verify cache is populated
        cached_genres = cache.get('all_genres')
        assert cached_genres is not None
        assert len(cached_genres) == 2
        assert cached_genres[0].name in ['Action', 'Adventure']

    def test_genre_signal_clears_cache(self):
        cache.set('all_genres', ['fake_data'])

        # Creating a genre should clear cache
        Genre.objects.create(name='Comedy', slug='comedy')

        assert cache.get('all_genres') is None

    def test_anime_detail_caches_seasons(self, client):
        # Setup
        anime = Anime.objects.create(title='Test Anime')
        season = Season.objects.create(anime=anime, number=1)
        Episode.objects.create(season=season, number=1)

        cache_key = f'anime_{anime.id}_seasons'
        cache.delete(cache_key)

        # First request
        response = client.get(reverse('anime_detail', args=[anime.id]))
        assert response.status_code == 200

        # Check cache
        cached_seasons = cache.get(cache_key)
        assert cached_seasons is not None
        assert len(cached_seasons) == 1
        # Accessing episodes should not trigger new DB queries if prefetched correctly,
        # but here we just check correctness of data
        assert cached_seasons[0].episodes.count() == 1

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
