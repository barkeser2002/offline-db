from django.test import TransactionTestCase
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from django.urls import path
from django.core.cache import cache
from core.consumers import ChatConsumer
import json

class ChatSecurityTests(TransactionTestCase):
    def setUp(self):
        cache.clear()

    async def test_chat_rate_limiting(self):
        application = URLRouter([
            path("ws/chat/<str:room_name>/", ChatConsumer.as_asgi()),
        ])

        room_name = "security_room"
        communicator = WebsocketCommunicator(application, f"/ws/chat/{room_name}/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Consume initial user count
        await communicator.receive_json_from()

        # Send 5 messages (Allowed limit)
        for i in range(5):
            await communicator.send_json_to({"message": f"msg {i}", "username": "tester"})
            response = await communicator.receive_json_from()
            self.assertEqual(response['type'], 'chat_message')

        # Send 6th message immediately - should trigger limit and close connection
        await communicator.send_json_to({"message": "spam", "username": "tester"})

        # We expect the connection to be closed
        # receive_output() returns the next raw ASGI message
        event = await communicator.receive_output()
        self.assertEqual(event['type'], 'websocket.close')

        await communicator.disconnect()
