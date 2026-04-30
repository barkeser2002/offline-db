import os
import django
from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.core.cache import cache

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aniscrap_core.settings')
django.setup()

from users.models import User, Badge, UserBadge
from content.models import Anime, Subscription, Review, Episode, Season
from users.services import check_badges

# Clear cache
cache.clear()

try:
    user = User.objects.get(username='perftest_manual7')
except User.DoesNotExist:
    user = User.objects.create_user(username='perftest_manual7', password='password')

import setup_badges

with CaptureQueriesContext(connection) as ctx:
    cache_key = f'user_{user.id}_badges_checked'
    if cache.get(cache_key):
        pass
    else:
        all_badges = cache.get('all_badges_dict')
        if all_badges is None:
            all_badges = {b.slug: b for b in Badge.objects.all()}
            cache.set('all_badges_dict', all_badges, 3600)
        awarded_slugs = set(UserBadge.objects.filter(user=user).values_list('badge__slug', flat=True))
        strategy_cache = {}
        new_badges = []

        # Here we mimic what the loop does to find where the queries come from.
        # But we don't call the actual strategies yet, just checking the framework overhead.

print(f"\nQueries executed (overhead): {len(ctx.captured_queries)}")

# Now run with strategy loop
cache.clear()
with CaptureQueriesContext(connection) as ctx2:
    cache_key = f'user_{user.id}_badges_checked'
    if cache.get(cache_key):
        pass
    else:
        all_badges = cache.get('all_badges_dict')
        if all_badges is None:
            all_badges = {b.slug: b for b in Badge.objects.all()}
            cache.set('all_badges_dict', all_badges, 3600)
        awarded_slugs = set(UserBadge.objects.filter(user=user).values_list('badge__slug', flat=True))
        strategy_cache = {}
        new_badges = []

        from users.badge_system import GENERAL_BADGE_STRATEGIES
        for strategy in GENERAL_BADGE_STRATEGIES:
            with CaptureQueriesContext(connection) as ctx_strat:
                strategy.check(user, awarded_slugs, all_badges, new_badges, cache=strategy_cache)
            if len(ctx_strat.captured_queries) > 0:
                print(f"Strategy {strategy.__class__.__name__} executed {len(ctx_strat.captured_queries)} queries.")

print(f"\nQueries executed (total with strategies): {len(ctx2.captured_queries)}")
