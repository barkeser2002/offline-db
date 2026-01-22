from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from aniscrap_core.asgi import application
from asgiref.sync import sync_to_async

User = get_user_model()

class ChatConsumerTests(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='chat_user', password='password')
        self.room_name = 'test_room'

    async def test_join_message(self):
        # Connect
        communicator = WebsocketCommunicator(application, f"ws/chat/{self.room_name}/")
        communicator.scope["user"] = self.user
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Expect user count update
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'user_count')

        # Expect "User joined" system message
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'chat_message')
        self.assertEqual(response['username'], 'System')
        self.assertTrue(response['is_system'])
        self.assertIn("chat_user joined the chat", response['message'])

        await communicator.disconnect()

    async def test_user_left_message(self):
        # User 1 connects
        communicator1 = WebsocketCommunicator(application, f"ws/chat/{self.room_name}/")
        communicator1.scope["user"] = self.user
        await communicator1.connect()

        # User 1 receives count and join message
        await communicator1.receive_json_from() # count
        await communicator1.receive_json_from() # join

        # User 2 connects
        user2 = await sync_to_async(User.objects.create_user)(username='chat_user_2', password='password')
        communicator2 = WebsocketCommunicator(application, f"ws/chat/{self.room_name}/")
        communicator2.scope["user"] = user2
        await communicator2.connect()

        # User 1 receives count update (for User 2 joining)
        response = await communicator1.receive_json_from()
        self.assertEqual(response['type'], 'user_count')

        # User 1 receives "User 2 joined"
        response = await communicator1.receive_json_from()
        self.assertEqual(response['type'], 'chat_message')
        self.assertEqual(response['username'], 'System')
        self.assertTrue(response['is_system'])
        self.assertIn("chat_user_2 joined the chat", response['message'])

        # User 2 disconnects
        await communicator2.disconnect()

        # User 1 receives count update (for User 2 leaving)
        response = await communicator1.receive_json_from()
        self.assertEqual(response['type'], 'user_count')

        # User 1 receives "User 2 left"
        response = await communicator1.receive_json_from()
        self.assertEqual(response['type'], 'chat_message')
        self.assertEqual(response['username'], 'System')
        self.assertTrue(response['is_system'])
        self.assertIn("chat_user_2 left the chat", response['message'])

        await communicator1.disconnect()
