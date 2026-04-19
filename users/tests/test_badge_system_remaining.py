from django.test import TestCase
from users.models import User, Badge, UserBadge, WatchLog
from content.models import Anime, Genre, Season, Episode, VideoFile
from users.badge_system import GenreBadgeStrategy, CommunityBadgeStrategy
from unittest.mock import MagicMock

class BadgeSystemRemainingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.genre_badge, _ = Badge.objects.get_or_create(slug='genre-explorer', defaults={'name': 'Genre Explorer'})
        self.content_badge, _ = Badge.objects.get_or_create(slug='content-creator', defaults={'name': 'Content Creator'})

        self.anime = Anime.objects.create(title='Test Anime')
        self.season = Season.objects.create(anime=self.anime, number=1)
        self.episode = Episode.objects.create(season=self.season, number=1, title='Test Episode')

    def test_genre_explorer_no_ids(self):
        strategy = GenreBadgeStrategy()
        awarded_slugs = set()
        all_badges = {'genre-explorer': self.genre_badge}
        new_badges = []

        # Test when get_anime_ids() returns empty, the coverage block for "else: genre_ids = []" is hit
        strategy.check(self.user, awarded_slugs, all_badges, new_badges, cache={'anime_ids': []})
        self.assertEqual(len(new_badges), 0)

    def test_content_creator_no_slug(self):
        # Create 5 videos
        for i in range(5):
            VideoFile.objects.create(uploader=self.user, episode=self.episode)

        strategy = CommunityBadgeStrategy()
        awarded_slugs = set()
        all_badges = {'content-creator': self.content_badge}
        new_badges = []

        # Should award content creator
        strategy.check(self.user, awarded_slugs, all_badges, new_badges, cache={'hosted_rooms': []})
        self.assertEqual(len(new_badges), 1)
        self.assertEqual(new_badges[0].badge.slug, 'content-creator')
