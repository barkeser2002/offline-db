from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from users.models import User, Badge, UserBadge, WatchLog
from content.models import Anime, Season, Episode
from users.services import check_badges

class SpeedsterBadgeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.badge, _ = Badge.objects.get_or_create(slug='speedster', defaults={'name': 'Speedster', 'description': 'Test'})

        # Setup content
        self.anime = Anime.objects.create(title='Test Anime')
        self.season = Season.objects.create(anime=self.anime, number=1)
        self.episodes = []
        for i in range(5):
            self.episodes.append(Episode.objects.create(season=self.season, number=i+1, title=f"Ep {i+1}"))

    def test_award_badge(self):
        # Watch 3 episodes within last hour
        now = timezone.now()

        w1 = WatchLog.objects.create(user=self.user, episode=self.episodes[0], duration=100)
        w1.watched_at = now - timedelta(minutes=50)
        w1.save()

        w2 = WatchLog.objects.create(user=self.user, episode=self.episodes[1], duration=100)
        w2.watched_at = now - timedelta(minutes=30)
        w2.save()

        w3 = WatchLog.objects.create(user=self.user, episode=self.episodes[2], duration=100)
        w3.watched_at = now - timedelta(minutes=10)
        w3.save()

        check_badges(self.user)
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())

    def test_no_badge_if_less_than_3(self):
        now = timezone.now()
        w1 = WatchLog.objects.create(user=self.user, episode=self.episodes[0], duration=100)
        w1.watched_at = now - timedelta(minutes=30)
        w1.save()

        w2 = WatchLog.objects.create(user=self.user, episode=self.episodes[1], duration=100)
        w2.watched_at = now - timedelta(minutes=10)
        w2.save()

        check_badges(self.user)
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())

    def test_no_badge_if_time_span_too_long(self):
        # 3 episodes, but over > 1 hour
        now = timezone.now()

        w1 = WatchLog.objects.create(user=self.user, episode=self.episodes[0], duration=100)
        w1.watched_at = now - timedelta(minutes=120) # 2 hours ago
        w1.save()

        w2 = WatchLog.objects.create(user=self.user, episode=self.episodes[1], duration=100)
        w2.watched_at = now - timedelta(minutes=30)
        w2.save()

        w3 = WatchLog.objects.create(user=self.user, episode=self.episodes[2], duration=100)
        w3.watched_at = now - timedelta(minutes=10)
        w3.save()

        # Only 2 in last hour
        check_badges(self.user)
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())

    def test_distinct_episodes_required(self):
        # Watch same episode 3 times in 1 hour
        now = timezone.now()

        for i in range(3):
            w = WatchLog.objects.create(user=self.user, episode=self.episodes[0], duration=100)
            w.watched_at = now - timedelta(minutes=10*i)
            w.save()

        check_badges(self.user)
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())
