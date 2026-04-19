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
    user = User.objects.get(username='perftest_manual8')
except User.DoesNotExist:
    user = User.objects.create_user(username='perftest_manual8', password='password')

import setup_badges

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
            strategy.check(user, awarded_slugs, all_badges, new_badges, cache=strategy_cache)

print(f"\nQueries executed (total with strategies): {len(ctx2.captured_queries)}")
for q in ctx2.captured_queries:
    print(q['sql'])
