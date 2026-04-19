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
    user = User.objects.get(username='perftest_manual6')
except User.DoesNotExist:
    user = User.objects.create_user(username='perftest_manual6', password='password')

# Ensure we have all badges seeded so they exist in all_badges dictionary
# This ensures we don't accidentally skip a badge and skew the query count
import setup_badges

with CaptureQueriesContext(connection) as ctx:
    check_badges(user)

print(f"\nQueries executed (cold cache, check_badges): {len(ctx.captured_queries)}")

# Second run should only have 1 query (to fetch user) since everything is cached!
with CaptureQueriesContext(connection) as ctx2:
    check_badges(user)

print(f"\nQueries executed (warm cache, check_badges): {len(ctx2.captured_queries)}")
