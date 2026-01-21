from django.test import TestCase
from django.utils import timezone
from users.models import User, Badge, UserBadge, WatchLog
from content.models import Anime, Season, Episode, Genre
from users.services import check_badges

class GenreMasterBadgeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.badge, _ = Badge.objects.get_or_create(slug='genre-master', defaults={'name': 'Genre Master', 'description': 'Test'})
        self.genre = Genre.objects.create(name='Action', slug='action')
        self.genre_other = Genre.objects.create(name='Romance', slug='romance')

    def test_award_badge(self):
        # Watch 10 different animes of the same genre
        for i in range(10):
            anime = Anime.objects.create(title=f'Anime {i}')
            anime.genres.add(self.genre)
            season = Season.objects.create(anime=anime, number=1)
            episode = Episode.objects.create(season=season, number=1)
            WatchLog.objects.create(user=self.user, episode=episode, duration=100)

        check_badges(self.user)

        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())

    def test_no_badge_if_less_than_10(self):
        # Watch 9 different animes of the same genre
        for i in range(9):
            anime = Anime.objects.create(title=f'Anime {i}')
            anime.genres.add(self.genre)
            season = Season.objects.create(anime=anime, number=1)
            episode = Episode.objects.create(season=season, number=1)
            WatchLog.objects.create(user=self.user, episode=episode, duration=100)

        check_badges(self.user)

        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())

    def test_no_badge_if_mixed_genres_not_enough(self):
        # Watch 5 Action and 5 Romance (total 10 animes, but not same genre)
        for i in range(5):
            anime = Anime.objects.create(title=f'Action {i}')
            anime.genres.add(self.genre)
            season = Season.objects.create(anime=anime, number=1)
            episode = Episode.objects.create(season=season, number=1)
            WatchLog.objects.create(user=self.user, episode=episode, duration=100)

        for i in range(5):
            anime = Anime.objects.create(title=f'Romance {i}')
            anime.genres.add(self.genre_other)
            season = Season.objects.create(anime=anime, number=1)
            episode = Episode.objects.create(season=season, number=1)
            WatchLog.objects.create(user=self.user, episode=episode, duration=100)

        check_badges(self.user)

        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())

    def test_badge_awarded_with_multiple_episodes_same_anime(self):
        # Watch 10 episodes of ONE anime (should NOT award badge)
        anime = Anime.objects.create(title='Anime One')
        anime.genres.add(self.genre)
        season = Season.objects.create(anime=anime, number=1)

        for i in range(10):
            episode = Episode.objects.create(season=season, number=i+1)
            WatchLog.objects.create(user=self.user, episode=episode, duration=100)

        check_badges(self.user)

        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())
