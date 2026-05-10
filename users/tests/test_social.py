import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from users.models import User, Follow, UserAnimeList, WatchLog, UserBadge, Badge
from content.models import Anime, Episode, Season

@pytest.fixture
def client():
    return APIClient()

@pytest.fixture
def user1():
    return User.objects.create_user(username='user1', password='password123', is_public=True)

@pytest.fixture
def user2():
    return User.objects.create_user(username='user2', password='password123', is_public=False)

@pytest.fixture
def anime1():
    return Anime.objects.create(title='Anime 1', type='TV')

@pytest.mark.django_db
def test_follow_user(client, user1, user2):
    client.force_authenticate(user=user1)
    response = client.post(reverse('follow-list'), {'following': user2.id})
    assert response.status_code == 201
    assert Follow.objects.filter(follower=user1, following=user2).exists()

@pytest.mark.django_db
def test_cannot_follow_self(client, user1):
    client.force_authenticate(user=user1)
    response = client.post(reverse('follow-list'), {'following': user1.id})
    assert response.status_code == 400

@pytest.mark.django_db
def test_unfollow_user(client, user1, user2):
    Follow.objects.create(follower=user1, following=user2)
    client.force_authenticate(user=user1)
    response = client.post(reverse('follow-unfollow'), {'following_id': user2.id})
    assert response.status_code == 200
    assert not Follow.objects.filter(follower=user1, following=user2).exists()

@pytest.mark.django_db
def test_anime_list_create(client, user1, anime1):
    client.force_authenticate(user=user1)
    response = client.post(reverse('anime-list-list'), {'anime': anime1.id, 'status': 'completed'})
    assert response.status_code == 201
    assert UserAnimeList.objects.filter(user=user1, anime=anime1, status='completed').exists()

@pytest.mark.django_db
def test_anime_list_view_public(client, user1, user2, anime1):
    UserAnimeList.objects.create(user=user1, anime=anime1, status='watchlist')
    client.force_authenticate(user=user2)
    response = client.get(reverse('anime-list-list') + f'?user_id={user1.id}')
    assert response.status_code == 200
    assert len(response.data.get('results', response.data)) == 1

@pytest.mark.django_db
def test_anime_list_view_private_not_following(client, user1, user2, anime1):
    UserAnimeList.objects.create(user=user2, anime=anime1, status='watchlist')
    client.force_authenticate(user=user1)
    response = client.get(reverse('anime-list-list') + f'?user_id={user2.id}')
    # user2 is private, user1 doesn't follow user2
    assert response.status_code == 200
    assert len(response.data.get('results', response.data)) == 0

@pytest.mark.django_db
def test_anime_list_view_private_following(client, user1, user2, anime1):
    UserAnimeList.objects.create(user=user2, anime=anime1, status='watchlist')
    Follow.objects.create(follower=user1, following=user2)
    client.force_authenticate(user=user1)
    response = client.get(reverse('anime-list-list') + f'?user_id={user2.id}')
    # user2 is private, but user1 follows user2
    assert response.status_code == 200
    assert len(response.data.get('results', response.data)) == 1

@pytest.mark.django_db
def test_activity_feed(client, user1, user2, anime1):
    Follow.objects.create(follower=user1, following=user2)

    badge = Badge.objects.create(slug='test-badge', name='Test Badge')
    UserBadge.objects.create(user=user2, badge=badge)

    season = Season.objects.create(anime=anime1, number=1)
    episode = Episode.objects.create(season=season, number=1)
    WatchLog.objects.create(user=user2, episode=episode, duration=100)

    client.force_authenticate(user=user1)
    response = client.get(reverse('activity-feed-list'))

    assert response.status_code == 200
    assert len(response.data) == 2
    types = [x['activity_type'] for x in response.data]
    assert 'badge_earned' in types
    assert 'episode_watched' in types
