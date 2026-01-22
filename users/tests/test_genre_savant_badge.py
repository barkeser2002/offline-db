from django.test import TestCase
from users.models import User, Badge, UserBadge, WatchLog
from content.models import Anime, Genre, Season, Episode
from users.services import check_badges
from django.utils import timezone

class GenreSavantBadgeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')

        # Ensure badge exists (seeded via migration, but we can double check/create)
        self.badge, _ = Badge.objects.get_or_create(slug='genre-savant', defaults={'name': 'Genre Savant'})

        self.genre = Genre.objects.create(name='Action', slug='action')
        self.anime = Anime.objects.create(title='Test Anime')
        self.anime.genres.add(self.genre)
        self.season = Season.objects.create(anime=self.anime, number=1)

        self.episodes = []
        for i in range(50):
            self.episodes.append(Episode.objects.create(season=self.season, number=i+1, title=f'Ep {i+1}'))

    def test_genre_savant_badge_awarded(self):
        # Watch 49 episodes
        for i in range(49):
            WatchLog.objects.create(user=self.user, episode=self.episodes[i], duration=100)

        check_badges(self.user)
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())

        # Watch 50th episode
        WatchLog.objects.create(user=self.user, episode=self.episodes[49], duration=100)

        check_badges(self.user)
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())
