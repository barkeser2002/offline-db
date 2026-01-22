from django.test import TestCase
from django.utils import timezone
from users.models import User, Badge, UserBadge, WatchLog
from content.models import Anime, Season, Episode
from users.services import check_badges
from unittest.mock import patch

class MovieBuffBadgeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='moviebuff', password='password')
        self.badge = Badge.objects.get(slug='movie-buff')

    def create_watch_log(self, anime_type, anime_title):
        anime = Anime.objects.create(title=anime_title, type=anime_type)
        season = Season.objects.create(anime=anime, number=1)
        episode = Episode.objects.create(season=season, number=1)
        WatchLog.objects.create(user=self.user, episode=episode, duration=100)

    @patch('users.services._send_badge_notifications')
    def test_award_movie_buff_badge(self, mock_notify):
        # Watch 5 movies
        for i in range(5):
            self.create_watch_log('Movie', f'Movie {i}')

        check_badges(self.user)

        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())
        # Verify notification was sent (mocked)
        self.assertTrue(mock_notify.called)

    def test_no_badge_for_less_than_5_movies(self):
        # Watch 4 movies
        for i in range(4):
            self.create_watch_log('Movie', f'Movie {i}')

        check_badges(self.user)

        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())

    def test_no_badge_for_tv_shows(self):
        # Watch 5 TV shows
        for i in range(5):
            self.create_watch_log('TV', f'TV Show {i}')

        check_badges(self.user)

        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())

    def test_distinct_movies_required(self):
        # Watch same movie 5 times
        anime = Anime.objects.create(title="Single Movie", type='Movie')
        season = Season.objects.create(anime=anime, number=1)
        episode = Episode.objects.create(season=season, number=1)

        for i in range(5):
            WatchLog.objects.create(user=self.user, episode=episode, duration=100)

        check_badges(self.user)

        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())
