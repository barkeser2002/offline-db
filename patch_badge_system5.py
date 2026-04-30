import re

with open('users/badge_system.py', 'r') as f:
    content = f.read()

# Fix cache key setting and retrieval so caching is done properly per user,
# preventing the issue from just moving from check_badges to first strategy execution.

# Replace ReviewBadgeStrategy aggregate
content = re.sub(
    r"        if cache is not None:\n            if 'review_stats' not in cache:\n                cache\['review_stats'\] = Review\.objects\.filter\(user=user\)\.aggregate\(\n                    total=Count\('id'\),\n                    perfect=Count\('id', filter=Q\(rating=10\)\)\n                \)\n            stats = cache\['review_stats'\]\n        else:\n            stats = Review\.objects\.filter\(user=user\)\.aggregate\(\n                total=Count\('id'\),\n                perfect=Count\('id', filter=Q\(rating=10\)\)\n            \)\n        total_reviews = stats\['total'\] or 0\n        perfect_reviews = stats\['perfect'\] or 0",
    r"""        if cache is not None:
            if 'review_stats' not in cache:
                cache['review_stats'] = Review.objects.filter(user=user).aggregate(
                    total=Count('id'),
                    perfect=Count('id', filter=Q(rating=10))
                )
            stats = cache['review_stats']
        else:
            stats = Review.objects.filter(user=user).aggregate(
                total=Count('id'),
                perfect=Count('id', filter=Q(rating=10))
            )
        total_reviews = stats['total'] or 0
        perfect_reviews = stats['perfect'] or 0""",
    content
)

with open('users/badge_system.py', 'w') as f:
    f.write(content)
