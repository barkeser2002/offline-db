from django.test import TestCase
from django.contrib.auth import get_user_model
from users.models import Badge, UserBadge, WatchLog
from content.models import Anime, Season, Episode
from users.services import check_badges

User = get_user_model()

class PilotConnoisseurBadgeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        # Ensure the badge exists (it might be created by migration in real db, but tests use empty db)
        self.badge, _ = Badge.objects.get_or_create(
            slug='pilot-connoisseur',
            defaults={
                'name': 'Pilot Connoisseur',
                'description': 'Watched the first episode of 5 different anime series.'
            }
        )

    def test_pilot_connoisseur_badge_awarded(self):
        # Create 5 animes, each with a season and episode 1
        for i in range(1, 6):
            anime = Anime.objects.create(title=f'Anime {i}')
            season = Season.objects.create(anime=anime, number=1)
            episode = Episode.objects.create(season=season, number=1, title=f'Pilot {i}')

            # Watch the episode
            WatchLog.objects.create(user=self.user, episode=episode, duration=100)

        # Check badges
        check_badges(self.user)

        # Verify badge is awarded
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())

    def test_pilot_connoisseur_badge_not_awarded_for_non_pilots(self):
        # Create 1 anime with 5 episodes
        anime = Anime.objects.create(title='Anime 1')
        season = Season.objects.create(anime=anime, number=1)

        for i in range(1, 6):
            episode = Episode.objects.create(season=season, number=i, title=f'Ep {i}')
            WatchLog.objects.create(user=self.user, episode=episode, duration=100)

        # Check badges
        check_badges(self.user)

        # Verify badge is NOT awarded
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())

    def test_pilot_connoisseur_badge_not_awarded_for_insufficient_pilots(self):
        # Create 4 animes
        for i in range(1, 5):
            anime = Anime.objects.create(title=f'Anime {i}')
            season = Season.objects.create(anime=anime, number=1)
            episode = Episode.objects.create(season=season, number=1, title=f'Pilot {i}')

            WatchLog.objects.create(user=self.user, episode=episode, duration=100)

        check_badges(self.user)
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())
