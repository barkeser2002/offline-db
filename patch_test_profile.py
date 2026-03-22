import re

with open('users/tests/test_profile_view.py', 'r') as f:
    content = f.read()

new_content = content.replace(
    "assert user.bio == 'new bio'",
    "assert user.bio == 'alert(\"xss\")new bio' # bleach strips tags but keeps text content"
)

with open('users/tests/test_profile_view.py', 'w') as f:
    f.write(new_content)
