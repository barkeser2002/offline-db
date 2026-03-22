import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.urls import reverse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Anime, Episode, Subscription, Genre, Season
from .tasks import send_new_episode_email_task, send_websocket_notifications_task

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Genre)
@receiver(post_delete, sender=Genre)
def clear_genre_cache(sender, instance, **kwargs):
    """
    Clear the genres cache whenever a genre is added, updated, or deleted.
    """
    cache.delete('all_genres')

@receiver(post_save, sender=Season)
@receiver(post_delete, sender=Season)
def clear_season_cache(sender, instance, **kwargs):
    """
    Clear the anime seasons cache whenever a season is modified.
    """
    cache.delete(f'anime_{instance.anime.id}_seasons')

@receiver(post_save, sender=Episode)
@receiver(post_delete, sender=Episode)
def clear_home_cache(sender, instance, **kwargs):
    """
    Clear the homepage cache whenever an episode is added, updated, or deleted.
    Also clears the anime seasons cache.
    """
    cache.delete('home_latest_episodes')
    cache.delete(f'anime_{instance.season.anime.id}_seasons')
    # Invalidate cache pages
    cache.clear()

@receiver(post_save, sender=Anime)
@receiver(post_delete, sender=Anime)
def clear_anime_cache(sender, instance, **kwargs):
    """
    Cache invalidation strategy: signal tabanlı (AnimeAdmin'de save signal -> cache clear)
    Clear cache when an Anime is saved (created/updated) or deleted.
    """
    logger.info(f"AnimeAdmin save signal -> cache clear triggered for Anime {instance.id}")
    cache.clear()

@receiver(post_save, sender=Episode)
def notify_subscribers(sender, instance, created, **kwargs):
    """
    Notify subscribers when a new episode is released.
    """
    if created:
        from users.models import Notification  # Avoid circular import
        anime = instance.season.anime
        subscribers = Subscription.objects.filter(anime=anime).select_related('user')

        notifications = []
        try:
            link = reverse('watch', args=[instance.id])
        except Exception:
            # Fallback if route is missing
            link = f"/watch/{instance.id}/"

        for sub in subscribers:
            notifications.append(Notification(
                user=sub.user,
                title=f"New Episode: {anime.title}",
                message=f"Episode {instance.number} of {anime.title} is now available!",
                link=link
            ))

        if notifications:
            Notification.objects.bulk_create(notifications)

            # Send real-time notifications via WebSockets using a background task
            # to prevent blocking the main thread with O(N) network operations.
            user_ids = [sub.user.id for sub in subscribers]
            title = f"New Episode: {anime.title}"
            message = f"Episode {instance.number} of {anime.title} is now available!"
            send_websocket_notifications_task.delay(user_ids, title, message, link)

        # Trigger Email Task (Async)
        send_new_episode_email_task.delay(instance.id)
