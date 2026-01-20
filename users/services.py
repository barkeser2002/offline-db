from django.utils import timezone
from datetime import timedelta
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
