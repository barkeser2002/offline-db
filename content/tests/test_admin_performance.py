from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from content.models import Anime, Season
from django.test.utils import CaptureQueriesContext
from django.db import connection

User = get_user_model()

class SeasonAdminPerformanceTest(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='password'
        )
        self.client.force_login(self.admin_user)

        # Create 10 seasons, each with a different anime
        for i in range(10):
            anime = Anime.objects.create(title=f"Anime {i}")
            Season.objects.create(anime=anime, number=1, title=f"Season 1")

    def test_season_admin_changelist_queries(self):
        url = reverse('admin:content_season_changelist')

        # Use follow=True to handle redirects if any
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(url, follow=True)

        self.assertEqual(response.status_code, 200)

        # We expect efficient queries.
        # With list_select_related or auto-select_related: ~6 queries.
        # Without it: ~15 queries (N+1).

        # print(f"Captured queries: {len(ctx.captured_queries)}")
        # for q in ctx.captured_queries:
        #     print(q['sql'])

        self.assertLess(len(ctx.captured_queries), 10)

from content.models import FansubGroup

class FansubGroupAdminPerformanceTest(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser('admin2', 'admin2@example.com', 'password')
        self.client.force_login(self.admin_user)

        # Create 10 FansubGroups with 10 different owners
        for i in range(10):
            user = User.objects.create_user(username=f'user{i}', password='password')
            FansubGroup.objects.create(name=f'Fansub {i}', owner=user)

    def test_fansubgroup_admin_changelist_performance(self):
        url = reverse('admin:content_fansubgroup_changelist')

        # Initial request to warm up
        self.client.get(url)

        # Expected queries:
        # 1. Session check
        # 2. User auth
        # 3. COUNT(*)
        # 4. Main query for FansubGroup + select_related('owner')
        # Without optimization, this would be ~14 queries.
        with self.assertNumQueries(5):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
