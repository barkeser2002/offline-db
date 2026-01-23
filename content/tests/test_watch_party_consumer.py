import pytest
from channels.testing import WebsocketCommunicator
from aniscrap_core.asgi import application
from content.models import WatchParty, Episode, Season, Anime
from users.models import User
from channels.db import database_sync_to_async

@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_watch_party_connection():
    # Setup
    user = await database_sync_to_async(User.objects.create_user)(username='host', password='password')
    anime = await database_sync_to_async(Anime.objects.create)(title="Test Anime")
    season = await database_sync_to_async(Season.objects.create)(anime=anime, number=1)
    episode = await database_sync_to_async(Episode.objects.create)(season=season, number=1)
    party = await database_sync_to_async(WatchParty.objects.create)(episode=episode, host=user)

    room_name = f"party_{party.uuid}"

    # Connect
    communicator = WebsocketCommunicator(application, f"ws/watch-party/{room_name}/")
    communicator.scope["user"] = user
    connected, _ = await communicator.connect()
    assert connected

    # Receive user count message first
    msg = await communicator.receive_json_from()
    assert msg['type'] == 'user_count'

    # Receive join message
    msg = await communicator.receive_json_from()
    assert msg['type'] == 'chat_message'
    assert 'joined the party' in msg['message']

    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_typing_indicator():
    # Setup
    user = await database_sync_to_async(User.objects.create_user)(username='typer', password='password')
    anime = await database_sync_to_async(Anime.objects.create)(title="Test Anime")
    season = await database_sync_to_async(Season.objects.create)(anime=anime, number=1)
    episode = await database_sync_to_async(Episode.objects.create)(season=season, number=1)
    party = await database_sync_to_async(WatchParty.objects.create)(episode=episode, host=user)

    room_name = f"party_{party.uuid}"

    # Connect
    communicator = WebsocketCommunicator(application, f"ws/watch-party/{room_name}/")
    communicator.scope["user"] = user
    connected, _ = await communicator.connect()
    assert connected

    # Consume initial messages
    await communicator.receive_json_from() # user count
    await communicator.receive_json_from() # join message

    # Send typing start
    await communicator.send_json_to({
        'type': 'typing',
        'is_typing': True
    })

    # Receive typing start
    response = await communicator.receive_json_from()
    assert response['type'] == 'typing'
    assert response['username'] == 'typer'
    assert response['is_typing'] is True

    # Send typing stop
    await communicator.send_json_to({
        'type': 'typing',
        'is_typing': False
    })

    # Receive typing stop
    response = await communicator.receive_json_from()
    assert response['type'] == 'typing'
    assert response['username'] == 'typer'
    assert response['is_typing'] is False

    await communicator.disconnect()
