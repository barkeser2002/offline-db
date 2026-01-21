from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import Count
from .models import Badge, UserBadge, WatchLog
from core.models import ChatMessage
from content.models import Subscription

def check_badges(user):
    """
    Checks and awards badges to the user based on criteria.
    """
    # 1. Binge Watcher: Watched 5+ episodes in the last 24 hours.
    try:
        binge_badge = Badge.objects.get(slug='binge-watcher')
        # Check if user already has it
        if not UserBadge.objects.filter(user=user, badge=binge_badge).exists():
            last_24h = timezone.now() - timedelta(hours=24)
            # Count distinct episodes watched
            distinct_episodes_count = WatchLog.objects.filter(
                user=user,
                watched_at__gte=last_24h
            ).values('episode').distinct().count()

            if distinct_episodes_count >= 5:
                UserBadge.objects.get_or_create(user=user, badge=binge_badge)
    except Badge.DoesNotExist:
        pass

    # 1.1 Weekend Warrior: Watched 5+ episodes on a single weekend day.
    try:
        weekend_warrior_badge = Badge.objects.get(slug='weekend-warrior')
        if not UserBadge.objects.filter(user=user, badge=weekend_warrior_badge).exists():
            # Check if today is Saturday (5) or Sunday (6)
            today = timezone.now().date()
            if today.weekday() in [5, 6]:
                # Count episodes watched TODAY
                distinct_episodes_today = WatchLog.objects.filter(
                    user=user,
                    watched_at__date=today
                ).values('episode').distinct().count()

                if distinct_episodes_today >= 5:
                    UserBadge.objects.get_or_create(user=user, badge=weekend_warrior_badge)
    except Badge.DoesNotExist:
        pass

    # 2. Supporter: Is Premium.
    try:
        supporter_badge = Badge.objects.get(slug='supporter')
        if not UserBadge.objects.filter(user=user, badge=supporter_badge).exists():
            if user.is_premium:
                UserBadge.objects.get_or_create(user=user, badge=supporter_badge)
    except Badge.DoesNotExist:
        pass

    # 3. Veteran: Account created over 1 year ago.
    try:
        veteran_badge = Badge.objects.get(slug='veteran')
        if not UserBadge.objects.filter(user=user, badge=veteran_badge).exists():
            if user.date_joined <= timezone.now() - timedelta(days=365):
                UserBadge.objects.get_or_create(user=user, badge=veteran_badge)
    except Badge.DoesNotExist:
        pass

    # 4. Night Owl: Watched an episode between 2 AM and 5 AM.
    try:
        night_owl_badge = Badge.objects.get(slug='night-owl')
        if not UserBadge.objects.filter(user=user, badge=night_owl_badge).exists():
            last_log = WatchLog.objects.filter(user=user).order_by('-watched_at').first()
            if last_log:
                hour = last_log.watched_at.hour
                if 2 <= hour < 5:
                    UserBadge.objects.get_or_create(user=user, badge=night_owl_badge)
    except Badge.DoesNotExist:
        pass

    # 5. Early Bird: Watched an episode within 1 hour of release.
    try:
        early_bird_badge = Badge.objects.get(slug='early-bird')
        if not UserBadge.objects.filter(user=user, badge=early_bird_badge).exists():
            last_log = WatchLog.objects.filter(user=user).select_related('episode').order_by('-watched_at').first()
            if last_log:
                episode_created_at = last_log.episode.created_at
                watched_at = last_log.watched_at

                # Check if watched within 1 hour (3600 seconds) of creation
                # We use abs() just in case of slight clock skews, though usually watched_at > created_at
                diff = watched_at - episode_created_at
                if timedelta(seconds=0) <= diff <= timedelta(hours=1):
                    UserBadge.objects.get_or_create(user=user, badge=early_bird_badge)
    except Badge.DoesNotExist:
        pass

    # 7. Collector: Subscribed to 10 different anime.
    try:
        collector_badge = Badge.objects.get(slug='collector')
        if not UserBadge.objects.filter(user=user, badge=collector_badge).exists():
            subscription_count = Subscription.objects.filter(user=user).count()
            if subscription_count >= 10:
                UserBadge.objects.get_or_create(user=user, badge=collector_badge)
    except Badge.DoesNotExist:
        pass

    # 8. Season Completist: Completed an entire season.
    try:
        season_completist_badge = Badge.objects.get(slug='season-completist')
        # This badge can be awarded multiple times? Usually badges are unique per user-badge pair in this system.
        # Assuming unique for now based on other badges.
        if not UserBadge.objects.filter(user=user, badge=season_completist_badge).exists():
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
                        UserBadge.objects.get_or_create(user=user, badge=season_completist_badge)
    except Badge.DoesNotExist:
        pass

    # 9. Marathoner: Watched 50 episodes in total.
    try:
        marathoner_badge = Badge.objects.get(slug='marathoner')
        if not UserBadge.objects.filter(user=user, badge=marathoner_badge).exists():
            watched_count = WatchLog.objects.filter(user=user).values('episode').distinct().count()
            if watched_count >= 50:
                UserBadge.objects.get_or_create(user=user, badge=marathoner_badge)
    except Badge.DoesNotExist:
        pass

    # 10. Genre Explorer: Watched anime from 5 different genres.
    try:
        genre_explorer_badge = Badge.objects.get(slug='genre-explorer')
        if not UserBadge.objects.filter(user=user, badge=genre_explorer_badge).exists():
            # Get all episodes watched by user
            watched_episodes = WatchLog.objects.filter(user=user).select_related('episode__season__anime')

            # Optimization: Filter distinct animes first.
            distinct_anime_ids = watched_episodes.values_list('episode__season__anime_id', flat=True).distinct()

            from content.models import Anime
            # Count distinct genres across all watched animes
            distinct_genres_count = Anime.objects.filter(
                id__in=distinct_anime_ids
            ).values('genres__id').distinct().count()

            if distinct_genres_count >= 5:
                UserBadge.objects.get_or_create(user=user, badge=genre_explorer_badge)
    except Badge.DoesNotExist:
        pass

    # 11. Loyal Fan: Watched 10 episodes of the same anime.
    try:
        loyal_fan_badge = Badge.objects.get(slug='loyal-fan')
        if not UserBadge.objects.filter(user=user, badge=loyal_fan_badge).exists():
            # Get the anime of the last watched episode
            last_log = WatchLog.objects.filter(user=user).select_related('episode__season__anime').order_by('-watched_at').first()
            if last_log:
                anime = last_log.episode.season.anime
                # Count episodes watched for this anime
                watched_count = WatchLog.objects.filter(
                    user=user,
                    episode__season__anime=anime
                ).values('episode').distinct().count()

                if watched_count >= 10:
                    UserBadge.objects.get_or_create(user=user, badge=loyal_fan_badge)
    except Badge.DoesNotExist:
        pass

    # 12. Streak Master: Watched anime for 7 consecutive days.
    try:
        streak_master_badge = Badge.objects.get(slug='streak-master')
        if not UserBadge.objects.filter(user=user, badge=streak_master_badge).exists():
            today = timezone.now().date()
            start_date = today - timedelta(days=6)
            # Make start_date aware to prevent naive datetime warnings
            start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))

            # Count distinct days in the last 7 days (inclusive)
            distinct_days_count = WatchLog.objects.filter(
                user=user,
                watched_at__gte=start_datetime  # Check from start of the 7-day window
            ).values('watched_at__date').distinct().count()

            if distinct_days_count >= 7:
                UserBadge.objects.get_or_create(user=user, badge=streak_master_badge)
    except Badge.DoesNotExist:
        pass

    # 13. Daily Viewer: Watched anime for 30 consecutive days.
    try:
        daily_viewer_badge = Badge.objects.get(slug='daily-viewer')
        if not UserBadge.objects.filter(user=user, badge=daily_viewer_badge).exists():
            today = timezone.now().date()
            start_date = today - timedelta(days=29)  # 30 days including today
            # Make start_date aware to prevent naive datetime warnings
            start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))

            # Count distinct days in the last 30 days
            distinct_days_count = WatchLog.objects.filter(
                user=user,
                watched_at__gte=start_datetime
            ).values('watched_at__date').distinct().count()

            if distinct_days_count >= 30:
                UserBadge.objects.get_or_create(user=user, badge=daily_viewer_badge)
    except Badge.DoesNotExist:
        pass

def check_chat_badges(user):
    """
    Checks badges related to chat activity.
    """
    # 5. Commentator: Posted 50 chat messages.
    try:
        commentator_badge = Badge.objects.get(slug='commentator')
        if not UserBadge.objects.filter(user=user, badge=commentator_badge).exists():
            message_count = ChatMessage.objects.filter(user=user).count()
            if message_count >= 50:
                UserBadge.objects.get_or_create(user=user, badge=commentator_badge)
    except Badge.DoesNotExist:
        pass

    # 6. Social Butterfly: Participated in 5 different chat rooms.
    try:
        social_butterfly_badge = Badge.objects.get(slug='social-butterfly')
        if not UserBadge.objects.filter(user=user, badge=social_butterfly_badge).exists():
            distinct_rooms = ChatMessage.objects.filter(user=user).values('room_name').distinct().count()
            if distinct_rooms >= 5:
                UserBadge.objects.get_or_create(user=user, badge=social_butterfly_badge)
    except Badge.DoesNotExist:
        pass
