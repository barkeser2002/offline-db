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
import pytest
from django.urls import reverse
from rest_framework.test import APIClient

@pytest.mark.django_db
def test_profile_patch_bio_and_username(django_user_model):
    client = APIClient()
    user = django_user_model.objects.create_user(username='testuser', password='password', bio='old bio')
    client.force_authenticate(user=user)
    url = reverse('user-profile')

    data = {
        'bio': '<script>alert("xss")</script><b>new bio</b>',
        'username': 'new_user_name'
    }

    response = client.patch(url, data, format='json')
    assert response.status_code == 200

    user.refresh_from_db()
    assert user.bio == 'alert("xss")new bio' # bleach strips tags but keeps text content
    assert user.username == 'new_user_name'

@pytest.mark.django_db
def test_profile_patch_invalid_username(django_user_model):
    client = APIClient()
    user = django_user_model.objects.create_user(username='testuser', password='password')
    client.force_authenticate(user=user)
    url = reverse('user-profile')

    data = {
        'username': 'invalid username!'
    }

    response = client.patch(url, data, format='json')
    assert response.status_code == 400
    assert 'error' in response.json()
    assert 'alphanumeric' in response.json()['error']

    user.refresh_from_db()
    assert user.username == 'testuser'

@pytest.mark.django_db
def test_profile_patch_duplicate_username(django_user_model):
    client = APIClient()
    django_user_model.objects.create_user(username='existinguser', password='password')
    user = django_user_model.objects.create_user(username='testuser', password='password')
    client.force_authenticate(user=user)
    url = reverse('user-profile')

    data = {
        'username': 'existinguser'
    }

    response = client.patch(url, data, format='json')
    assert response.status_code == 400
    assert 'error' in response.json()
    assert 'already taken' in response.json()['error']

    user.refresh_from_db()
    assert user.username == 'testuser'
