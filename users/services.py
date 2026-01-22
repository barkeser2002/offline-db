from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import Count, Q
from .models import Badge, UserBadge, WatchLog
from core.models import ChatMessage
from content.models import Subscription, Review, WatchParty, VideoFile, Anime, Genre

def check_badges(user):
    """
    Checks and awards badges to the user based on criteria.
    Optimized to minimize DB queries.
    """
    # Bulk fetch badges and awarded status
    all_badges = {b.slug: b for b in Badge.objects.all()}
    awarded_slugs = set(UserBadge.objects.filter(user=user).values_list('badge__slug', flat=True))

    new_badges = []

    def award(slug):
        if slug in all_badges and slug not in awarded_slugs:
            new_badges.append(UserBadge(user=user, badge=all_badges[slug]))
            awarded_slugs.add(slug)

    # 0. Critic: Wrote first review.
    if 'critic' not in awarded_slugs and 'critic' in all_badges:
        if Review.objects.filter(user=user).exists():
            award('critic')

    # 0.5. Opinionated: Wrote 5 reviews.
    if 'opinionated' not in awarded_slugs and 'opinionated' in all_badges:
        if Review.objects.filter(user=user).count() >= 5:
            award('opinionated')

    # 1. Binge Watcher: Watched 5+ episodes in the last 24 hours.
    if 'binge-watcher' not in awarded_slugs and 'binge-watcher' in all_badges:
        last_24h = timezone.now() - timedelta(hours=24)
        distinct_episodes_count = WatchLog.objects.filter(
            user=user,
            watched_at__gte=last_24h
        ).values('episode').distinct().count()
        if distinct_episodes_count >= 5:
            award('binge-watcher')

    # 1.1 Weekend Warrior: Watched 5+ episodes on a single weekend day.
    if 'weekend-warrior' not in awarded_slugs and 'weekend-warrior' in all_badges:
        today = timezone.now().date()
        if today.weekday() in [5, 6]:
            distinct_episodes_today = WatchLog.objects.filter(
                user=user,
                watched_at__date=today
            ).values('episode').distinct().count()
            if distinct_episodes_today >= 5:
                award('weekend-warrior')

    # 2. Supporter: Is Premium.
    if 'supporter' not in awarded_slugs and 'supporter' in all_badges:
        if user.is_premium:
            award('supporter')

    # 3. Veteran: Account created over 1 year ago.
    if 'veteran' not in awarded_slugs and 'veteran' in all_badges:
        if user.date_joined <= timezone.now() - timedelta(days=365):
            award('veteran')

    # 4. Night Owl: Watched an episode between 2 AM and 5 AM.
    if 'night-owl' not in awarded_slugs and 'night-owl' in all_badges:
        last_log = WatchLog.objects.filter(user=user).order_by('-watched_at').first()
        if last_log:
            hour = last_log.watched_at.hour
            if 2 <= hour < 5:
                award('night-owl')

    # 4.5. Morning Glory: Watched an episode between 6 AM and 9 AM.
    if 'morning-glory' not in awarded_slugs and 'morning-glory' in all_badges:
        last_log = WatchLog.objects.filter(user=user).order_by('-watched_at').first()
        if last_log:
            hour = last_log.watched_at.hour
            if 6 <= hour < 9:
                award('morning-glory')

    # 5. Early Bird: Watched an episode within 1 hour of release.
    if 'early-bird' not in awarded_slugs and 'early-bird' in all_badges:
        last_log = WatchLog.objects.filter(user=user).select_related('episode').order_by('-watched_at').first()
        if last_log:
            episode_created_at = last_log.episode.created_at
            watched_at = last_log.watched_at
            diff = watched_at - episode_created_at
            if timedelta(seconds=0) <= diff <= timedelta(hours=1):
                award('early-bird')

    # 7. Collector: Subscribed to 10 different anime.
    if 'collector' not in awarded_slugs and 'collector' in all_badges:
        subscription_count = Subscription.objects.filter(user=user).count()
        if subscription_count >= 10:
            award('collector')

    # 8. Season Completist: Completed an entire season.
    if 'season-completist' not in awarded_slugs and 'season-completist' in all_badges:
        last_log = WatchLog.objects.filter(user=user).select_related('episode__season').order_by('-watched_at').first()
        if last_log:
            season = last_log.episode.season
            total_episodes = season.episodes.count()
            if total_episodes > 0:
                watched_count = WatchLog.objects.filter(
                    user=user,
                    episode__season=season
                ).values('episode').distinct().count()
                if watched_count >= total_episodes:
                    award('season-completist')

    # 9. Marathoner: Watched 50 episodes in total.
    if 'marathoner' not in awarded_slugs and 'marathoner' in all_badges:
        watched_count = WatchLog.objects.filter(user=user).values('episode').distinct().count()
        if watched_count >= 50:
            award('marathoner')

    # 10. Genre Explorer: Watched anime from 5 different genres.
    if 'genre-explorer' not in awarded_slugs and 'genre-explorer' in all_badges:
        watched_episodes = WatchLog.objects.filter(user=user).select_related('episode__season__anime')
        distinct_anime_ids = watched_episodes.values_list('episode__season__anime_id', flat=True).distinct()
        distinct_genres_count = Anime.objects.filter(
            id__in=distinct_anime_ids
        ).values('genres__id').distinct().count()
        if distinct_genres_count >= 5:
            award('genre-explorer')

    # 11. Loyal Fan: Watched 10 episodes of the same anime.
    if 'loyal-fan' not in awarded_slugs and 'loyal-fan' in all_badges:
        last_log = WatchLog.objects.filter(user=user).select_related('episode__season__anime').order_by('-watched_at').first()
        if last_log:
            anime = last_log.episode.season.anime
            watched_count = WatchLog.objects.filter(
                user=user,
                episode__season__anime=anime
            ).values('episode').distinct().count()
            if watched_count >= 10:
                award('loyal-fan')

    # 12. Streak Master: Watched anime for 7 consecutive days.
    if 'streak-master' not in awarded_slugs and 'streak-master' in all_badges:
        today = timezone.now().date()
        start_date = today - timedelta(days=6)
        start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
        distinct_days_count = WatchLog.objects.filter(
            user=user,
            watched_at__gte=start_datetime
        ).values('watched_at__date').distinct().count()
        if distinct_days_count >= 7:
            award('streak-master')

    # 13. Daily Viewer: Watched anime for 30 consecutive days.
    if 'daily-viewer' not in awarded_slugs and 'daily-viewer' in all_badges:
        today = timezone.now().date()
        start_date = today - timedelta(days=29)
        start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
        distinct_days_count = WatchLog.objects.filter(
            user=user,
            watched_at__gte=start_datetime
        ).values('watched_at__date').distinct().count()
        if distinct_days_count >= 30:
            award('daily-viewer')

    # 14. Genre Master: Watched 10 different anime from the same genre.
    if 'genre-master' not in awarded_slugs and 'genre-master' in all_badges:
        watched_anime_ids = WatchLog.objects.filter(user=user).values_list('episode__season__anime_id', flat=True).distinct()
        if watched_anime_ids:
            qs = Genre.objects.filter(animes__id__in=watched_anime_ids).annotate(
                user_anime_count=Count('animes', filter=Q(animes__id__in=watched_anime_ids))
            )
            if qs.filter(user_anime_count__gte=10).exists():
                 award('genre-master')

    # 15. Speedster: Watched 3 episodes in 1 hour.
    if 'speedster' not in awarded_slugs and 'speedster' in all_badges:
        last_hour = timezone.now() - timedelta(hours=1)
        count = WatchLog.objects.filter(
            user=user,
            watched_at__gte=last_hour
        ).values('episode').distinct().count()
        if count >= 3:
            award('speedster')

    # 16. Party Host: Hosted 5 Watch Parties.
    if 'party-host' not in awarded_slugs and 'party-host' in all_badges:
        host_count = WatchParty.objects.filter(host=user).count()
        if host_count >= 5:
            award('party-host')

    # 18. Content Creator: Uploaded 5 videos.
    if 'content-creator' not in awarded_slugs and 'content-creator' in all_badges:
        upload_count = VideoFile.objects.filter(uploader=user).count()
        if upload_count >= 5:
            award('content-creator')

    # Commit all new badges
    if new_badges:
        UserBadge.objects.bulk_create(new_badges, ignore_conflicts=True)

