from django.test import TestCase
from django.utils import timezone
from users.models import User, Badge, UserBadge, WatchLog
from content.models import Anime, Season, Episode
from users.services import check_badges

class LoyalFanBadgeTest(TestCase):
    def setUp(self):
        # Create User
        self.user = User.objects.create_user(username='fanuser', password='password')

        # Get or Create Badge
        self.badge, _ = Badge.objects.get_or_create(
            slug='loyal-fan',
            defaults={
                'name': 'Loyal Fan',
                'description': 'Watched 10 episodes of the same anime.'
            }
        )

        # Create Content
        self.anime = Anime.objects.create(title="One Piece")
        self.season = Season.objects.create(anime=self.anime, number=1)

        # Create 10 episodes
        self.episodes = []
        for i in range(1, 11):
            ep = Episode.objects.create(season=self.season, number=i, title=f"Ep {i}")
            self.episodes.append(ep)

    def test_loyal_fan_badge_awarded(self):
        # Watch 9 episodes
        for i in range(9):
            WatchLog.objects.create(user=self.user, episode=self.episodes[i], watched_at=timezone.now(), duration=100)

        # Check: Badge NOT awarded yet
        check_badges(self.user)
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())

        # Watch 10th episode
        WatchLog.objects.create(user=self.user, episode=self.episodes[9], watched_at=timezone.now(), duration=100)

        # Check: Badge AWARDED
        check_badges(self.user)
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())

    def test_loyal_fan_badge_not_awarded_for_different_animes(self):
        # Create another anime
        anime2 = Anime.objects.create(title="Naruto")
        season2 = Season.objects.create(anime=anime2, number=1)
        ep_anime2 = Episode.objects.create(season=season2, number=1, title="Ep 1")

        # Watch 9 episodes of One Piece
        for i in range(9):
            WatchLog.objects.create(user=self.user, episode=self.episodes[i], watched_at=timezone.now(), duration=100)

        # Watch 1 episode of Naruto
        WatchLog.objects.create(user=self.user, episode=ep_anime2, watched_at=timezone.now(), duration=100)

        # Total 10 episodes watched, but not of the SAME anime
        check_badges(self.user)
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())
