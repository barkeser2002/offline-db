import pytest
from users.models import User, Badge, UserBadge, WatchLog
from content.models import Anime, Season, Episode
from users.services import check_badges
from django.utils import timezone

@pytest.mark.django_db
class TestSuperFanBadge:
    @pytest.fixture
    def user(self):
        return User.objects.create_user(username='testuser', password='password')

    @pytest.fixture
    def super_fan_badge(self):
        return Badge.objects.get_or_create(slug='super-fan', defaults={'name': 'Super Fan', 'description': 'Completed all episodes.'})[0]

    @pytest.fixture
    def anime_setup(self):
        anime = Anime.objects.create(title="Test Anime")
        season1 = Season.objects.create(anime=anime, number=1)
        season2 = Season.objects.create(anime=anime, number=2)

        ep1 = Episode.objects.create(season=season1, number=1)
        ep2 = Episode.objects.create(season=season1, number=2)
        ep3 = Episode.objects.create(season=season2, number=1)

        return [ep1, ep2, ep3]

    def test_awards_super_fan_badge(self, user, super_fan_badge, anime_setup):
        episodes = anime_setup

        # Watch all episodes
        for ep in episodes:
            WatchLog.objects.create(user=user, episode=ep, duration=100)

        check_badges(user)

        assert UserBadge.objects.filter(user=user, badge=super_fan_badge).exists()

    def test_does_not_award_if_incomplete(self, user, super_fan_badge, anime_setup):
        episodes = anime_setup
        # Watch only 2 of 3 episodes
        WatchLog.objects.create(user=user, episode=episodes[0], duration=100)
        WatchLog.objects.create(user=user, episode=episodes[1], duration=100)

        check_badges(user)

        assert not UserBadge.objects.filter(user=user, badge=super_fan_badge).exists()

    def test_does_not_award_if_watched_same_episode_twice(self, user, super_fan_badge, anime_setup):
        episodes = anime_setup
        # Watch ep1 twice and ep2 once, but missing ep3
        WatchLog.objects.create(user=user, episode=episodes[0], duration=100)
        WatchLog.objects.create(user=user, episode=episodes[0], duration=100)
        WatchLog.objects.create(user=user, episode=episodes[1], duration=100)

        check_badges(user)

        assert not UserBadge.objects.filter(user=user, badge=super_fan_badge).exists()
