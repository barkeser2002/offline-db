from django.test import TestCase
from users.models import User, Badge, UserBadge, WatchLog
from content.models import Anime, Season, Episode, Genre

class SpecificGenreBadgeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')

        # Get Badges (created by migration, but in tests we need to create them manually
        # if migrations are not fully applied or to be safe)
        self.nightmare_badge, _ = Badge.objects.get_or_create(
            slug='nightmare',
            defaults={
                'name': 'Nightmare',
                'description': 'Watched 5 Horror anime.'
            }
        )
        self.comedy_badge, _ = Badge.objects.get_or_create(
            slug='comedy-gold',
            defaults={
                'name': 'Comedy Gold',
                'description': 'Watched 5 Comedy anime.'
            }
        )

        # Create Genres
        self.horror = Genre.objects.create(name='Horror', slug='horror')
        self.comedy = Genre.objects.create(name='Comedy', slug='comedy')

    def test_nightmare_badge(self):
        # Watch 4 different Horror Anime
        for i in range(4):
            anime = Anime.objects.create(title=f"Horror Anime {i}")
            anime.genres.add(self.horror)
            season = Season.objects.create(anime=anime, number=1)
            episode = Episode.objects.create(season=season, number=1)
            WatchLog.objects.create(user=self.user, episode=episode, duration=100)

        # Should not have badge yet
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.nightmare_badge).exists())

        # Watch 5th Horror Anime
        anime_5 = Anime.objects.create(title="Horror Anime 5")
        anime_5.genres.add(self.horror)
        season = Season.objects.create(anime=anime_5, number=1)
        episode = Episode.objects.create(season=season, number=1)
        WatchLog.objects.create(user=self.user, episode=episode, duration=100)

        # Should have badge now
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=self.nightmare_badge).exists())

    def test_comedy_gold_badge(self):
        # Watch 4 different Comedy Anime
        for i in range(4):
            anime = Anime.objects.create(title=f"Comedy Anime {i}")
            anime.genres.add(self.comedy)
            season = Season.objects.create(anime=anime, number=1)
            episode = Episode.objects.create(season=season, number=1)
            WatchLog.objects.create(user=self.user, episode=episode, duration=100)

        # Should not have badge yet
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.comedy_badge).exists())

        # Watch 5th Comedy Anime
        anime_5 = Anime.objects.create(title="Comedy Anime 5")
        anime_5.genres.add(self.comedy)
        season = Season.objects.create(anime=anime_5, number=1)
        episode = Episode.objects.create(season=season, number=1)
        WatchLog.objects.create(user=self.user, episode=episode, duration=100)

        # Should have badge now
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=self.comedy_badge).exists())

    def test_mixed_genres_dont_interfere(self):
        # Watch 4 Horror
        for i in range(4):
            anime = Anime.objects.create(title=f"Horror Anime {i}")
            anime.genres.add(self.horror)
            season = Season.objects.create(anime=anime, number=1)
            episode = Episode.objects.create(season=season, number=1)
            WatchLog.objects.create(user=self.user, episode=episode, duration=100)

        # Watch 4 Comedy
        for i in range(4):
            anime = Anime.objects.create(title=f"Comedy Anime {i}")
            anime.genres.add(self.comedy)
            season = Season.objects.create(anime=anime, number=1)
            episode = Episode.objects.create(season=season, number=1)
            WatchLog.objects.create(user=self.user, episode=episode, duration=100)

        # Verify neither badge is awarded
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.nightmare_badge).exists())
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.comedy_badge).exists())

    def test_case_insensitive_genre_match(self):
         # Create Lowercase Horror
        horror_lower = Genre.objects.create(name='horror', slug='horror-lower')

        # Watch 5 anime with lowercase horror
        for i in range(5):
            anime = Anime.objects.create(title=f"Lower Horror Anime {i}")
            anime.genres.add(horror_lower)
            season = Season.objects.create(anime=anime, number=1)
            episode = Episode.objects.create(season=season, number=1)
            WatchLog.objects.create(user=self.user, episode=episode, duration=100)

        # Should have badge (assuming iexact works)
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=self.nightmare_badge).exists())
