import re

with open('users/badge_system.py', 'r') as f:
    content = f.read()

# 1. ReviewBadgeStrategy
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

# 2. AccountBadgeStrategy
content = re.sub(
    r"        if Subscription\.objects\.filter\(user=user\)\.count\(\) >= 10:",
    r"""        if cache is not None:
            if 'subscription_count' not in cache:
                cache['subscription_count'] = Subscription.objects.filter(user=user).count()
            sub_count = cache['subscription_count']
        else:
            sub_count = Subscription.objects.filter(user=user).count()
        if sub_count >= 10:""",
    content
)


# 3. CommunityBadgeStrategy
content = re.sub(
    r"        if VideoFile\.objects\.filter\(uploader=user\)\.count\(\) >= 5:",
    r"""        if cache is not None:
            if 'video_count' not in cache:
                cache['video_count'] = VideoFile.objects.filter(uploader=user).count()
            video_count = cache['video_count']
        else:
            video_count = VideoFile.objects.filter(uploader=user).count()
        if video_count >= 5:""",
    content
)

with open('users/badge_system.py', 'w') as f:
    f.write(content)
