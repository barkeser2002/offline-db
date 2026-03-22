import pytest
from django.urls import reverse
from users.models import UserBadge, Badge, WatchLog
from content.models import Anime, Episode, Season

from rest_framework.test import APIClient

@pytest.mark.django_db
def test_profile_view_access(django_user_model):
    """Test that the profile view returns 200 for logged-in users."""
    client = APIClient()
    user = django_user_model.objects.create_user(username='testuser', password='password')
    client.force_authenticate(user=user)
    url = reverse('user-profile')
    response = client.get(url)
    assert response.status_code == 200

@pytest.mark.django_db
def test_profile_view_redirect_anonymous():
    """Test that anonymous users are redirected to login."""
    client = APIClient()
    url = reverse('user-profile')
    response = client.get(url)
    assert response.status_code == 401

@pytest.mark.django_db
def test_profile_view_context(django_user_model):
    """Test that badges and history are passed to the context."""
    client = APIClient()
    user = django_user_model.objects.create_user(username='testuser2', password='password')
    client.force_authenticate(user=user)

    # Create a badge and award it
    badge = Badge.objects.create(name="Test Badge", slug="test-badge")
    UserBadge.objects.create(user=user, badge=badge)

    # Create some history
    anime = Anime.objects.create(title="Test Anime")
    season = Season.objects.create(anime=anime, number=1)
    episode = Episode.objects.create(season=season, number=1)
    WatchLog.objects.create(user=user, episode=episode, duration=100)

    url = reverse('user-profile')
    response = client.get(url)

    assert response.status_code == 200
    # Check that Test Badge is present (other badges might be awarded automatically via signals)
    data = response.json()
    assert any(b['badge']['name'] == "Test Badge" for b in data['badges'])
    assert len(data['recent_history']) == 1
    # Check that episode is related correctly
    assert data['recent_history'][0]['episode'] == episode.id

@pytest.mark.django_db
def test_profile_update_bio_xss_protection(django_user_model):
    """Test that a user can update their bio and XSS payloads are sanitized."""
    client = APIClient()
    user = django_user_model.objects.create_user(username='xsstester', password='password')
    client.force_authenticate(user=user)

    url = reverse('user-profile')
    malicious_bio = '<script>alert("xss")</script>This is my <b>bio</b>.'

    # Send a PATCH request to update the bio
    response = client.patch(url, {'bio': malicious_bio}, format='json')

    assert response.status_code == 200

    # Reload user and check sanitized bio
    user.refresh_from_db()
    assert user.bio == 'alert("xss")This is my bio.'
    assert response.json()['bio'] == 'alert("xss")This is my bio.'
