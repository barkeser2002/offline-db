import re

with open('users/models.py', 'r') as f:
    content = f.read()

new_content = re.sub(
    r'is_premium = models.BooleanField\(default=False, verbose_name=_\("Premium Status"\)\)',
    'is_premium = models.BooleanField(default=False, verbose_name=_("Premium Status"))\n    bio = models.TextField(blank=True, verbose_name=_("Bio"))',
    content
)

with open('users/models.py', 'w') as f:
    f.write(new_content)
