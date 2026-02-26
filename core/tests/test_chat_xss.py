from django.test import TransactionTestCase
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from django.urls import path
from channels.db import database_sync_to_async
from core.consumers import ChatConsumer
from core.models import ChatMessage
import pytest

@pytest.mark.asyncio
class ChatXSSTests(TransactionTestCase):
    async def test_xss_vulnerability(self):
        # Setup application router for testing
        application = URLRouter([
            path("ws/chat/<str:room_name>/", ChatConsumer.as_asgi()),
        ])

        room_name = "test_xss_room"
        communicator = WebsocketCommunicator(application, f"/ws/chat/{room_name}/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Consume initial user count message
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'user_count')

        # Send malicious payload
        payload = "<script>alert('XSS')</script>"
        await communicator.send_json_to({
            "message": payload,
            "username": "Attacker"
        })

        # Receive echo message
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'chat_message')

        # Verify if the message is escaped in the response
        # If vulnerable, response['message'] will be exactly payload
        # If fixed, it should be escaped (e.g. &lt;script&gt;...)

        # Check DB persistence
        @database_sync_to_async
        def get_saved_message():
            return ChatMessage.objects.filter(room_name=room_name).last()

        saved_msg = await get_saved_message()

        # Assertions
        # Currently expected to FAIL if we assert safe behavior, or PASS if we assert vulnerability
        # Let's assert that it IS escaped, so the test fails initially (TDD)
        from django.utils.html import escape
        expected_safe = escape(payload)

        self.assertEqual(response['message'], expected_safe, "Response message should be HTML escaped")
        self.assertEqual(saved_msg.message, expected_safe, "Saved message should be HTML escaped")

        await communicator.disconnect()
