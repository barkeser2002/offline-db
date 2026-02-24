import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from content.models import Anime, Genre, Season, Episode

@pytest.mark.django_db
def test_home_view_performance(django_assert_num_queries):
    client = APIClient()
    try:
        url = reverse('home-list')
    except:
        # Fallback if reverse fails due to router config (though it seemed correct)
        url = '/api/v1/home/'

    # Create Genres
    g1 = Genre.objects.create(name='Action', slug='action')
    g2 = Genre.objects.create(name='Adventure', slug='adventure')

    # Create Trending Animes (10 items)
    for i in range(10):
        a = Anime.objects.create(
            title=f'Trending {i}',
            popularity=1000 - i,
            mal_id=i+1,
            score=9.0
        )
        a.genres.add(g1, g2)

    # Create Seasonal Animes (10 items)
    for i in range(10):
        a = Anime.objects.create(
            title=f'Seasonal {i}',
            status='Currently Airing',
            score=8.0 + (i * 0.1),
            mal_id=100+i
        )
        a.genres.add(g1, g2)

    # Create Latest Episodes (12 items)
    anime = Anime.objects.first()
    season = Season.objects.create(anime=anime, number=1)
    for i in range(12):
        Episode.objects.create(season=season, number=i+1, title=f'Ep {i+1}')

    # Initial request to warm up
    client.get(url)

    # Expectation:
    # 1 query for Trending Anime
    # 10 queries for Trending Genres (N+1)
    # 1 query for Seasonal Anime
    # 10 queries for Seasonal Genres (N+1)
    # 1 query for Latest Episodes
    # 1 query for Latest Episodes related (season__anime) - select_related
    # 1 query for video_files - prefetch_related
    # 1 query for external_sources - prefetch_related
    # Total roughly: 1 + 10 + 1 + 10 + 1 + 1 + 1 + 1 = 26 queries

    # If we optimize:
    # 1 query for Trending Anime + 1 query for Genres (prefetch)
    # 1 query for Seasonal Anime + 1 query for Genres (prefetch)
    # Total roughly: 2 + 2 + 4 = 8 queries.
    # Actual result is 7 queries.

    # I'll set a limit that should fail if N+1 is present.
    # 26 queries vs 7 queries.

    with django_assert_num_queries(7):
         res = client.get(url)
         assert res.status_code == 200
