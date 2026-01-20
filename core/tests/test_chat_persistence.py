from django.test import TransactionTestCase
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from channels.db import database_sync_to_async
from django.urls import path
from core.consumers import ChatConsumer
from core.models import ChatMessage
import json

class ChatPersistenceTests(TransactionTestCase):
    async def test_chat_persistence_and_history(self):
        # Create a router
        application = URLRouter([
            path("ws/chat/<str:room_name>/", ChatConsumer.as_asgi()),
        ])

        room_name = "testroom_persist"

        # 1. Connect and send a message
        communicator1 = WebsocketCommunicator(application, f"/ws/chat/{room_name}/")
        connected1, subprotocol1 = await communicator1.connect()
        self.assertTrue(connected1)

        # Consume initial user count
        response_count = await communicator1.receive_json_from()
        self.assertEqual(response_count['type'], 'user_count')

        await communicator1.send_json_to({
            "message": "Hello World",
            "username": "User1"
        })

        # Verify echo
        response1 = await communicator1.receive_json_from()
        self.assertEqual(response1['message'], 'Hello World')
        self.assertEqual(response1['username'], 'User1')

        await communicator1.disconnect()

        # 2. Check DB
        @database_sync_to_async
        def check_db():
             return ChatMessage.objects.filter(room_name=room_name, message="Hello World").exists()

        self.assertTrue(await check_db(), "Message should be saved to DB")

        # 3. Connect as new user and check history
        communicator2 = WebsocketCommunicator(application, f"/ws/chat/{room_name}/")
        connected2, subprotocol2 = await communicator2.connect()
        self.assertTrue(connected2)

        # Should receive the history message immediately, but might be interleaved with user_count
        found_history = False
        for _ in range(5):
            response = await communicator2.receive_json_from()
            if response.get('type') == 'chat_message' and response.get('message') == 'Hello World':
                found_history = True
                self.assertEqual(response['username'], 'User1')
                self.assertIn('created_at', response)
                break

        self.assertTrue(found_history, "Did not receive history message")

        await communicator2.disconnect()
