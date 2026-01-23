import pytest
from django.urls import reverse
from users.models import UserBadge, Badge, WatchLog
from content.models import Anime, Episode, Season

@pytest.mark.django_db
def test_profile_view_access(client, django_user_model):
    """Test that the profile view returns 200 for logged-in users."""
    user = django_user_model.objects.create_user(username='testuser', password='password')
    client.force_login(user)
    url = reverse('profile')
    response = client.get(url)
    assert response.status_code == 200
    assert 'profile.html' in [t.name for t in response.templates]

@pytest.mark.django_db
def test_profile_view_redirect_anonymous(client):
    """Test that anonymous users are redirected to login."""
    url = reverse('profile')
    response = client.get(url)
    assert response.status_code == 302

@pytest.mark.django_db
def test_profile_view_context(client, django_user_model):
    """Test that badges and history are passed to the context."""
    user = django_user_model.objects.create_user(username='testuser2', password='password')
    client.force_login(user)

    # Create a badge and award it
    badge = Badge.objects.create(name="Test Badge", slug="test-badge")
    UserBadge.objects.create(user=user, badge=badge)

    # Create some history
    anime = Anime.objects.create(title="Test Anime")
    season = Season.objects.create(anime=anime, number=1)
    episode = Episode.objects.create(season=season, number=1)
    WatchLog.objects.create(user=user, episode=episode, duration=100)

    url = reverse('profile')
    response = client.get(url)

    assert response.status_code == 200
    # Check that Test Badge is present (other badges might be awarded automatically via signals)
    assert any(b.badge.name == "Test Badge" for b in response.context['badges'])
    assert len(response.context['history']) == 1
    # Check that episode is related correctly
    assert response.context['history'][0].episode == episode
