import os
import django
from django.test.utils import CaptureQueriesContext
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aniscrap_core.settings')
django.setup()

from users.models import User, Badge, UserBadge
from content.models import Anime, Subscription, Review
from users.services import check_badges

# Badges were created by setup_badges.py earlier.

try:
    user = User.objects.get(username='perftest_manual')
except User.DoesNotExist:
    user = User.objects.create_user(username='perftest_manual', password='password')

anime = Anime.objects.create(title='Test Anime 3')
Subscription.objects.create(user=user, anime=anime)
Review.objects.create(user=user, anime=anime, rating=10, text='Great!')

# Run check_badges once to warm up (and award badges if logic works)
check_badges(user)

with CaptureQueriesContext(connection) as ctx:
    check_badges(user)

print(f"\nQueries executed: {len(ctx.captured_queries)}")
for q in ctx.captured_queries:
    print(q)
