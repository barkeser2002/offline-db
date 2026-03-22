import pytest
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from apps.watchparty.models import Room, Participant
from content.models import Anime, Season, Episode
from asgiref.sync import sync_to_async
from django.urls import path
from apps.watchparty.consumers import WatchPartyConsumer
import uuid

User = get_user_model()

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_max_participants_limit():
    user1 = await sync_to_async(User.objects.create_user)(username='user1', password='p')
    user2 = await sync_to_async(User.objects.create_user)(username='user2', password='p')
    user3 = await sync_to_async(User.objects.create_user)(username='user3', password='p')

    anime = await sync_to_async(Anime.objects.create)(title="Test Anime")
    season = await sync_to_async(Season.objects.create)(anime=anime, number=1)
    episode = await sync_to_async(Episode.objects.create)(season=season, number=1)

    # room with max 2 participants (host + 1 viewer)
    room = await sync_to_async(Room.objects.create)(host=user1, episode=episode, max_participants=2)

    from aniscrap_core.asgi import application

    # Communicator 1: host connects
    comm1 = WebsocketCommunicator(application, f"/ws/watch-party/{room.uuid}/")
    comm1.scope["user"] = user1
    connected1, _ = await comm1.connect()
    assert connected1

    # Communicator 2: viewer 1 connects
    comm2 = WebsocketCommunicator(application, f"/ws/watch-party/{room.uuid}/")
    comm2.scope["user"] = user2
    connected2, _ = await comm2.connect()
    assert connected2

    # Communicator 3: viewer 2 connects (should be denied)
    comm3 = WebsocketCommunicator(application, f"/ws/watch-party/{room.uuid}/")
    comm3.scope["user"] = user3
    connected3, _ = await comm3.connect()
    assert not connected3

    # Disconnect everyone
    await comm1.disconnect()
    await comm2.disconnect()
    await comm3.disconnect()

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_max_participants_no_limit():
    user1 = await sync_to_async(User.objects.create_user)(username='user1', password='p')
    user2 = await sync_to_async(User.objects.create_user)(username='user2', password='p')
    user3 = await sync_to_async(User.objects.create_user)(username='user3', password='p')

    anime = await sync_to_async(Anime.objects.create)(title="Test Anime")
    season = await sync_to_async(Season.objects.create)(anime=anime, number=1)
    episode = await sync_to_async(Episode.objects.create)(season=season, number=1)

    # room with NO limit (max_participants=0)
    room = await sync_to_async(Room.objects.create)(host=user1, episode=episode, max_participants=0)

    from aniscrap_core.asgi import application

    comm1 = WebsocketCommunicator(application, f"/ws/watch-party/{room.uuid}/")
    comm1.scope["user"] = user1
    connected1, _ = await comm1.connect()
    assert connected1

    comm2 = WebsocketCommunicator(application, f"/ws/watch-party/{room.uuid}/")
    comm2.scope["user"] = user2
    connected2, _ = await comm2.connect()
    assert connected2

    comm3 = WebsocketCommunicator(application, f"/ws/watch-party/{room.uuid}/")
    comm3.scope["user"] = user3
    connected3, _ = await comm3.connect()
    assert connected3

    await comm1.disconnect()
    await comm2.disconnect()
    await comm3.disconnect()
