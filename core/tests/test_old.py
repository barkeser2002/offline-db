from django.test import TestCase, RequestFactory, TransactionTestCase
from content.models import Anime, Season, Episode, VideoFile
from core.dashboard import dashboard_callback
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from django.urls import path
from core.consumers import ChatConsumer

class DashboardTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_dashboard_stats_bandwidth(self):
        # Setup data
        anime = Anime.objects.create(title="Test Anime")
        season = Season.objects.create(anime=anime, number=1)
        episode = Episode.objects.create(season=season, number=1)

        # 1 GB file
        file_size = 1024 * 1024 * 1024
        VideoFile.objects.create(
            episode=episode,
            quality='1080p',
            hls_path='/tmp/test.m3u8',
            encryption_key='testkey',
            file_size_bytes=file_size
        )

        request = self.factory.get('/')
        context = {}

        # Call function
        updated_context = dashboard_callback(request, context)

        # Verify
        stats = updated_context.get('dashboard_stats', {})
        self.assertIn('bandwidth_saved_gb', stats)
        # 1 GB file -> 1.0 GB saved
        self.assertEqual(stats['bandwidth_saved_gb'], 1.0)

        # Verify Graph Data
        self.assertIn('bandwidth_chart', stats)
        import json
        chart = json.loads(stats['bandwidth_chart'])
        self.assertIn('labels', chart)
        self.assertIn('datasets', chart)
        datasets = chart['datasets']
        self.assertEqual(len(datasets), 1)
        data = datasets[0]['data']
        self.assertEqual(len(data), 7)
        # Check that the last element (today) is 1.0 GB
        self.assertEqual(data[-1], 1.0)

class ChatConsumerTests(TransactionTestCase):
    async def test_chat_consumer(self):
        # Create a router to verify path parsing
        application = URLRouter([
            path("ws/chat/<str:room_name>/", ChatConsumer.as_asgi()),
        ])

        communicator = WebsocketCommunicator(application, "/ws/chat/testroom/")
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)

        # Consume initial user count message
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'user_count')

        # Test sending message
        await communicator.send_json_to({
            "message": "hello",
            "username": "tester"
        })

        # Test receiving message
        response = await communicator.receive_json_from()
        self.assertEqual(response['message'], 'hello')
        self.assertEqual(response['username'], 'tester')

        await communicator.disconnect()
