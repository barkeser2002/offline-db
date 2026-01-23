from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.urls import reverse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Episode, Subscription, Genre, Season
from .tasks import send_new_episode_email_task

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
        for sub in subscribers:
            notifications.append(Notification(
                user=sub.user,
                title=f"New Episode: {anime.title}",
                message=f"Episode {instance.number} of {anime.title} is now available!",
                link=reverse('watch', args=[instance.id])
            ))

        if notifications:
            Notification.objects.bulk_create(notifications)

            # Send real-time notifications via WebSockets
            channel_layer = get_channel_layer()
            for notification in notifications:
                group_name = f"user_{notification.user.id}"
                async_to_sync(channel_layer.group_send)(
                    group_name,
                    {
                        'type': 'notification_message',
                        'title': notification.title,
                        'message': notification.message,
                        'link': notification.link,
                    }
                )

        # Trigger Email Task (Async)
        send_new_episode_email_task.delay(instance.id)
