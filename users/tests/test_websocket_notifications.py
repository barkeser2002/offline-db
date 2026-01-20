from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from content.models import Anime, Season, Episode, Subscription
from aniscrap_core.asgi import application
import json

User = get_user_model()

class NotificationWebSocketTests(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='ws_user', password='password')
        self.anime = Anime.objects.create(title='WS Anime')
        self.season = Season.objects.create(anime=self.anime, number=1)
        self.subscription = Subscription.objects.create(user=self.user, anime=self.anime)

    async def test_notification_sent_via_websocket(self):
        # Establish WebSocket connection
        communicator = WebsocketCommunicator(application, "ws/notifications/")
        communicator.scope["user"] = self.user
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Trigger signal by creating an episode (needs to run in sync mode for db access within signal,
        # but TransactionTestCase allows async test methods)
        # However, the signal handler calls async_to_sync(channel_layer.group_send), which works fine.

        # We need to run the creation in a sync context or use database_sync_to_async if we were inside the consumer,
        # but here we are in the test.
        # Since we are using TransactionTestCase, we can use ORM directly?
        # No, for async tests we should wrap DB operations.

        from channels.db import database_sync_to_async

        @database_sync_to_async
        def create_episode():
             Episode.objects.create(season=self.season, number=2, title='WS Episode')

        await create_episode()

        # Check for message
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'notification')
        self.assertEqual(response['title'], f"New Episode: {self.anime.title}")
        self.assertIn("Episode 2", response['message'])

        await communicator.disconnect()

    async def test_websocket_rejects_unauthenticated(self):
        communicator = WebsocketCommunicator(application, "ws/notifications/")
        # No user in scope, or AnonymousUser
        from django.contrib.auth.models import AnonymousUser
        communicator.scope["user"] = AnonymousUser()

        connected, _ = await communicator.connect()
        self.assertFalse(connected)
