from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.db import connection, reset_queries
from decimal import Decimal
from users.models import User, WatchLog, Wallet
from content.models import Anime, Season, Episode, VideoFile, FansubGroup
from billing.models import ShopierPayment
from billing.tasks import calculate_revenue

class PerformanceTest(TestCase):
    def setUp(self):
        # Create Users
        self.user = User.objects.create_user(username='testuser', password='password')
        self.uploader = User.objects.create_user(username='uploader', password='password')
        self.fansub_owner = User.objects.create_user(username='fansub_owner', password='password')

        # Create Fansub Group
        self.fansub_group = FansubGroup.objects.create(name='Test Fansub', owner=self.fansub_owner)

        # Create Anime, Season, Episode
        self.anime = Anime.objects.create(title='Test Anime')
        self.season = Season.objects.create(anime=self.anime, number=1)
        self.episodes = []
        for i in range(10): # Create 10 episodes
            episode = Episode.objects.create(season=self.season, number=i+1)
            self.episodes.append(episode)

            # Create VideoFile for each episode
            VideoFile.objects.create(
                episode=episode,
                fansub_group=self.fansub_group,
                uploader=self.uploader,
                quality='1080p',
                hls_path='/path/to/hls',
                encryption_key='key',
                file_size_bytes=1000
            )

        # Create Payment
        ShopierPayment.objects.create(
            user=self.user,
            amount=Decimal('100.00'),
            transaction_id='ORD-12345',
            status='success',
            is_distributed=False
        )

    def test_calculate_revenue_performance(self):
        # Create WatchLogs for each episode
        for episode in self.episodes:
            WatchLog.objects.create(user=self.user, episode=episode, duration=100)

        # Run calculate_revenue and count queries
        reset_queries()
        with CaptureQueriesContext(connection) as context:
            calculate_revenue()

        query_count = len(context.captured_queries)

        # After optimization, we expect significantly fewer queries.
        # 1 (payments) + 1 (aggregate) + 1 (logs + episodes) + 3 (video files + related)
        # + wallet updates (depends on unique users/groups)
        # With 10 logs but same group/uploader, the number of queries should be roughly constant (around 18).
        # Without optimization, it was 55+.

        self.assertTrue(query_count < 25, f"Expected < 25 queries, got {query_count}")
