import pytest
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
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
async def test_chat_message_xss_vulnerability():
    # Setup Data
    user, room = await create_test_data()

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
    # Expect "X joined"
    msg1 = await communicator.receive_json_from()
    # Expect participants list
    msg2 = await communicator.receive_json_from()

    # Payload
    xss_payload = "<script>alert('pwned')</script>"

    # Send Chat Message
    await communicator.send_json_to({
        "type": "chat",
        "message": xss_payload
    })

    # Receive Broadcast
    response = await communicator.receive_json_from()

    # Assertions
    assert response["type"] == "chat_message"
    assert response["username"] == "attacker"

    # If vulnerable, the message will contain the raw script tag
    if "<script>" in response["message"]:
        print("\n[VULNERABILITY CONFIRMED] Chat message contains raw HTML/Script tags.")
    else:
        print("\n[SECURE] Chat message appears to be sanitized.")

    # We expect it to be sanitized (escaped)
    assert "&lt;script&gt;" in response["message"]
    assert "<script>" not in response["message"]

    await communicator.disconnect()
