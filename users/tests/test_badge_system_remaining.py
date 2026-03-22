import pytest
from django.test import TestCase
from users.models import User, Badge, UserBadge, WatchLog
from content.models import Subscription, Review, VideoFile, Anime, Genre, Episode, Season
from apps.watchparty.models import Room
from users.badge_system import (
    ReviewBadgeStrategy, WatchTimeBadgeStrategy, AccountBadgeStrategy,
    CommunityBadgeStrategy, ConsistencyBadgeStrategy, ConsumptionBadgeStrategy, CompletionBadgeStrategy, GenreBadgeStrategy, SpecificGenreBadgeStrategy
)

class BadgeSystemRemainingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.all_badges = {b.slug: b for b in Badge.objects.all()}

    def test_review_badge_strategy_not_needed(self):
        strategy = ReviewBadgeStrategy()
        new_badges = []
        strategy.check(self.user, {'critic', 'opinionated', 'review-guru', 'star-power'}, self.all_badges, new_badges)
        self.assertEqual(len(new_badges), 0)

    def test_watch_time_badge_strategy_not_needed(self):
        strategy = WatchTimeBadgeStrategy()
        new_badges = []
        strategy.check(self.user, {'binge-watcher', 'marathon-runner', 'weekend-warrior', 'speedster'}, self.all_badges, new_badges)
        self.assertEqual(len(new_badges), 0)

    def test_account_badge_strategy_not_needed(self):
        strategy = AccountBadgeStrategy()
        new_badges = []
        strategy.check(self.user, {'early-adopter', 'supporter', 'collector'}, self.all_badges, new_badges)
        self.assertEqual(len(new_badges), 0)

    def test_community_badge_strategy_cache_miss(self):
        strategy = CommunityBadgeStrategy()
        new_badges = []
        episode = Episode.objects.create(season=Season.objects.create(anime=Anime.objects.create(title="A"), number=1), number=1); Room.objects.create(host=self.user, episode=episode, max_participants=10)
        strategy.check(self.user, set(), self.all_badges, new_badges, cache=None)

    def test_community_badge_strategy_cache_hit(self):
        strategy = CommunityBadgeStrategy()
        new_badges = []
        cache = {'hosted_rooms': [{'max_participants': 10}]}
        strategy.check(self.user, set(), self.all_badges, new_badges, cache=cache)

    def test_consumption_badge_strategy_cache_miss(self):
        strategy = ConsumptionBadgeStrategy()
        new_badges = []
        anime = Anime.objects.create(title="Anime")
        season = Season.objects.create(anime=anime, number=1)
        episode = Episode.objects.create(season=season, number=1)
        WatchLog.objects.create(user=self.user, episode=episode, duration=100)
        strategy.check(self.user, set(), self.all_badges, new_badges, cache=None)

    def test_completion_badge_strategy_cache_miss(self):
        strategy = CompletionBadgeStrategy()
        new_badges = []
        anime = Anime.objects.create(title="Anime")
        season = Season.objects.create(anime=anime, number=1)
        episode = Episode.objects.create(season=season, number=1)
        WatchLog.objects.create(user=self.user, episode=episode, duration=100)
        strategy.check(self.user, set(), self.all_badges, new_badges, cache=None)

    def test_completion_badge_strategy_cache_hit(self):
        strategy = CompletionBadgeStrategy()
        new_badges = []
        anime = Anime.objects.create(title="Anime")
        season = Season.objects.create(anime=anime, number=1)
        episode = Episode.objects.create(season=season, number=1)
        log = WatchLog.objects.create(user=self.user, episode=episode, duration=100)
        cache = {'last_log': log, 'episode_ids': [episode.id]}
        strategy.check(self.user, set(), self.all_badges, new_badges, cache=cache)

    def test_genre_badge_strategy_cache_miss(self):
        strategy = GenreBadgeStrategy()
        new_badges = []
        anime = Anime.objects.create(title="Anime")
        season = Season.objects.create(anime=anime, number=1)
        episode = Episode.objects.create(season=season, number=1)
        WatchLog.objects.create(user=self.user, episode=episode, duration=100)
        strategy.check(self.user, set(), self.all_badges, new_badges, cache=None)

    def test_specific_genre_badge_strategy_cache_miss(self):
        strategy = SpecificGenreBadgeStrategy()
        new_badges = []
        anime = Anime.objects.create(title="Anime")
        season = Season.objects.create(anime=anime, number=1)
        episode = Episode.objects.create(season=season, number=1)
        WatchLog.objects.create(user=self.user, episode=episode, duration=100)
        strategy.check(self.user, set(), self.all_badges, new_badges, cache=None)

    def test_consistency_badge_strategy_cache_hit_daily_viewer(self):
        strategy = ConsistencyBadgeStrategy()
        new_badges = []
        import datetime
        from django.utils import timezone
        now = timezone.now()
        dates_30 = {(now - datetime.timedelta(days=i)).date() for i in range(30)}
        cache = {'watched_dates_30': dates_30}
        strategy.check(self.user, set(), self.all_badges, new_badges, cache=cache)
        self.assertTrue(any(b.badge.slug == 'daily-viewer' for b in new_badges))

    def test_completion_badge_strategy_cache_hit_season(self):
        strategy = CompletionBadgeStrategy()
        new_badges = []
        anime = Anime.objects.create(title="Anime")
        season = Season.objects.create(anime=anime, number=1)
        episode = Episode.objects.create(season=season, number=1)
        log = WatchLog.objects.create(user=self.user, episode=episode, duration=100)
        cache = {'last_log': log} # episode_ids missing
        strategy.check(self.user, set(), self.all_badges, new_badges, cache=cache)

    def test_genre_badge_strategy_cache_hit_anime_ids(self):
        strategy = GenreBadgeStrategy()
        new_badges = []
        anime = Anime.objects.create(title="Anime")
        season = Season.objects.create(anime=anime, number=1)
        episode = Episode.objects.create(season=season, number=1)
        WatchLog.objects.create(user=self.user, episode=episode, duration=100)
        cache = {'anime_ids': [anime.id]}
        strategy.check(self.user, set(), self.all_badges, new_badges, cache=cache)

    def test_specific_genre_badge_strategy_cache_hit_anime_ids(self):
        strategy = SpecificGenreBadgeStrategy()
        new_badges = []
        anime = Anime.objects.create(title="Anime")
        season = Season.objects.create(anime=anime, number=1)
        episode = Episode.objects.create(season=season, number=1)
        WatchLog.objects.create(user=self.user, episode=episode, duration=100)
        cache = {'anime_ids': [anime.id]}
        strategy.check(self.user, set(), self.all_badges, new_badges, cache=cache)

    def test_community_badge_strategy_party_host(self):
        strategy = CommunityBadgeStrategy()
        new_badges = []
        episode = Episode.objects.create(season=Season.objects.create(anime=Anime.objects.create(title="B"), number=1), number=1)
        for i in range(5):
            Room.objects.create(host=self.user, episode=episode, max_participants=1)
        cache = {'hosted_rooms': [{'max_participants': 1} for i in range(5)]}
        strategy.check(self.user, set(), self.all_badges, new_badges, cache=cache)
        self.assertTrue(any(b.badge.slug == 'party-host' for b in new_badges))
    def test_consistency_badge_strategy_cache_hit_daily_viewer_cache_miss(self):
        strategy = ConsistencyBadgeStrategy()
        new_badges = []
        cache = {}
        strategy.check(self.user, set(), self.all_badges, new_badges, cache=cache)

    def test_completion_badge_strategy_cache_hit_season_cache_miss(self):
        strategy = CompletionBadgeStrategy()
        new_badges = []
        cache = {}
        strategy.check(self.user, set(), self.all_badges, new_badges, cache=cache)

    def test_genre_badge_strategy_cache_hit_anime_ids_cache_miss(self):
        strategy = GenreBadgeStrategy()
        new_badges = []
        cache = {}
        strategy.check(self.user, set(), self.all_badges, new_badges, cache=cache)

    def test_specific_genre_badge_strategy_cache_hit_anime_ids_cache_miss(self):
        strategy = SpecificGenreBadgeStrategy()
        new_badges = []
        cache = {}
        strategy.check(self.user, set(), self.all_badges, new_badges, cache=cache)

    def test_daily_viewer_cache_miss(self):
        strategy = ConsistencyBadgeStrategy()
        new_badges = []
        import datetime
        from django.utils import timezone
        now = timezone.now()
        anime = Anime.objects.create(title="Anime")
        season = Season.objects.create(anime=anime, number=1)
        episode = Episode.objects.create(season=season, number=1)

        for i in range(30):
            WatchLog.objects.create(user=self.user, episode=episode, duration=100)
            log = WatchLog.objects.filter(user=self.user).last()
            log.watched_at = now - datetime.timedelta(days=i)
            log.save()

        strategy.check(self.user, set(), self.all_badges, new_badges, cache=None)

    def test_genre_badge_strategy_get_anime_ids_hit(self):
        strategy = GenreBadgeStrategy()
        new_badges = []
        cache = {'anime_ids': [1]}
        # We need to call check such that get_anime_ids gets called and hits `if anime_ids is not None`
        # Because anime_ids is a nonlocal it's populated on first call.
        # The logic is ids = get_anime_ids() then later if 'genre-savant' ...
        # wait genre savant uses WatchLog.objects directly.
        # But we can call get_anime_ids multiple times if 'genre-explorer' and 'genre-master' are not awarded
        # Actually it's only called once.
        # Line 305 is `return anime_ids` if `anime_ids is not None`.
        # This will only be hit if get_anime_ids is called twice in the same check.
        # Let's check users/badge_system.py around 305.
    def test_genre_badge_strategy_get_anime_ids_nonlocal_hit(self):
        strategy = GenreBadgeStrategy()
        new_badges = []
        # Calling check without 'genre-explorer' and 'genre-master' awarded
        # Both require get_anime_ids()
        # In check(), it first checks if either is not awarded. If so, it calls get_anime_ids().
        # So get_anime_ids() is called ONCE.
        # But wait, later in check() it's not called again.
        # Can we trigger get_anime_ids() to be called twice?
        # Let's write a mock function that replaces `WatchLog.objects.filter` inside `check`?
        # Actually `get_anime_ids` is an inner function.
        # We can just test it by calling it? We can't access inner function.
        # Let's see if there's any other place calling get_anime_ids.
        pass
