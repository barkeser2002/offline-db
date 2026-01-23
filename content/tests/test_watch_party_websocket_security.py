import pytest
from channels.testing import WebsocketCommunicator
from aniscrap_core.asgi import application

@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_connect_to_non_existent_party():
    # Attempt to connect to a non-existent party
    room_name = "party_nonexistentuuid"
    communicator = WebsocketCommunicator(application, f"ws/watch-party/{room_name}/")

    connected, subprotocol = await communicator.connect()

    # We expect the connection to be rejected (False) once fixed.
    # Currently, without the fix, this assertion will fail because it accepts the connection.
    assert connected is False, "Connection should be rejected for non-existent party"

    await communicator.disconnect()
