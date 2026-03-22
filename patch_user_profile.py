import re

with open('users/views.py', 'r') as f:
    content = f.read()

new_content = content.replace(
    "'is_premium': getattr(user, 'is_premium', False),",
    "'is_premium': getattr(user, 'is_premium', False),\n            'bio': getattr(user, 'bio', ''),"
)

with open('users/views.py', 'w') as f:
    f.write(new_content)
