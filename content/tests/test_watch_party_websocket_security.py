import pytest
from channels.testing import WebsocketCommunicator
from aniscrap_core.asgi import application

@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_connect_to_non_existent_party():
    # Attempt to connect to a non-existent party
    room_name = "00000000-0000-0000-0000-000000000000"
    communicator = WebsocketCommunicator(application, f"ws/watch-party/{room_name}/")

    from channels.exceptions import DenyConnection
    try:
        connected, subprotocol = await communicator.connect()
        assert connected is False, "Connection should be rejected for non-existent party"
    except DenyConnection:
        pass

    await communicator.disconnect()

@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_connect_unauthenticated():
    from channels.db import database_sync_to_async
    from django.contrib.auth import get_user_model
    from apps.watchparty.models import Room
    from content.models import Anime, Season, Episode
    User = get_user_model()

    @database_sync_to_async
    def create_room():
        user = User.objects.create_user(username='hostuser', password='password')
        anime = Anime.objects.create(title='Test Anime')
        season = Season.objects.create(anime=anime, number=1)
        episode = Episode.objects.create(season=season, number=1, title='Test Ep')
        room = Room.objects.create(episode=episode, host=user)
        return room

    room = await create_room()
    communicator = WebsocketCommunicator(application, f"ws/watch-party/{room.uuid}/")

    # We expect the connection to be rejected because user is unauthenticated
    from channels.exceptions import DenyConnection
    try:
        connected, subprotocol = await communicator.connect()
        assert connected is False, "Connection should be rejected for unauthenticated users"
    except DenyConnection:
        pass

    await communicator.disconnect()
