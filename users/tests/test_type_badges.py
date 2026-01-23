from django.test import TestCase
from users.models import User, Badge, UserBadge, WatchLog
from content.models import Anime, Season, Episode

class TypeBadgeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')

        # Get Badges (created by migration)
        self.tv_badge, _ = Badge.objects.get_or_create(
            slug='tv-addict',
            defaults={
                'name': 'TV Addict',
                'description': 'Watched 10 different TV Series.'
            }
        )
        self.ova_badge, _ = Badge.objects.get_or_create(
            slug='ova-enthusiast',
            defaults={
                'name': 'OVA Enthusiast',
                'description': 'Watched 5 different OVAs.'
            }
        )

    def test_tv_addict_badge(self):
        # Watch 9 different TV Series
        for i in range(9):
            anime = Anime.objects.create(title=f"TV Anime {i}", type='TV')
            season = Season.objects.create(anime=anime, number=1)
            episode = Episode.objects.create(season=season, number=1)
            WatchLog.objects.create(user=self.user, episode=episode, duration=100)

        # Should not have badge yet
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.tv_badge).exists())

        # Watch 10th TV Series
        anime_10 = Anime.objects.create(title="TV Anime 10", type='TV')
        season = Season.objects.create(anime=anime_10, number=1)
        episode = Episode.objects.create(season=season, number=1)
        WatchLog.objects.create(user=self.user, episode=episode, duration=100)

        # Should have badge now
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=self.tv_badge).exists())

    def test_ova_enthusiast_badge(self):
        # Watch 4 different OVAs
        for i in range(4):
            anime = Anime.objects.create(title=f"OVA Anime {i}", type='OVA')
            season = Season.objects.create(anime=anime, number=1)
            episode = Episode.objects.create(season=season, number=1)
            WatchLog.objects.create(user=self.user, episode=episode, duration=100)

        # Should not have badge yet
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.ova_badge).exists())

        # Watch 5th OVA
        anime_5 = Anime.objects.create(title="OVA Anime 5", type='OVA')
        season = Season.objects.create(anime=anime_5, number=1)
        episode = Episode.objects.create(season=season, number=1)
        WatchLog.objects.create(user=self.user, episode=episode, duration=100)

        # Should have badge now
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=self.ova_badge).exists())

    def test_mixed_types_dont_interfere(self):
        # Watch 5 TV Series
        for i in range(5):
            anime = Anime.objects.create(title=f"TV Anime {i}", type='TV')
            season = Season.objects.create(anime=anime, number=1)
            episode = Episode.objects.create(season=season, number=1)
            WatchLog.objects.create(user=self.user, episode=episode, duration=100)

        # Watch 4 OVAs
        for i in range(4):
            anime = Anime.objects.create(title=f"OVA Anime {i}", type='OVA')
            season = Season.objects.create(anime=anime, number=1)
            episode = Episode.objects.create(season=season, number=1)
            WatchLog.objects.create(user=self.user, episode=episode, duration=100)

        # Verify neither badge is awarded
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.tv_badge).exists())
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.ova_badge).exists())

    def test_duplicate_watches_dont_count(self):
        # Watch same OVA 5 times
        anime = Anime.objects.create(title="OVA Anime Repeated", type='OVA')
        season = Season.objects.create(anime=anime, number=1)
        episode = Episode.objects.create(season=season, number=1)

        for _ in range(5):
            WatchLog.objects.create(user=self.user, episode=episode, duration=100)

        # Should not have badge (only 1 distinct OVA)
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.ova_badge).exists())
