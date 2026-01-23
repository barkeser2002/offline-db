from django.test import TestCase, Client
from django.urls import reverse
from content.models import Anime, Season, Episode, VideoFile, FansubGroup
from django.db import connection, reset_queries
import time

class PlayerViewPerformanceTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.anime = Anime.objects.create(title="Test Anime", synopsis="Test Synopsis")
        self.season = Season.objects.create(anime=self.anime, number=1)
        self.episode = Episode.objects.create(season=self.season, number=1, title="Test Episode")
        self.fansub = FansubGroup.objects.create(name="Test Subs")
        self.video = VideoFile.objects.create(
            episode=self.episode,
            quality='1080p',
            hls_path='/path/to/playlist.m3u8',
            encryption_key='key',
            fansub_group=self.fansub
        )
        self.url = reverse('watch', args=[self.episode.id])

    def test_player_view_query_count(self):
        # Warm up
        self.client.get(self.url)

        reset_queries()
        with self.assertNumQueries(3):
            # 1. Get Episode + Season + Anime (select_related)
            # 2. Get Video + FansubGroup (select_related)
            # 3. Get AdSlot (template tag)
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)

        # Print queries for debugging
        # for query in connection.queries:
        #     print(query['sql'])
