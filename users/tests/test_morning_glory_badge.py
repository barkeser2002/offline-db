from django.test import TestCase
from users.models import User, Badge, UserBadge, WatchLog
from content.models import Anime, Season, Episode
from users.services import check_badges
from unittest import mock
from datetime import datetime, timezone as dt_timezone

class MorningGloryBadgeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        # We use 'morning-glory' slug as seeded in migration
        self.badge, _ = Badge.objects.get_or_create(
            slug='morning-glory',
            defaults={'name': 'Morning Glory', 'description': 'Test'}
        )

        self.anime = Anime.objects.create(title='Test Anime')
        self.season = Season.objects.create(anime=self.anime, number=1)
        self.episode = Episode.objects.create(season=self.season, number=1, title="Ep 1")

    @mock.patch('django.utils.timezone.now')
    def test_award_badge_at_6_am(self, mock_now):
        # Watch at 6:30 AM UTC
        target_time = datetime(2024, 1, 1, 6, 30, 0, tzinfo=dt_timezone.utc)
        mock_now.return_value = target_time

        # Create log (auto_now_add uses mocked time)
        WatchLog.objects.create(user=self.user, episode=self.episode, duration=100)

        # Signal triggers check_badges automatically, but we can call it explicitly too to be safe/clear
        check_badges(self.user)
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())

    @mock.patch('django.utils.timezone.now')
    def test_award_badge_at_8_59_am(self, mock_now):
        # Watch at 8:59 AM UTC
        target_time = datetime(2024, 1, 1, 8, 59, 59, tzinfo=dt_timezone.utc)
        mock_now.return_value = target_time

        WatchLog.objects.create(user=self.user, episode=self.episode, duration=100)

        check_badges(self.user)
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())

    @mock.patch('django.utils.timezone.now')
    def test_no_badge_at_5_59_am(self, mock_now):
        # Watch at 5:59 AM UTC
        target_time = datetime(2024, 1, 1, 5, 59, 59, tzinfo=dt_timezone.utc)
        mock_now.return_value = target_time

        WatchLog.objects.create(user=self.user, episode=self.episode, duration=100)

        check_badges(self.user)
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())

    @mock.patch('django.utils.timezone.now')
    def test_no_badge_at_9_00_am(self, mock_now):
        # Watch at 9:00 AM UTC
        target_time = datetime(2024, 1, 1, 9, 0, 0, tzinfo=dt_timezone.utc)
        mock_now.return_value = target_time

        WatchLog.objects.create(user=self.user, episode=self.episode, duration=100)

        check_badges(self.user)
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())
