from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import WatchLog
from core.models import ChatMessage
from .services import check_badges, check_chat_badges

@receiver(post_save, sender=WatchLog)
def check_badges_on_watch(sender, instance, created, **kwargs):
    if created:
        check_badges(instance.user)

@receiver(post_save, sender=ChatMessage)
def check_badges_on_chat(sender, instance, created, **kwargs):
    if created and instance.user:
        check_chat_badges(instance.user)
