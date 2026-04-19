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
    user = User.objects.get(username='perftest_manual4')
except User.DoesNotExist:
    user = User.objects.create_user(username='perftest_manual4', password='password')

# We need to make sure the user hasn't been checked recently
cache.delete(f'user_{user.id}_badges_checked')

with CaptureQueriesContext(connection) as ctx:
    check_badges(user)

print(f"\nQueries executed (cold cache, check_badges): {len(ctx.captured_queries)}")
for q in ctx.captured_queries:
    print(q['sql'])
