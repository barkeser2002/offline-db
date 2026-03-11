import pytest
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from django.core.cache import cache
from apps.watchparty.consumers import WatchPartyConsumer
from apps.watchparty.models import Room
from content.models import Anime, Season, Episode

User = get_user_model()

@database_sync_to_async
def create_test_data():
    user = User.objects.create_user(username='attacker', password='password')
    anime = Anime.objects.create(title='Test Anime')
    season = Season.objects.create(anime=anime, number=1)
    episode = Episode.objects.create(season=season, number=1, title='Test Ep')
    room = Room.objects.create(episode=episode, host=user)
    return user, room

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_emote_dos_rate_limiting():
    # Setup Data
    user, room = await create_test_data()
    cache.clear()

    # Initialize Communicator
    communicator = WebsocketCommunicator(
        WatchPartyConsumer.as_asgi(),
        f"/ws/watch-party/{room.uuid}/"
    )
    # Manually inject user into scope since we bypass middleware stack
    communicator.scope["user"] = user
    communicator.scope["url_route"] = {
        "kwargs": {"room_name": str(room.uuid)}
    }

    connected, subprotocol = await communicator.connect()
    assert connected

    # Consume system messages (join message and participants list)
    await communicator.receive_json_from()
    await communicator.receive_json_from()

    # Payload
    emote_payload = "😂"

    # Send Emote Messages rapidly
    for i in range(15):
        await communicator.send_json_to({
            "type": "emote",
            "emote": emote_payload
        })

    # Receive Broadcast
    received_emotes = 0
    import asyncio
    try:
        while True:
            response = await communicator.receive_json_from(timeout=1.0)
            if response["type"] == "emote_rain":
                received_emotes += 1
            if received_emotes == 10:
                break
    except asyncio.TimeoutError:
        pass

    assert received_emotes == 10

    await communicator.disconnect()
