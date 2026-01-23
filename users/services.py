from django.utils import timezone
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
    # Bulk fetch badges and awarded status
    all_badges = {b.slug: b for b in Badge.objects.all()}
    awarded_slugs = set(UserBadge.objects.filter(user=user).values_list('badge__slug', flat=True))
    new_badges = []

    for strategy in GENERAL_BADGE_STRATEGIES:
        strategy.check(user, awarded_slugs, all_badges, new_badges)

    # Commit all new badges
    if new_badges:
        UserBadge.objects.bulk_create(new_badges, ignore_conflicts=True)
        _send_badge_notifications(user, new_badges)

def check_chat_badges(user):
    """
    Checks badges related to chat activity.
    Optimized to minimize DB queries.
    Refactored to use Strategy Pattern.
    """
    all_badges = {b.slug: b for b in Badge.objects.all()}
    awarded_slugs = set(UserBadge.objects.filter(user=user).values_list('badge__slug', flat=True))
    new_badges = []

    for strategy in CHAT_BADGE_STRATEGIES:
        strategy.check(user, awarded_slugs, all_badges, new_badges)

    # Commit all new badges
    if new_badges:
        UserBadge.objects.bulk_create(new_badges, ignore_conflicts=True)
        _send_badge_notifications(user, new_badges)
