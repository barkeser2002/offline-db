import pytest
from users.models import User, Badge, UserBadge, WatchLog
from content.models import Anime, Season, Episode
from users.services import check_badges
from django.utils import timezone
from unittest.mock import patch, MagicMock

@pytest.mark.django_db
class TestOtakuBadge:
    @pytest.fixture
    def user(self):
        return User.objects.create_user(username='testuser', password='password')

    @pytest.fixture
    def otaku_badge(self):
        return Badge.objects.get_or_create(slug='otaku', defaults={'name': 'Otaku', 'description': 'Completed 5 different anime series.'})[0]

    def test_awards_otaku_badge(self, user, otaku_badge):
        # Create 5 anime, each with 1 episode for simplicity (or more)
        for i in range(5):
            anime = Anime.objects.create(title=f"Anime {i}")
            season = Season.objects.create(anime=anime, number=1)
            ep = Episode.objects.create(season=season, number=1)

            # Watch the episode
            WatchLog.objects.create(user=user, episode=ep, duration=100)

        # Mock async_to_sync and get_channel_layer to avoid async issues in synchronous tests
        with patch('users.services.get_channel_layer') as mock_channel_layer, \
             patch('users.services.async_to_sync') as mock_async_to_sync:
            mock_async_to_sync.return_value = MagicMock()

            check_badges(user)

        assert UserBadge.objects.filter(user=user, badge=otaku_badge).exists()

    def test_does_not_award_otaku_badge_if_less_than_5_completed(self, user, otaku_badge):
        # Create 5 anime, but only watch 4 of them
        for i in range(5):
            anime = Anime.objects.create(title=f"Anime {i}")
            season = Season.objects.create(anime=anime, number=1)
            ep = Episode.objects.create(season=season, number=1)

            if i < 4:
                # Watch the episode
                WatchLog.objects.create(user=user, episode=ep, duration=100)

        with patch('users.services.get_channel_layer') as mock_channel_layer, \
             patch('users.services.async_to_sync') as mock_async_to_sync:

            check_badges(user)

        assert not UserBadge.objects.filter(user=user, badge=otaku_badge).exists()

    def test_does_not_award_otaku_badge_if_series_incomplete(self, user, otaku_badge):
        # Create 5 anime. For the 5th one, create 2 episodes but watch only 1.
        for i in range(5):
            anime = Anime.objects.create(title=f"Anime {i}")
            season = Season.objects.create(anime=anime, number=1)
            ep1 = Episode.objects.create(season=season, number=1)

            if i == 4:
                # Add another episode to the 5th anime
                ep2 = Episode.objects.create(season=season, number=2)
                # Watch only ep1
                WatchLog.objects.create(user=user, episode=ep1, duration=100)
            else:
                # Watch ep1 for others
                WatchLog.objects.create(user=user, episode=ep1, duration=100)

        with patch('users.services.get_channel_layer') as mock_channel_layer, \
             patch('users.services.async_to_sync') as mock_async_to_sync:

            check_badges(user)

        assert not UserBadge.objects.filter(user=user, badge=otaku_badge).exists()
