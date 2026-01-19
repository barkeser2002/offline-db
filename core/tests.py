from django.test import TestCase, RequestFactory
from content.models import Anime, Season, Episode, VideoFile
from core.dashboard import dashboard_callback

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
        chart = stats['bandwidth_chart']
        self.assertIn('labels', chart)
        self.assertIn('data', chart)
        self.assertEqual(len(chart['data']), 7)
        # Check that the last element (today) is 1.0 GB
        self.assertEqual(chart['data'][-1], 1.0)
