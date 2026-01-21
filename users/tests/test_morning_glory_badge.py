from django.test import TestCase
from django.utils import timezone
from users.models import User, Badge, UserBadge, WatchLog
from content.models import Anime, Season, Episode
from users.services import check_badges

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

    def test_award_badge_at_6_am(self):
        # Watch at 6:30 AM UTC
        now = timezone.now()
        target_time = now.replace(hour=6, minute=30, second=0, microsecond=0)

        w = WatchLog.objects.create(user=self.user, episode=self.episode, duration=100)
        w.watched_at = target_time
        w.save()

        check_badges(self.user)
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())

    def test_award_badge_at_8_59_am(self):
        # Watch at 8:59 AM UTC
        now = timezone.now()
        target_time = now.replace(hour=8, minute=59, second=59, microsecond=0)

        w = WatchLog.objects.create(user=self.user, episode=self.episode, duration=100)
        w.watched_at = target_time
        w.save()

        check_badges(self.user)
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())

    def test_no_badge_at_5_59_am(self):
        # Watch at 5:59 AM UTC
        now = timezone.now()
        target_time = now.replace(hour=5, minute=59, second=59, microsecond=0)

        w = WatchLog.objects.create(user=self.user, episode=self.episode, duration=100)
        w.watched_at = target_time
        w.save()

        check_badges(self.user)
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())

    def test_no_badge_at_9_00_am(self):
        # Watch at 9:00 AM UTC
        now = timezone.now()
        target_time = now.replace(hour=9, minute=0, second=0, microsecond=0)

        w = WatchLog.objects.create(user=self.user, episode=self.episode, duration=100)
        w.watched_at = target_time
        w.save()

        check_badges(self.user)
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())
