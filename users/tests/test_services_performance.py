from django.test import TestCase
from django.contrib.auth import get_user_model
from django.test.utils import CaptureQueriesContext
from django.db import connection
from users.services import check_badges
from users.models import Badge, UserBadge
from content.models import Anime, Subscription, Review

User = get_user_model()

class BadgePerformanceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='perftest', password='password')
        # Badges should be seeded by migrations
        # Verify a few key badges exist
        self.assertTrue(Badge.objects.filter(slug='critic').exists())
        self.assertTrue(Badge.objects.filter(slug='collector').exists())

    def test_check_badges_query_count(self):
        # Create some conditions to trigger badges
        anime = Anime.objects.create(title='Test Anime')
        Subscription.objects.create(user=self.user, anime=anime)
        Review.objects.create(user=self.user, anime=anime, rating=10, text='Great!')

        # Run check_badges once to warm up (and award badges if logic works)
        check_badges(self.user)

        # Now run again. It should check existing badges and NOT award duplicates.
        # This is where we want to minimize queries (checking "if not exists").

        with CaptureQueriesContext(connection) as ctx:
            check_badges(self.user)

        # Without optimization, this will do:
        # 1 query for each badge to get the Badge object (unless cached, but local get() isn't cached across calls usually)
        # 1 query for each badge to check UserBadge exists
        # There are ~18 badges. So ~36 queries.

        print(f"\nQueries executed: {len(ctx.captured_queries)}")

        # Optimized version should be well under 30 queries (was 56)
        self.assertLess(len(ctx.captured_queries), 30)

    def test_badges_awarded_correctly(self):
        # Create a review to trigger the badge
        anime = Anime.objects.create(title='Test Anime 2')
        Review.objects.create(user=self.user, anime=anime, rating=10, text='Great!')

        # Verify 'critic' badge is awarded
        check_badges(self.user)
        critic = Badge.objects.get(slug='critic')
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=critic).exists())
