from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import WatchLog
from core.models import ChatMessage
from content.models import Subscription, Review, VideoFile
from apps.watchparty.models import Room
from .services import check_badges, check_chat_badges

@receiver(post_save, sender=VideoFile)
def check_badges_on_video_upload(sender, instance, created, **kwargs):
    if created and instance.uploader:
        check_badges(instance.uploader)

@receiver(post_save, sender=Review)
def check_badges_on_review(sender, instance, created, **kwargs):
    if created:
        check_badges(instance.user)

@receiver(post_save, sender=Subscription)
def check_badges_on_subscribe(sender, instance, created, **kwargs):
    if created:
        check_badges(instance.user)

@receiver(post_save, sender=WatchLog)
def check_badges_on_watch(sender, instance, created, **kwargs):
    if created:
        check_badges(instance.user)

@receiver(post_save, sender=ChatMessage)
def check_badges_on_chat(sender, instance, created, **kwargs):
    if created and instance.user:
        check_chat_badges(instance.user)

@receiver(post_save, sender=Room)
def check_badges_on_watch_party(sender, instance, created, **kwargs):
    if created:
        check_badges(instance.host)
