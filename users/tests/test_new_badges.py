from django.test import TestCase
from users.models import User, Badge, UserBadge, WatchLog
from content.models import Anime, Season, Episode
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock

class NewBadgeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')

        # Ensure badges exist (they should be seeded by migrations, but in tests migrations might not run fully if not configured,
        # usually Django tests run migrations. But to be safe/explicit if needed, we can rely on migrations having run)
        # We can fetch them to be sure.
        self.marathon_badge = Badge.objects.get(slug='marathon-runner')
        self.millennium_badge = Badge.objects.get(slug='millennium-club')

    def test_marathon_runner_badge(self):
        # Create 1 Anime, 1 Season, 15 Episodes
        anime = Anime.objects.create(title="Marathon Anime", type='TV')
        season = Season.objects.create(anime=anime, number=1)
        episodes = [Episode.objects.create(season=season, number=i) for i in range(1, 16)]

        # Watch 11 episodes in last 24 hours
        for i in range(11):
            WatchLog.objects.create(user=self.user, episode=episodes[i], duration=100)

        # Should not have badge yet
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.marathon_badge).exists())

        # Watch 12th episode
        WatchLog.objects.create(user=self.user, episode=episodes[11], duration=100)

        # Should have badge now
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=self.marathon_badge).exists())

    @patch('users.badge_system.WatchLog.objects.filter')
    def test_millennium_club_badge(self, mock_filter):
        # We mock the chain: filter(...).values(...).distinct().count()
        # Since logic is:
        # distinct_episodes = WatchLog.objects.filter(user=user).values('episode').distinct().count()

        # Setup the mock chain
        mock_qs = MagicMock()
        mock_filter.return_value = mock_qs
        mock_qs.values.return_value = mock_qs
        mock_qs.distinct.return_value = mock_qs

        # Case 1: 999 episodes
        mock_qs.count.return_value = 999

        # Trigger check (we need to trigger it manually or via a signal on a dummy object)
        # Since we are mocking WatchLog.objects.filter, we can't easily rely on real WatchLog creation to trigger it naturally
        # because the signal handler calls check_badges which calls badge strategies which call WatchLog.objects.filter.
        # But if we patch it, the signal handler will use the mock.

        # However, creating a WatchLog needs real DB access for the creation itself.
        # If we patch WatchLog.objects.filter, it might interfere with other checks or internal Django stuff if not careful.
        # But badge logic imports WatchLog from .models.

        # Let's directly call the strategy check method or check_badges service to test logic.
        from users.badge_system import ConsumptionBadgeStrategy

        strategy = ConsumptionBadgeStrategy()
        awarded_slugs = set()
        all_badges = {b.slug: b for b in Badge.objects.all()}
        new_badges = []

        # Check with 999
        strategy.check(self.user, awarded_slugs, all_badges, new_badges)

        # Should NOT be in new_badges
        self.assertFalse(any(b.badge.slug == 'millennium-club' for b in new_badges))

        # Case 2: 1000 episodes
        mock_qs.count.return_value = 1000
        new_badges = [] # Reset

        strategy.check(self.user, awarded_slugs, all_badges, new_badges)

        # Should BE in new_badges
        self.assertTrue(any(b.badge.slug == 'millennium-club' for b in new_badges))
