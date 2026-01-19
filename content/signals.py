from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Episode

@receiver(post_save, sender=Episode)
@receiver(post_delete, sender=Episode)
def clear_home_cache(sender, instance, **kwargs):
    """
    Clear the homepage cache whenever an episode is added, updated, or deleted.
    """
    cache.delete('home_latest_episodes')
