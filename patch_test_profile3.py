import re

with open('users/tests/test_profile_view.py', 'r') as f:
    content = f.read()

new_content = content.replace(
    "response = client.patch(url, data, format='json')",
    "response = client.patch(url, data, format='json', secure=True)"
)

with open('users/tests/test_profile_view.py', 'w') as f:
    f.write(new_content)
