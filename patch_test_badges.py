import re

with open('users/tests/test_badges.py', 'r') as f:
    content = f.read()

new_content = content.replace(
    "WatchLog.objects.create(\n            user=self.user,\n            episode=self.episodes[4],\n            duration=1200\n        )",
    "WatchLog.objects.create(\n            user=self.user,\n            episode=self.episodes[4],\n            duration=1200\n        )\n        from django.core.cache import cache\n        cache.delete(f'user_{self.user.id}_badges_checked')\n        check_badges(self.user)"
)

new_content = new_content.replace(
    "WatchLog.objects.create(\n            user=self.user,\n            episode=many_episodes[49],\n            duration=1200\n        )",
    "WatchLog.objects.create(\n            user=self.user,\n            episode=many_episodes[49],\n            duration=1200\n        )\n        from django.core.cache import cache\n        cache.delete(f'user_{self.user.id}_badges_checked')\n        check_badges(self.user)"
)

new_content = new_content.replace(
    "WatchLog.objects.create(\n            user=self.user,\n            episode=self.episodes[9],\n            duration=1200\n        )",
    "WatchLog.objects.create(\n            user=self.user,\n            episode=self.episodes[9],\n            duration=1200\n        )\n        from django.core.cache import cache\n        cache.delete(f'user_{self.user.id}_badges_checked')\n        check_badges(self.user)"
)

new_content = new_content.replace(
    "WatchLog.objects.create(\n            user=self.user,\n            episode=episodes[4],\n            duration=1200\n        )",
    "WatchLog.objects.create(\n            user=self.user,\n            episode=episodes[4],\n            duration=1200\n        )\n        from django.core.cache import cache\n        cache.delete(f'user_{self.user.id}_badges_checked')\n        check_badges(self.user)"
)

new_content = new_content.replace(
    "ChatMessage.objects.create(\n            user=self.user,\n            username=self.user.username,\n            room_name='test_room',\n            message='Message 50'\n        )",
    "ChatMessage.objects.create(\n            user=self.user,\n            username=self.user.username,\n            room_name='test_room',\n            message='Message 50'\n        )\n        from django.core.cache import cache\n        from users.services import check_chat_badges\n        cache.delete(f'user_{self.user.id}_chat_badges_checked')\n        check_chat_badges(self.user)"
)

new_content = new_content.replace(
    "ChatMessage.objects.create(\n            user=self.user,\n            username=self.user.username,\n            room_name='room_final',\n            message='Hello'\n        )",
    "ChatMessage.objects.create(\n            user=self.user,\n            username=self.user.username,\n            room_name='room_final',\n            message='Hello'\n        )\n        from django.core.cache import cache\n        from users.services import check_chat_badges\n        cache.delete(f'user_{self.user.id}_chat_badges_checked')\n        check_chat_badges(self.user)"
)


with open('users/tests/test_badges.py', 'w') as f:
    f.write(new_content)
