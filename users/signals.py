from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import WatchLog
from .services import check_badges

@receiver(post_save, sender=WatchLog)
def check_badges_on_watch(sender, instance, created, **kwargs):
    if created:
        check_badges(instance.user)