def check_chat_badges(user):
    """
    Checks badges related to chat activity.
    Optimized to minimize DB queries.
    """
    all_badges = {b.slug: b for b in Badge.objects.all()}
    awarded_slugs = set(UserBadge.objects.filter(user=user).values_list('badge__slug', flat=True))

    new_badges = []

    def award(slug):
        if slug in all_badges and slug not in awarded_slugs:
            new_badges.append(UserBadge(user=user, badge=all_badges[slug]))
            awarded_slugs.add(slug)

    # 5. Commentator: Posted 50 chat messages.
    if 'commentator' not in awarded_slugs and 'commentator' in all_badges:
        message_count = ChatMessage.objects.filter(user=user).count()
        if message_count >= 50:
            award('commentator')

    # 6. Social Butterfly: Participated in 5 different chat rooms.
    if 'social-butterfly' not in awarded_slugs and 'social-butterfly' in all_badges:
        distinct_rooms = ChatMessage.objects.filter(user=user).values('room_name').distinct().count()
        if distinct_rooms >= 5:
            award('social-butterfly')

    # 17. Party Animal: Participated in 5 different Watch Parties.
    if 'party-animal' not in awarded_slugs and 'party-animal' in all_badges:
        distinct_parties = ChatMessage.objects.filter(
            user=user,
            room_name__startswith='party_'
        ).values('room_name').distinct().count()
        if distinct_parties >= 5:
            award('party-animal')

    # Commit all new badges
    if new_badges:
        UserBadge.objects.bulk_create(new_badges, ignore_conflicts=True)
