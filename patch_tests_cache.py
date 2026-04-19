import glob
import os

test_files = glob.glob('users/tests/test_*.py')
for file in test_files:
    if file in ('users/tests/test_profile_view.py', 'users/tests/test_serializers.py', 'users/tests/test_badge_strategy_base.py', 'users/tests/test_services_performance.py', 'users/tests/test_watch_log_api.py', 'users/tests/test_websocket_notifications.py', 'users/tests/test_notifications.py', 'users/tests/test_api_rate_limits.py', 'users/tests/test_api_throttling.py', 'users/tests/test_profile_update.py', 'users/tests/test_admin_performance.py', 'users/tests/test_models.py', 'users/tests/test_idor_auth.py', 'users/tests/test_validation.py', 'users/tests/test_badges_api.py'):
        continue

    with open(file, 'r') as f:
        content = f.read()

    new_content = content.replace("check_badges(self.user)", "from django.core.cache import cache\n        cache.delete(f'user_{self.user.id}_badges_checked')\n        check_badges(self.user)")
    new_content = new_content.replace("check_badges(user)", "from django.core.cache import cache\n        cache.delete(f'user_{user.id}_badges_checked')\n        check_badges(user)")
    new_content = new_content.replace("check_chat_badges(self.user)", "from django.core.cache import cache\n        cache.delete(f'user_{self.user.id}_chat_badges_checked')\n        check_chat_badges(self.user)")

    with open(file, 'w') as f:
        f.write(new_content)
