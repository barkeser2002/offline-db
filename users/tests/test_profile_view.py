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
    response = client.get(url, secure=True)
    assert response.status_code == 200

@pytest.mark.django_db
def test_profile_view_redirect_anonymous():
    """Test that anonymous users are redirected to login."""
    client = APIClient()
    url = reverse('user-profile')
    response = client.get(url, secure=True)
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
    response = client.get(url, secure=True)

    assert response.status_code == 200
    # Check that Test Badge is present (other badges might be awarded automatically via signals)
    data = response.json()
    assert any(b['badge']['name'] == "Test Badge" for b in data['badges'])
    assert len(data['recent_history']) == 1
    # Check that episode is related correctly
    assert data['recent_history'][0]['episode'] == episode.id
    assert 'bio' in data

@pytest.mark.django_db
def test_profile_update_bio(django_user_model):
    """Test that users can update their bio."""
    client = APIClient()
    user = django_user_model.objects.create_user(username='testuser_bio', password='password')
    client.force_authenticate(user=user)

    url = reverse('user-profile')

    # Update bio using PATCH
    data = {'bio': 'This is my new bio.'}
    response = client.patch(url, data, format='json', secure=True)
    assert response.status_code == 200
    assert response.json()['bio'] == 'This is my new bio.'

    # Verify bio was saved in the database
    user.refresh_from_db()
    assert user.bio == 'This is my new bio.'

@pytest.mark.django_db
def test_profile_update_bio_sanitization(django_user_model):
    """Test that HTML tags in bio are stripped."""
    client = APIClient()
    user = django_user_model.objects.create_user(username='testuser_bio_san', password='password')
    client.force_authenticate(user=user)

    url = reverse('user-profile')

    # Attempt to inject XSS in bio
    malicious_bio = '<script>alert("xss")</script><b>Hello</b>'
    data = {'bio': malicious_bio}
    response = client.patch(url, data, format='json', secure=True)

    assert response.status_code == 200
    # bleach.clean with strip=True should remove the tags entirely
    assert response.json()['bio'] == 'alert("xss")Hello'

    # Verify sanitized bio was saved
    user.refresh_from_db()
    assert user.bio == 'alert("xss")Hello'
