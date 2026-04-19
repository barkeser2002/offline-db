from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta, datetime
from django.db.models import Count, Q
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Badge, UserBadge, WatchLog, Notification
from core.models import ChatMessage
from content.models import Subscription, Review, VideoFile, Anime, Genre, Episode
from apps.watchparty.models import Room
from .badge_system import GENERAL_BADGE_STRATEGIES, CHAT_BADGE_STRATEGIES

def _send_badge_notifications(user, new_badges):
    """
    Helper to create notifications and send WebSocket events for new badges.
    """
    if not new_badges:
        return

    notifications = []
    for user_badge in new_badges:
        notifications.append(Notification(
            user=user,
            title="New Badge Earned!",
            message=f"You have unlocked the '{user_badge.badge.name}' badge!",
        ))

    Notification.objects.bulk_create(notifications)

    channel_layer = get_channel_layer()
    group_name = f"user_{user.id}"

    for notif in notifications:
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'notification_message',
                'title': notif.title,
                'message': notif.message,
                'link': notif.link or '',
            }
        )

def check_badges(user):
    """
    Checks and awards badges to the user based on criteria.
    Optimized to minimize DB queries.
    Refactored to use Strategy Pattern.
    """
    cache_key = f'user_{user.id}_badges_checked'
    if cache.get(cache_key):
        return

    # Bulk fetch badges and awarded status
    all_badges = cache.get('all_badges_dict')
    if all_badges is None:
        all_badges = {b.slug: b for b in Badge.objects.all()}
        cache.set('all_badges_dict', all_badges, 3600)
    awarded_slugs = set(UserBadge.objects.filter(user=user).values_list('badge__slug', flat=True))
    strategy_cache = {}
    # Pre-fetch common data to avoid DB queries during strategy checks
    today = timezone.now().date()
    last_24h = timezone.now() - timedelta(days=1)
    last_hour = timezone.now() - timedelta(hours=1)
    start_date_30 = today - timedelta(days=29)
    start_datetime_30 = timezone.make_aware(datetime.combine(start_date_30, datetime.min.time()))
    strategy_cache['review_stats'] = Review.objects.filter(user=user).aggregate(total=Count('id'), perfect=Count('id', filter=Q(rating=10)))
    strategy_cache['subscription_count'] = Subscription.objects.filter(user=user).count()
    strategy_cache['video_count'] = VideoFile.objects.filter(uploader=user).count()
    strategy_cache['episode_ids'] = list(WatchLog.objects.filter(user=user).values_list('episode_id', flat=True).distinct())
    strategy_cache['anime_ids'] = list(WatchLog.objects.filter(user=user).values_list('episode__season__anime_id', flat=True).distinct())
    strategy_cache['last_log'] = WatchLog.objects.filter(user=user).select_related('episode__season__anime').order_by('-watched_at').first()
    strategy_cache['watched_dates_30'] = set(WatchLog.objects.filter(user=user, watched_at__gte=start_datetime_30).values_list('watched_at__date', flat=True))
    strategy_cache['hosted_rooms'] = list(Room.objects.filter(host=user).values('max_participants'))
    stats = ChatMessage.objects.filter(user=user).values('room_name').distinct()
    strategy_cache['chat_stats'] = list(stats)
    strategy_cache['total_msgs'] = ChatMessage.objects.filter(user=user).count()
    new_badges = []

    for strategy in GENERAL_BADGE_STRATEGIES:
        strategy.check(user, awarded_slugs, all_badges, new_badges, cache=strategy_cache)

    # Commit all new badges
    if new_badges:
        UserBadge.objects.bulk_create(new_badges, ignore_conflicts=True)
        _send_badge_notifications(user, new_badges)

    cache.set(cache_key, True, 30 * 60)

def check_chat_badges(user):
    """
    Checks badges related to chat activity.
    Optimized to minimize DB queries.
    Refactored to use Strategy Pattern.
    """
    cache_key = f'user_{user.id}_chat_badges_checked'
    if cache.get(cache_key):
        return

    all_badges = cache.get('all_badges_dict')
    if all_badges is None:
        all_badges = {b.slug: b for b in Badge.objects.all()}
        cache.set('all_badges_dict', all_badges, 3600)
    awarded_slugs = set(UserBadge.objects.filter(user=user).values_list('badge__slug', flat=True))
    strategy_cache = {}
    # Pre-fetch common data to avoid DB queries during strategy checks
    today = timezone.now().date()
    last_24h = timezone.now() - timedelta(days=1)
    last_hour = timezone.now() - timedelta(hours=1)
    start_date_30 = today - timedelta(days=29)
    start_datetime_30 = timezone.make_aware(datetime.combine(start_date_30, datetime.min.time()))
    strategy_cache['review_stats'] = Review.objects.filter(user=user).aggregate(total=Count('id'), perfect=Count('id', filter=Q(rating=10)))
    strategy_cache['subscription_count'] = Subscription.objects.filter(user=user).count()
    strategy_cache['video_count'] = VideoFile.objects.filter(uploader=user).count()
    strategy_cache['episode_ids'] = list(WatchLog.objects.filter(user=user).values_list('episode_id', flat=True).distinct())
    strategy_cache['anime_ids'] = list(WatchLog.objects.filter(user=user).values_list('episode__season__anime_id', flat=True).distinct())
    strategy_cache['last_log'] = WatchLog.objects.filter(user=user).select_related('episode__season__anime').order_by('-watched_at').first()
    strategy_cache['watched_dates_30'] = set(WatchLog.objects.filter(user=user, watched_at__gte=start_datetime_30).values_list('watched_at__date', flat=True))
    strategy_cache['hosted_rooms'] = list(Room.objects.filter(host=user).values('max_participants'))
    stats = ChatMessage.objects.filter(user=user).values('room_name').distinct()
    strategy_cache['chat_stats'] = list(stats)
    strategy_cache['total_msgs'] = ChatMessage.objects.filter(user=user).count()
    new_badges = []

    for strategy in CHAT_BADGE_STRATEGIES:
        strategy.check(user, awarded_slugs, all_badges, new_badges, cache=strategy_cache)

    # Commit all new badges
    if new_badges:
        UserBadge.objects.bulk_create(new_badges, ignore_conflicts=True)
        _send_badge_notifications(user, new_badges)

    cache.set(cache_key, True, 30 * 60)
