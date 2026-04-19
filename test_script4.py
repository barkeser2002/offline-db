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
    user = User.objects.get(username='perftest_manual3')
except User.DoesNotExist:
    user = User.objects.create_user(username='perftest_manual3', password='password')

anime = Anime.objects.create(title='Test Anime 4')
season = Season.objects.create(anime=anime, title="Season 1", number=1)
ep1 = Episode.objects.create(season=season, title="Ep 1", number=1)
ep2 = Episode.objects.create(season=season, title="Ep 2", number=2)

from users.models import WatchLog
WatchLog.objects.create(user=user, episode=ep1, duration=1200)

with CaptureQueriesContext(connection) as ctx:
    check_badges(user)

print(f"\nQueries executed (cold cache, with episodes watched): {len(ctx.captured_queries)}")
for q in ctx.captured_queries:
    print(q['sql'])
