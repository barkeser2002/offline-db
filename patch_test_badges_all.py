import glob
import os

test_files = glob.glob('users/tests/test_*.py')
for file in test_files:
    if file == 'users/tests/test_profile_view.py' or file == 'users/tests/test_serializers.py':
        continue
    with open(file, 'r') as f:
        content = f.read()

    new_content = content.replace(
        "WatchLog.objects.create(",
        "WatchLog.objects.create(\n            user=self.user,\n            episode=self.episodes[4],\n            duration=1200\n        )\n        from django.core.cache import cache\n        cache.delete(f'user_{self.user.id}_badges_checked')\n        check_badges(self.user)\n        #"
    )
