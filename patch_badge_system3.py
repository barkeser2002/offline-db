import re

with open('users/badge_system.py', 'r') as f:
    content = f.read()

# Fix cache key setting and retrieval so caching is done properly per user,
# preventing the issue from just moving from check_badges to first strategy execution.

# Replace ReviewBadgeStrategy aggregate
content = re.sub(
    r"        stats = Review\.objects\.filter\(user=user\)\.aggregate\(\n            total=Count\('id'\),\n            perfect=Count\('id', filter=Q\(rating=10\)\)\n        \)\n        total_reviews = stats\['total'\] or 0\n        perfect_reviews = stats\['perfect'\] or 0",
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

# Replace Subscription check
content = re.sub(
    r"        if 'collector' not in awarded_slugs:\n            if Subscription\.objects\.filter\(user=user\)\.count\(\) >= 10:",
    r"""        if 'collector' not in awarded_slugs:
            if cache is not None:
                if 'subscription_count' not in cache:
                    cache['subscription_count'] = Subscription.objects.filter(user=user).count()
                sub_count = cache['subscription_count']
            else:
                sub_count = Subscription.objects.filter(user=user).count()
            if sub_count >= 10:""",
    content
)


# Replace VideoFile check
content = re.sub(
    r"        if 'content-creator' not in awarded_slugs:\n            if VideoFile\.objects\.filter\(uploader=user\)\.count\(\) >= 5:",
    r"""        if 'content-creator' not in awarded_slugs:
            if cache is not None:
                if 'video_count' not in cache:
                    cache['video_count'] = VideoFile.objects.filter(uploader=user).count()
                video_count = cache['video_count']
            else:
                video_count = VideoFile.objects.filter(uploader=user).count()
            if video_count >= 5:""",
    content
)

# Replace type counts in ConsistencyBadgeStrategy
content = re.sub(
    r"            type_counts_qs = Anime\.objects\.filter\(\n                id__in=anime_qs\n            \)\.values\('type'\)\.annotate\(count=Count\('id', distinct=True\)\)",
    r"""            if cache is not None:
                if 'type_counts' not in cache:
                    cache['type_counts'] = list(Anime.objects.filter(id__in=anime_qs).values('type').annotate(count=Count('id', distinct=True)))
                type_counts_qs = cache['type_counts']
            else:
                type_counts_qs = Anime.objects.filter(id__in=anime_qs).values('type').annotate(count=Count('id', distinct=True))""",
    content
)

with open('users/badge_system.py', 'w') as f:
    f.write(content)
