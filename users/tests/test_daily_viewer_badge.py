from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from users.models import User, Badge, UserBadge, WatchLog
from content.models import Episode, Anime, Season
from users.services import check_badges

class DailyViewerBadgeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='daily_viewer_user', password='password')
        self.anime = Anime.objects.create(title="Test Anime")
        self.season = Season.objects.create(anime=self.anime, number=1)
        self.episode = Episode.objects.create(season=self.season, number=1, title="Ep 1")

        # Ensure badge exists (in case migration didn't run in test DB setup, though it should)
        Badge.objects.get_or_create(slug='daily-viewer', defaults={'name': 'Daily Viewer'})

    def test_daily_viewer_badge_awarded(self):
        """Test that the Daily Viewer badge is awarded for 30 consecutive days of watching."""
        today = timezone.now()

        # Create watch logs for the last 30 days (including today)
        for i in range(30):
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
            UserBadge.objects.filter(user=self.user, badge__slug='daily-viewer').exists(),
            "Daily Viewer badge should be awarded"
        )

    def test_daily_viewer_badge_not_awarded_for_29_days(self):
        """Test that the badge is NOT awarded for less than 30 days."""
        today = timezone.now()

        for i in range(29):
            date = today - timedelta(days=i)
            log = WatchLog.objects.create(
                user=self.user,
                episode=self.episode,
                duration=100
            )
            WatchLog.objects.filter(pk=log.pk).update(watched_at=date)

        check_badges(self.user)

        self.assertFalse(
            UserBadge.objects.filter(user=self.user, badge__slug='daily-viewer').exists(),
            "Daily Viewer badge should NOT be awarded for only 29 days"
        )

    def test_daily_viewer_badge_not_awarded_with_gaps(self):
        """Test that the badge is NOT awarded if there are gaps."""
        today = timezone.now()

        # Watch on day 0, day 2, ..., day 58 (30 days total but spread out)
        for i in range(30):
            date = today - timedelta(days=i*2) # Gap of 1 day
            log = WatchLog.objects.create(
                user=self.user,
                episode=self.episode,
                duration=100
            )
            WatchLog.objects.filter(pk=log.pk).update(watched_at=date)

        check_badges(self.user)

        self.assertFalse(
            UserBadge.objects.filter(user=self.user, badge__slug='daily-viewer').exists(),
            "Daily Viewer badge should NOT be awarded with gaps in 30-day window"
        )
