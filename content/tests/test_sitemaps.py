import pytest
from django.urls import reverse
from content.models import Anime, Season, Episode
from django.utils import timezone

@pytest.mark.django_db
def test_sitemap_status_code(client):
    """Test that sitemap.xml returns a 200 OK status."""
    url = reverse('django.contrib.sitemaps.views.sitemap')
    response = client.get(url)
    assert response.status_code == 200

@pytest.mark.django_db
def test_sitemap_content(client):
    """Test that sitemap contains URLs for Anime and Episodes."""
    # Create test data
    anime = Anime.objects.create(title="Test Anime", synopsis="Test Synopsis")
    season = Season.objects.create(anime=anime, number=1, title="Season 1")
    episode = Episode.objects.create(season=season, number=1, title="Episode 1")

    url = reverse('django.contrib.sitemaps.views.sitemap')
    response = client.get(url)

    assert response.status_code == 200
    content = response.content.decode('utf-8')

    # Check if URLs are present in the sitemap
    assert anime.get_absolute_url() in content
    assert episode.get_absolute_url() in content
