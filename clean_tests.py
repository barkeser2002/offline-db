import re

files_to_clean = [
    'users/tests/test_badges.py',
    'users/tests/test_content_creator_badge.py',
    'users/tests/test_opinionated_badge.py',
    'users/tests/test_new_badges.py'
]

for file in files_to_clean:
    with open(file, 'r') as f:
        content = f.read()

    # Remove redundant check_badges lines
    content = content.replace("check_badges(self.user)\n        check_badges(self.user)", "check_badges(self.user)")
    content = content.replace("cache.delete(f\"user_{self.user.id}_chat_badges_checked\")", "")
    content = content.replace("cache.delete(f\"user_{self.user.id}_badges_checked\")", "cache.delete(f'user_{self.user.id}_badges_checked')")

    with open(file, 'w') as f:
        f.write(content)
