import pytest
from users.models import User, Badge, UserBadge, WatchLog
from content.models import Anime, Season, Episode
from users.services import check_badges
from unittest.mock import patch, MagicMock

@pytest.mark.django_db
class TestCenturyClubBadge:
    @pytest.fixture
    def user(self):
        return User.objects.create_user(username='testuser', password='password')

    @pytest.fixture
    def century_club_badge(self):
        return Badge.objects.get_or_create(slug='century-club', defaults={'name': 'Century Club', 'description': 'Watched 100 episodes.', 'icon_url': '/static/badges/century_club.png'})[0]

    def test_awards_century_club_badge(self, user, century_club_badge):
        anime = Anime.objects.create(title="Long Anime")
        season = Season.objects.create(anime=anime, number=1)

        # Bulk create episodes
        episodes = [Episode(season=season, number=i) for i in range(1, 101)]
        Episode.objects.bulk_create(episodes)

        # Reload episodes to get IDs
        episodes = list(Episode.objects.all())

        # Bulk create watch logs
        logs = [WatchLog(user=user, episode=ep, duration=100) for ep in episodes]
        WatchLog.objects.bulk_create(logs)

        with patch('users.services.get_channel_layer') as mock_channel_layer, \
             patch('users.services.async_to_sync') as mock_async_to_sync:
            mock_async_to_sync.return_value = MagicMock()

            check_badges(user)

        assert UserBadge.objects.filter(user=user, badge=century_club_badge).exists()

    def test_does_not_award_century_club_badge_if_less_than_100(self, user, century_club_badge):
        anime = Anime.objects.create(title="Medium Anime")
        season = Season.objects.create(anime=anime, number=1)

        # Bulk create 99 episodes
        episodes = [Episode(season=season, number=i) for i in range(1, 100)]
        Episode.objects.bulk_create(episodes)

        episodes = list(Episode.objects.all())

        logs = [WatchLog(user=user, episode=ep, duration=100) for ep in episodes]
        WatchLog.objects.bulk_create(logs)

        with patch('users.services.get_channel_layer') as mock_channel_layer, \
             patch('users.services.async_to_sync') as mock_async_to_sync:

            check_badges(user)

        assert not UserBadge.objects.filter(user=user, badge=century_club_badge).exists()
