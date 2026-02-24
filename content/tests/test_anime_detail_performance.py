from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.test.utils import CaptureQueriesContext
from django.db import connection
from content.models import Anime, Season, Episode, VideoFile, ExternalSource, Genre

class AnimeDetailPerformanceTest(APITestCase):
    def setUp(self):
        self.genre = Genre.objects.create(name="Action", slug="action")
        self.anime = Anime.objects.create(title="Performance Test Anime")
        self.anime.genres.add(self.genre)

        # Create 2 seasons
        for s in range(1, 3):
            season = Season.objects.create(anime=self.anime, number=s, title=f"Season {s}")
            # Create 5 episodes per season
            for e in range(1, 6):
                episode = Episode.objects.create(season=season, number=e, title=f"S{s}E{e}")
                # Create 3 video files per episode
                for q in ['480p', '720p', '1080p']:
                    VideoFile.objects.create(
                        episode=episode,
                        quality=q,
                        hls_path=f"path/to/{q}.m3u8",
                        encryption_key="key"
                    )
                # Create 2 external sources per episode
                for src in ['hianime', 'zoro']:
                    ExternalSource.objects.create(
                        episode=episode,
                        source_type=src,
                        embed_url=f"https://example.com/{src}"
                    )

        # The URL for anime detail viewset
        # Using the router in aniscrap_core/urls.py
        # router.register(r'anime', AnimeViewSet) -> 'anime-detail'
        # But verify the reverse name. Usually it's basename-detail.
        # If no basename provided, it defaults to queryset model name lowercased.
        # Here Anime -> anime -> anime-detail.
        self.url = f'/api/v1/anime/{self.anime.id}/'

    def test_anime_detail_query_count(self):
        # Warm up
        self.client.get(self.url)

        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Analyze queries
        video_file_queries = [q for q in ctx.captured_queries if 'content_videofile' in q['sql']]
        external_source_queries = [q for q in ctx.captured_queries if 'content_externalsource' in q['sql']]

        # We expect 1 query for VideoFiles and 1 query for ExternalSources due to prefetch
        self.assertEqual(len(video_file_queries), 1, "Should have exactly 1 query for VideoFiles")
        self.assertEqual(len(external_source_queries), 1, "Should have exactly 1 query for ExternalSources")

        # Total queries should be low (around 7-9)
        # 1 Anime + 1 Genres + 1 Seasons + 1 Episodes + 1 AnimeCharacters + 1 Characters + 1 VideoFiles + 1 ExternalSources + maybe 1 session/auth
        self.assertLessEqual(len(ctx.captured_queries), 12, f"Total queries too high: {len(ctx.captured_queries)}")

        # Verify response structure
        data = response.data
        self.assertIn('seasons', data)
        self.assertEqual(len(data['seasons']), 2)

        season_data = data['seasons'][0]
        self.assertIn('name', season_data) # Check if 'name' is present (mapped from 'title')
        self.assertIn('episodes', season_data)

        episode_data = season_data['episodes'][0]
        self.assertIn('video_files', episode_data)
        self.assertIn('external_sources', episode_data)

        video_files = episode_data['video_files']
        self.assertEqual(len(video_files), 3)
        self.assertIn('file_url', video_files[0]) # Check if 'file_url' is present (mapped from 'hls_path')

        external_sources = episode_data['external_sources']
        self.assertEqual(len(external_sources), 2)
        self.assertIn('source_name', external_sources[0]) # Check if 'source_name' is present (mapped from 'source_type')
