from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import WatchLog
from content.models import Subscription, Review, VideoFile
from apps.watchparty.models import Room, Message
from .tasks import calculate_badges_task, calculate_chat_badges_task

@receiver(post_save, sender=VideoFile)
def check_badges_on_video_upload(sender, instance, created, **kwargs):
    if created and instance.uploader:
        calculate_badges_task.delay(instance.uploader.id)

@receiver(post_save, sender=Review)
def check_badges_on_review(sender, instance, created, **kwargs):
    if created:
        calculate_badges_task.delay(instance.user.id)

@receiver(post_save, sender=Subscription)
def check_badges_on_subscribe(sender, instance, created, **kwargs):
    if created:
        calculate_badges_task.delay(instance.user.id)

@receiver(post_save, sender=WatchLog)
def check_badges_on_watch(sender, instance, created, **kwargs):
    if created:
        calculate_badges_task.delay(instance.user.id)

@receiver(post_save, sender=Message)
def check_badges_on_chat(sender, instance, created, **kwargs):
    if created and instance.sender:
        calculate_chat_badges_task.delay(instance.sender.id)

@receiver(post_save, sender=Room)
def check_badges_on_watch_party(sender, instance, created, **kwargs):
    if created:
        calculate_badges_task.delay(instance.host.id)
