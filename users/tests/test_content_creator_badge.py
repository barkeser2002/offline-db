from django.test import TestCase
from users.models import User, Badge, UserBadge
from content.models import Anime, Season, Episode, VideoFile
from users.services import check_badges

class ContentCreatorBadgeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='uploader', password='password')

        # Badge should be seeded by migration, but in tests we ensure it exists
        self.badge, _ = Badge.objects.get_or_create(
            slug='content-creator',
            defaults={'name': 'Content Creator', 'description': 'Uploaded 5 videos.'}
        )

        self.anime = Anime.objects.create(title='Test Anime')
        self.season = Season.objects.create(anime=self.anime, number=1)
        self.episode = Episode.objects.create(season=self.season, number=1, title="Ep 1")

    def test_content_creator_badge(self):
        # Upload 4 videos
        for i in range(4):
            VideoFile.objects.create(
                episode=self.episode,
                uploader=self.user,
                quality='1080p',
                hls_path=f'path/to/video_{i}.m3u8',
                encryption_key=f'key_{i}'
            )

        # Verify no badge yet
        # check_badges is called via signal, so we can verify directly
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())

        # Upload 5th video
        VideoFile.objects.create(
            episode=self.episode,
            uploader=self.user,
            quality='1080p',
            hls_path='path/to/video_5.m3u8',
            encryption_key='key_5'
        )

        # Verify badge awarded
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())
