import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aniscrap_core.settings')
django.setup()

from users.badge_system import check_badges
from users.models import User, WatchLog
from content.models import Episode

user = User.objects.first()
if user:
    import time
    from django.db import connection, reset_queries
    reset_queries()
    start = time.time()
    check_badges(user)
    end = time.time()
    print(f"Time taken: {end - start:.4f}s")
    print(f"Queries: {len(connection.queries)}")
