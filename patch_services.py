with open("users/services.py", "r") as f:
    lines = f.readlines()

out = []
for line in lines:
    if "strategy_cache = {}" in line:
        out.append(line)
        # Add pre-fetched common queries to avoid N+1 across strategies
        out.append("    # Pre-fetch common data to avoid DB queries during strategy checks\n")
        out.append("    today = timezone.now().date()\n")
        out.append("    last_24h = timezone.now() - timedelta(days=1)\n")
        out.append("    last_hour = timezone.now() - timedelta(hours=1)\n")
        out.append("    start_date_30 = today - timedelta(days=29)\n")
        out.append("    start_datetime_30 = timezone.make_aware(datetime.combine(start_date_30, datetime.min.time()))\n")

        # Populate the cache dict manually to prevent lazy eval N+1
        out.append("    strategy_cache['review_stats'] = Review.objects.filter(user=user).aggregate(total=Count('id'), perfect=Count('id', filter=Q(rating=10)))\n")
        out.append("    strategy_cache['subscription_count'] = Subscription.objects.filter(user=user).count()\n")
        out.append("    strategy_cache['video_count'] = VideoFile.objects.filter(uploader=user).count()\n")
        out.append("    strategy_cache['episode_ids'] = list(WatchLog.objects.filter(user=user).values_list('episode_id', flat=True).distinct())\n")
        out.append("    strategy_cache['anime_ids'] = list(WatchLog.objects.filter(user=user).values_list('episode__season__anime_id', flat=True).distinct())\n")
        out.append("    strategy_cache['last_log'] = WatchLog.objects.filter(user=user).select_related('episode__season__anime').order_by('-watched_at').first()\n")
        out.append("    strategy_cache['watched_dates_30'] = set(WatchLog.objects.filter(user=user, watched_at__gte=start_datetime_30).values_list('watched_at__date', flat=True))\n")
        out.append("    strategy_cache['hosted_rooms'] = list(Room.objects.filter(host=user).values('max_participants'))\n")

        # Chat badge specific stats (can pre-fetch them all or just for chat badges)
        out.append("    stats = ChatMessage.objects.filter(user=user).values('room_name').distinct()\n")
        out.append("    strategy_cache['chat_stats'] = list(stats)\n")
        out.append("    strategy_cache['total_msgs'] = ChatMessage.objects.filter(user=user).count()\n")

    else:
        out.append(line)

with open("users/services.py", "w") as f:
    f.writelines(out)
