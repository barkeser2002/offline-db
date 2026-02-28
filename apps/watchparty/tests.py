import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.watchparty.models import Room
from content.models import Anime, Season, Episode, VideoFile, ExternalSource, FansubGroup
from django.test.utils import CaptureQueriesContext
from django.db import connection

User = get_user_model()

@pytest.mark.django_db
def test_room_list_queries():
    # Setup data
    user = User.objects.create_user(username='testuser', password='password')
    fansub = FansubGroup.objects.create(name='TestFansub')
    anime = Anime.objects.create(title='Test Anime')
    season = Season.objects.create(anime=anime, number=1)

    for i in range(10):
        episode = Episode.objects.create(season=season, number=i, title=f'Episode {i}')
        VideoFile.objects.create(episode=episode, quality='1080p', fansub_group=fansub, hls_path=f'path{i}')
        ExternalSource.objects.create(episode=episode, source_type='hianime', embed_url=f'http://example.com/{i}')
        Room.objects.create(episode=episode, host=user)

    client = Client()
    # Let's try to find the correct URL name
    url = reverse('room-list')

    # Warm up
    client.get(url)

    with CaptureQueriesContext(connection) as queries:
        response = client.get(url)

    assert response.status_code == 200
    print(f"\nNumber of queries for 10 rooms: {len(queries)}")
    for i, q in enumerate(queries):
        print(f"Query {i+1}: {q['sql'][:100]}...")

    # For 10 rooms:
    # 1. SELECT rooms
    # 10 * (
    #   SELECT host
    #   SELECT episode
    #   SELECT video_files
    #   SELECT external_sources
    #   FOR EACH video_file (1 here):
    #     SELECT fansub_group
    # )
    # Total expected: 1 + 10 * (1 + 1 + 1 + 1 + 1) = 51 queries?
    # Actually VideoFileSerializer and ExternalSourceSerializer are used inside EpisodeSerializer.

@pytest.mark.django_db
def test_room_host_authorization():
    # Setup data
    host_user = User.objects.create_user(username='hostuser', password='password')
    other_user = User.objects.create_user(username='otheruser', password='password')
    anime = Anime.objects.create(title='Test Anime')
    season = Season.objects.create(anime=anime, number=1)
    episode = Episode.objects.create(season=season, number=1, title='Episode 1')

    room = Room.objects.create(episode=episode, host=host_user)

    client = Client()
    url = reverse('room-detail', kwargs={'pk': room.uuid})

    # 1. Test unauthenticated access (should not be able to patch)
    response = client.patch(url, {'is_active': False}, content_type='application/json')
    assert response.status_code == 401 # Unauthorized

    # 2. Test authenticated but not host access (should be forbidden)
    client.force_login(other_user)
    response = client.patch(url, {'is_active': False}, content_type='application/json')
    assert response.status_code == 403 # Forbidden

    # Verify is_active wasn't changed
    room.refresh_from_db()
    assert room.is_active is True

    # 3. Test host access (should be allowed)
    client.force_login(host_user)
    response = client.patch(url, {'is_active': False}, content_type='application/json')
    assert response.status_code == 200 # OK

    # Verify is_active was changed
    room.refresh_from_db()
    assert room.is_active is False
