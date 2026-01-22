import pytest
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from content.models import WatchParty, Episode, Season, Anime
from core.models import ChatMessage
from content.consumers import WatchPartyConsumer
from aniscrap_core.asgi import application

User = get_user_model()

@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_watch_party_chat_persistence():
    # Setup Data
    user = await database_sync_to_async(User.objects.create_user)(username='testuser', password='password')
    anime = await database_sync_to_async(Anime.objects.create)(title="Test Anime")
    season = await database_sync_to_async(Season.objects.create)(anime=anime, number=1)
    episode = await database_sync_to_async(Episode.objects.create)(season=season, number=1)

    # Create Watch Party
    party = await database_sync_to_async(WatchParty.objects.create)(episode=episode, host=user)

    room_name = f"party_{party.uuid}"

    # Connect to WebSocket
    communicator = WebsocketCommunicator(application, f"/ws/watch-party/{room_name}/")
    communicator.scope['user'] = user
    connected, subprotocol = await communicator.connect()
    assert connected

    # Receive Join Message (System)
    response = await communicator.receive_json_from()
    assert response['type'] == 'user_count'

    response = await communicator.receive_json_from()
    assert response['type'] == 'chat_message'
    assert response['is_system'] is True
    assert "joined the party" in response['message']

    # Send Chat Message
    await communicator.send_json_to({
        'message': 'Hello World'
    })

    # Receive Echo
    response = await communicator.receive_json_from()
    assert response['type'] == 'chat_message'
    assert response['message'] == 'Hello World'
    assert response['username'] == 'testuser'

    # Verify Persistence
    assert await ChatMessage.objects.filter(room_name=room_name, message='Hello World').aexists()

    await communicator.disconnect()

    # Test History Retrieval
    communicator2 = WebsocketCommunicator(application, f"/ws/watch-party/{room_name}/")
    communicator2.scope['user'] = user
    connected, subprotocol = await communicator2.connect()
    assert connected

    # Should receive history first (direct send vs group send race)
    response = await communicator2.receive_json_from()
    assert response['type'] == 'chat_message'
    assert response['message'] == 'Hello World'
    assert response['username'] == 'testuser'

    # Then group messages
    response = await communicator2.receive_json_from()
    assert response['type'] == 'user_count'

    response = await communicator2.receive_json_from()
    assert response['type'] == 'chat_message'
    assert response['is_system'] is True

    await communicator2.disconnect()
