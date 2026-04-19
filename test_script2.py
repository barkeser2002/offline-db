import os
import django
from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.core.cache import cache

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aniscrap_core.settings')
django.setup()

from users.models import User, Badge, UserBadge
from content.models import Anime, Subscription, Review
from users.services import check_badges

# Clear cache to force it to do the actual check
cache.clear()

try:
    user = User.objects.get(username='perftest_manual')
except User.DoesNotExist:
    user = User.objects.create_user(username='perftest_manual', password='password')

# We want to measure the queries when badges are not cached for the specific user

with CaptureQueriesContext(connection) as ctx:
    check_badges(user)

print(f"\nQueries executed (cold cache, check_badges): {len(ctx.captured_queries)}")
for q in ctx.captured_queries:
    print(q['sql'])
