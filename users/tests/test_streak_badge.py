from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from users.models import User, Badge, UserBadge, WatchLog
from content.models import Episode, Anime, Season
from users.services import check_badges

class StreakBadgeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='streak_user', password='password')
        self.anime = Anime.objects.create(title="Test Anime")
        self.season = Season.objects.create(anime=self.anime, number=1)
        self.episode = Episode.objects.create(season=self.season, number=1, title="Ep 1")

        # Ensure badge exists
        Badge.objects.get_or_create(slug='streak-master', defaults={'name': 'Streak Master'})

    def test_streak_master_badge_awarded(self):
        """Test that the Streak Master badge is awarded for 7 consecutive days of watching."""
        today = timezone.now()

        # Create watch logs for the last 7 days (including today)
        for i in range(7):
            date = today - timedelta(days=i)
            log = WatchLog.objects.create(
                user=self.user,
                episode=self.episode,
                duration=100
            )
            # Update created time
            WatchLog.objects.filter(pk=log.pk).update(watched_at=date)

        # Trigger check
        check_badges(self.user)

        # Verify
        self.assertTrue(
            UserBadge.objects.filter(user=self.user, badge__slug='streak-master').exists(),
            "Streak Master badge should be awarded"
        )

    def test_streak_master_badge_not_awarded_for_6_days(self):
        """Test that the badge is NOT awarded for less than 7 days."""
        today = timezone.now()

        for i in range(6):
            date = today - timedelta(days=i)
            log = WatchLog.objects.create(
                user=self.user,
                episode=self.episode,
                duration=100
            )
            WatchLog.objects.filter(pk=log.pk).update(watched_at=date)

        check_badges(self.user)

        self.assertFalse(
            UserBadge.objects.filter(user=self.user, badge__slug='streak-master').exists(),
            "Streak Master badge should NOT be awarded for only 6 days"
        )
