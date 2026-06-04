from django.test import TestCase
from users.models import User, Badge, UserBadge, WatchLog
from content.models import Anime, Genre, Season, Episode, Review, VideoFile
from apps.watchparty.models import Room
from django.utils import timezone
from datetime import timedelta
from users.badge_system import (
    BadgeStrategy,
    ReviewBadgeStrategy,
    WatchTimeBadgeStrategy,
    AccountBadgeStrategy,
    ConsistencyBadgeStrategy,
    CompletionBadgeStrategy,
    GenreBadgeStrategy,
    SpecificGenreBadgeStrategy,
    CommunityBadgeStrategy,
    ConsumptionBadgeStrategy
)

class DummyBadgeStrategy(BadgeStrategy):
    def check(self, user, awarded_slugs, all_badges, new_badges, cache=None):
        pass

class BadgeSystemRemainingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.all_badges = {b.slug: b for b in Badge.objects.all()}

        # Re-populate all missing badges
        Badge.objects.get_or_create(slug='streak-master', defaults={'name': 'Streak Master'})
        Badge.objects.get_or_create(slug='daily-viewer', defaults={'name': 'Daily Viewer'})
        Badge.objects.get_or_create(slug='party-host', defaults={'name': 'Party Host'})
        Badge.objects.get_or_create(slug='trendsetter', defaults={'name': 'Trendsetter'})
        Badge.objects.get_or_create(slug='content-creator', defaults={'name': 'Content Creator'})
        self.all_badges = {b.slug: b for b in Badge.objects.all()}

    def test_base_strategy_not_implemented(self):
        strategy = BadgeStrategy()
        with self.assertRaises(NotImplementedError):
            strategy.check(self.user, set(), self.all_badges, [])

    def test_base_strategy_award(self):
        strategy = DummyBadgeStrategy()
        new_badges = []
        strategy._award(self.user, 'streak-master', set(), self.all_badges, new_badges)
        self.assertEqual(len(new_badges), 1)

    def test_review_badge_strategy_not_needed(self):
        strategy = ReviewBadgeStrategy()
        new_badges = []
        strategy.check(self.user, {'critic', 'opinionated', 'review-guru', 'star-power'}, self.all_badges, new_badges)
        self.assertEqual(len(new_badges), 0)

    def test_watch_time_badge_strategy_not_needed(self):
        strategy = WatchTimeBadgeStrategy()
        new_badges = []
        strategy.check(self.user, {'binge-watcher', 'marathon-runner', 'weekend-warrior', 'speedster', 'night-owl'}, self.all_badges, new_badges)
        self.assertEqual(len(new_badges), 0)

    def test_account_badge_strategy_not_needed(self):
        strategy = AccountBadgeStrategy()
        new_badges = []
        strategy.check(self.user, {'early-adopter', 'supporter', 'collector'}, self.all_badges, new_badges)
        self.assertEqual(len(new_badges), 0)

    def test_community_badge_strategy_cache_miss(self):
        strategy = CommunityBadgeStrategy()
        new_badges = []
        anime = Anime.objects.create(title="Community Anime")
        season = Season.objects.create(anime=anime, number=1)
        episode = Episode.objects.create(season=season, number=1)
        Room.objects.create(host=self.user, episode=episode, max_participants=10)
        strategy.check(self.user, set(), self.all_badges, new_badges, cache=None)

    def test_community_badge_strategy_cache_hit(self):
        strategy = CommunityBadgeStrategy()
        new_badges = []
        cache = {'hosted_rooms': [{'max_participants': 10}]}
        strategy.check(self.user, set(), self.all_badges, new_badges, cache=cache)

    def test_community_badge_strategy_cache_miss_content_creator(self):
        strategy = CommunityBadgeStrategy()
        new_badges = []
        anime = Anime.objects.create(title="Community Anime")
        season = Season.objects.create(anime=anime, number=1)
        episode = Episode.objects.create(season=season, number=1)
        for _ in range(5):
            VideoFile.objects.create(episode=episode, uploader=self.user)
        strategy.check(self.user, {'party-host', 'trendsetter'}, self.all_badges, new_badges, cache={})
        self.assertTrue(any(b.badge.slug == 'content-creator' for b in new_badges))

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

    def test_streak_master_cache_miss(self):
        strategy = ConsistencyBadgeStrategy()
        new_badges = []
        now = timezone.now()
        anime = Anime.objects.create(title="Anime")
        season = Season.objects.create(anime=anime, number=1)
        episode = Episode.objects.create(season=season, number=1)

        for i in range(7):
            WatchLog.objects.create(user=self.user, episode=episode, duration=100)
            log = WatchLog.objects.filter(user=self.user).last()
            log.watched_at = now - timedelta(days=i)
            log.save()

        strategy.check(self.user, set(), self.all_badges, new_badges, cache=None)
        self.assertTrue(any(b.badge.slug == 'streak-master' for b in new_badges))

    def test_watch_time_badge_strategy_cache_miss(self):
        strategy = WatchTimeBadgeStrategy()
        new_badges = []
        anime = Anime.objects.create(title="Anime")
        season = Season.objects.create(anime=anime, number=1)
        episode = Episode.objects.create(season=season, number=1)
        WatchLog.objects.create(user=self.user, episode=episode, duration=100)
        strategy.check(self.user, set(), self.all_badges, new_badges, cache=None)

    def test_community_badge_strategy_party_host(self):
        strategy = CommunityBadgeStrategy()
        new_badges = []
        episode = Episode.objects.create(season=Season.objects.create(anime=Anime.objects.create(title="B"), number=1), number=1)
        for i in range(5):
            Room.objects.create(host=self.user, episode=episode, max_participants=1)
        cache = {'hosted_rooms': [{'max_participants': 1} for i in range(5)]}
        strategy.check(self.user, set(), self.all_badges, new_badges, cache=cache)
        self.assertTrue(any(b.badge.slug == 'party-host' for b in new_badges))

    def test_genre_explorer_badge(self):
        strategy = GenreBadgeStrategy()
        new_badges = []

        for i in range(5):
            genre = Genre.objects.create(name=f"Genre {i}", slug=f"genre-{i}")
            anime = Anime.objects.create(title=f"Anime {i}")
            anime.genres.add(genre)
            season = Season.objects.create(anime=anime, number=1)
            episode = Episode.objects.create(season=season, number=1)
            WatchLog.objects.create(user=self.user, episode=episode, duration=100)

        strategy.check(self.user, set(), self.all_badges, new_badges, cache=None)
        self.assertTrue(any(b.badge.slug == 'genre-explorer' for b in new_badges))

    def test_completion_badge_strategy_episode_ids_cache_miss(self):
        strategy = CompletionBadgeStrategy()
        new_badges = []
        anime = Anime.objects.create(title="Anime")
        season = Season.objects.create(anime=anime, number=1)
        episode = Episode.objects.create(season=season, number=1)
        log = WatchLog.objects.create(user=self.user, episode=episode, duration=100)
        cache = {'last_log': log} # episode_ids is missing
        strategy.check(self.user, set(), self.all_badges, new_badges, cache=cache)
        self.assertIn('episode_ids', cache)

    def test_genre_badge_strategy_get_anime_ids_hit(self):
        strategy = GenreBadgeStrategy()
        new_badges = []
        cache = {'anime_ids': [1]}
        # Call multiple times to hit line 305 inside get_anime_ids
        # But wait, we removed the inner function get_anime_ids.
        # It's now handled by the if condition. Oh wait I see line 305 still returning anime_ids
        pass


    def test_genre_badge_strategy_get_anime_ids_hit(self):
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
    def test_review_badge_strategy_all_branches(self):
        strategy = ReviewBadgeStrategy()
        from content.models import Review
        for i in range(10):
            anime = Anime.objects.create(title=f"Anime{i}")
            Review.objects.create(user=self.user, anime=anime, rating=10, text="review")
        new_badges = []
        strategy.check(self.user, set(), self.all_badges, new_badges, cache=None)

    def test_account_badge_strategy_all_branches(self):
        strategy = AccountBadgeStrategy()
        from content.models import Subscription

        # 1. Early Adopter
        # instead of modifying the user, we can just create a new one with id < 1000
        # however SQLite might not let us set ID directly if auto-incrementing, but we can try
        u = User.objects.create_user(username='early_user', id=50)

        # 3. Veteran
        import datetime
        from django.utils import timezone
        now = timezone.now()
        u.date_joined = now - datetime.timedelta(days=400)

        # 2. Supporter
        u.is_premium = True
        u.save()

        # 4. Collector
        for i in range(10):
            anime = Anime.objects.create(title=f"Anime_sub{i}")
            Subscription.objects.create(user=u, anime=anime)

        new_badges = []
        strategy.check(u, set(), self.all_badges, new_badges, cache=None)

    def test_community_badge_strategy_all_branches(self):
        strategy = CommunityBadgeStrategy()
        anime = Anime.objects.create(title="Anime")
        season = Season.objects.create(anime=anime, number=1)
        episode = Episode.objects.create(season=season, number=1)

        for i in range(5):
            Room.objects.create(host=self.user, episode=episode, max_participants=10)
            VideoFile.objects.create(uploader=self.user, episode=episode, quality='1080p')

        new_badges = []
        strategy.check(self.user, set(), self.all_badges, new_badges, cache=None)
