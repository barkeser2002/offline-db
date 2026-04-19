with open('users/services.py', 'r') as f:
    content = f.read()

content = content.replace("    cache_key = f'user_{user.id}_badges_checked'\n    if cache.get(cache_key):\n        return\n", "")
content = content.replace("\n    cache.set(cache_key, True, 30 * 60)\n", "")

content = content.replace("    cache_key = f'user_{user.id}_chat_badges_checked'\n    if cache.get(cache_key):\n        return\n", "")

with open('users/services.py', 'w') as f:
    f.write(content)
