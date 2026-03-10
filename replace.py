import sys
import re

content = open('users/badge_system.py', 'r').read()

new_content = re.sub(
    r"WatchLog\.objects\.filter\((.*?)\)\.values\('episode'\)\.distinct\(\)\.count\(\)",
    r"len(set(WatchLog.objects.filter(\1).values_list('episode_id', flat=True)))",
    content
)

open('users/badge_system.py', 'w').write(new_content)
