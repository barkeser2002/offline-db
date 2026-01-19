from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.urls import reverse
from .models import Episode, Subscription

@receiver(post_save, sender=Episode)
@receiver(post_delete, sender=Episode)
def clear_home_cache(sender, instance, **kwargs):
    """
    Clear the homepage cache whenever an episode is added, updated, or deleted.
    """
    cache.delete('home_latest_episodes')

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
