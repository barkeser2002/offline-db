from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timedelta, timezone as dt_timezone
from unittest.mock import patch
from users.models import User, Badge, UserBadge, WatchLog
from content.models import Anime, Season, Episode
from core.models import ChatMessage
from users.services import check_badges

class BadgeSystemTests(TestCase):
    def setUp(self):
        # Create user
        self.user = User.objects.create_user(username='testuser', password='password')

        # Get or create badges (since migration might have created them)
        self.binge_badge, _ = Badge.objects.get_or_create(
            slug='binge-watcher',
            defaults={'name': 'Binge Watcher', 'description': 'Watched 5 episodes in 24 hours'}
        )
        self.supporter_badge, _ = Badge.objects.get_or_create(
            slug='supporter',
            defaults={'name': 'Supporter', 'description': 'Is a Premium Member'}
        )
        self.veteran_badge, _ = Badge.objects.get_or_create(
            slug='veteran',
            defaults={'name': 'Veteran', 'description': 'Member for over 1 year'}
        )

        # Create content
        self.anime = Anime.objects.create(title="Test Anime")
        self.season = Season.objects.create(anime=self.anime, number=1)
        # Create 10 episodes
        self.episodes = []
        for i in range(1, 11):
            ep = Episode.objects.create(season=self.season, number=i)
            self.episodes.append(ep)

    def test_binge_watcher_badge(self):
        # Watch 4 episodes
        for i in range(4):
            WatchLog.objects.create(
                user=self.user,
                episode=self.episodes[i],
                duration=1200
            )

        # Should not have badge yet
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.binge_badge).exists())

        # Watch 5th episode
        WatchLog.objects.create(
            user=self.user,
            episode=self.episodes[4],
            duration=1200
        )

        # Signal should trigger check_badges -> award badge
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=self.binge_badge).exists())

    def test_supporter_badge(self):
        self.user.is_premium = True
        self.user.save()

        # check_badges needs to be called manually or via some trigger (e.g. payment success)
        # For now, let's call it manually as we hooked it to WatchLog, not User.save
        check_badges(self.user)

        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=self.supporter_badge).exists())

    def test_veteran_badge(self):
        # Make user old
        self.user.date_joined = timezone.now() - timedelta(days=400)
        self.user.save()

        check_badges(self.user)
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=self.veteran_badge).exists())

    @patch('django.utils.timezone.now')
    def test_night_owl_badge(self, mock_now):
        # Set time to 3 AM UTC
        fixed_now = datetime(2023, 1, 1, 3, 0, 0, tzinfo=dt_timezone.utc)
        mock_now.return_value = fixed_now

        night_owl_badge, _ = Badge.objects.get_or_create(
            slug='night-owl',
            defaults={'name': 'Night Owl', 'description': 'Watched between 2 AM and 5 AM'}
        )

        # Create log (auto_now_add uses mock_now)
        WatchLog.objects.create(
            user=self.user,
            episode=self.episodes[0],
            duration=1200
        )
        # Signal runs check_badges automatically on create

        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=night_owl_badge).exists())

    @patch('django.utils.timezone.now')
    def test_night_owl_badge_negative(self, mock_now):
        # Set time to 10 AM UTC
        fixed_now = datetime(2023, 1, 1, 10, 0, 0, tzinfo=dt_timezone.utc)
        mock_now.return_value = fixed_now

        night_owl_badge, _ = Badge.objects.get_or_create(
            slug='night-owl',
            defaults={'name': 'Night Owl', 'description': 'Watched between 2 AM and 5 AM'}
        )

        WatchLog.objects.create(
            user=self.user,
            episode=self.episodes[0],
            duration=1200
        )

        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=night_owl_badge).exists())

    def test_commentator_badge(self):
        commentator_badge, _ = Badge.objects.get_or_create(
            slug='commentator',
            defaults={'name': 'Commentator', 'description': 'Posted 50 chat messages'}
        )

        # Create 49 messages
        for i in range(49):
            ChatMessage.objects.create(
                user=self.user,
                username=self.user.username,
                room_name='test_room',
                message=f'Message {i}'
            )

        # Check badge not awarded
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=commentator_badge).exists())

        # Create 50th message
        ChatMessage.objects.create(
            user=self.user,
            username=self.user.username,
            room_name='test_room',
            message='Message 50'
        )

        # Check badge awarded (signal should have triggered)
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=commentator_badge).exists())

    def test_early_bird_badge(self):
        early_bird_badge, _ = Badge.objects.get_or_create(
            slug='early-bird',
            defaults={'name': 'Early Bird', 'description': 'Watched within 1 hour'}
        )

        # Case 1: Watched late (2 hours after release)
        episode_late = Episode.objects.create(
            season=self.season,
            number=100
        )
        # Manually set created_at
        episode_late.created_at = timezone.now() - timedelta(hours=3)
        episode_late.save()

        WatchLog.objects.create(
            user=self.user,
            episode=episode_late,
            duration=100
        )

        # Trigger check manually because our signal setup might be tricky with mock times in other tests
        # But signals are synchronous, so it should have run.
        # check_badges(self.user) # Redundant if signal works

        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=early_bird_badge).exists())

        # Case 2: Watched early (30 mins after release)
        episode_early = Episode.objects.create(
            season=self.season,
            number=101
        )
        # Ensure created_at is strictly set (though auto_now_add handles it)
        # We'll trust auto_now_add sets it to Now.

        # We need to simulate that the Episode was created "just now" and we watched it "just now".
        # Since logic compares (watched_at - created_at) <= 1h.

        WatchLog.objects.create(
            user=self.user,
            episode=episode_early,
            duration=100
        )

        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=early_bird_badge).exists())
