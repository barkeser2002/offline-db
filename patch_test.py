import re

content = open('users/tests/test_new_badges.py', 'r').read()

new_content = re.sub(
    r"mock_qs\.count\.return_value = 999",
    r"mock_qs.__len__.return_value = 999",
    content
)

new_content = re.sub(
    r"mock_qs\.count\.return_value = 1000",
    r"mock_qs.__len__.return_value = 1000",
    new_content
)

# Wait, the error is inside `anime_ep_ids = set(Episode.objects.filter(season__anime=anime).values_list('id', flat=True))`
# This error implies that `last_log = WatchLog.objects.filter(user=user).select_related('episode__season__anime').order_by('-watched_at').first()` returned something, and `last_log.episode.season.anime` was an empty list!
