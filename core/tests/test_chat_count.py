
import pytest
from channels.testing import WebsocketCommunicator
from aniscrap_core.asgi import application
from django.core.cache import cache

@pytest.mark.asyncio
@pytest.mark.django_db
async def test_chat_user_count():
    # Setup
    room_name = "test_room_count"

    # Clean cache key
    cache_key = f"chat_count_{room_name}"
    cache.delete(cache_key)

    # 1. Connect first user
    communicator1 = WebsocketCommunicator(application, f"/ws/chat/{room_name}/")
    connected1, _ = await communicator1.connect()
    assert connected1

    # User 1 should receive count = 1
    # We loop to find the 'user_count' message as other messages (history) might arrive
    found_count_1 = False
    for _ in range(10):
        try:
            response = await communicator1.receive_json_from(timeout=1)
            if response.get('type') == 'user_count' and response['count'] == 1:
                found_count_1 = True
                break
        except:
            break
    assert found_count_1, "User 1 did not receive count=1"

    # 2. Connect second user
    communicator2 = WebsocketCommunicator(application, f"/ws/chat/{room_name}/")
    connected2, _ = await communicator2.connect()
    assert connected2

    # User 1 should receive count = 2
    found_count_2_u1 = False
    for _ in range(10):
        try:
            response = await communicator1.receive_json_from(timeout=1)
            if response.get('type') == 'user_count' and response['count'] == 2:
                found_count_2_u1 = True
                break
        except:
            break
    assert found_count_2_u1, "User 1 did not receive count=2"

    # User 2 should receive count = 2
    found_count_2_u2 = False
    for _ in range(10):
        try:
            response = await communicator2.receive_json_from(timeout=1)
            if response.get('type') == 'user_count' and response['count'] == 2:
                found_count_2_u2 = True
                break
        except:
            break
    assert found_count_2_u2, "User 2 did not receive count=2"

    # 3. Disconnect User 2
    await communicator2.disconnect()

    # User 1 should receive count = 1
    found_count_1_u1 = False
    for _ in range(10):
        try:
            response = await communicator1.receive_json_from(timeout=1)
            if response.get('type') == 'user_count' and response['count'] == 1:
                found_count_1_u1 = True
                break
        except:
            break
    assert found_count_1_u1, "User 1 did not receive count=1 (disconnect)"

    # Cleanup
    await communicator1.disconnect()
