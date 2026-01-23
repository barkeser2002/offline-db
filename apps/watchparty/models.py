from django.db import models
from django.conf import settings
import uuid

class Room(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Linking to Episode from content app. We need to import it carefully to avoid circular deps if any.
    # Assuming content.Episode is stable.
    episode = models.ForeignKey('content.Episode', on_delete=models.CASCADE, related_name='watch_rooms')
    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hosted_rooms')
    max_participants = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Room {self.uuid} - {self.episode}"

class Participant(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='watch_participations')
    joined_at = models.DateTimeField(auto_now_add=True)
    # Roles: host is defined in Room, but we can track permissions here if needed.
    # For now, let's just track presence.
    is_online = models.BooleanField(default=True)

    class Meta:
        unique_together = ('room', 'user')

    def __str__(self):
        return f"{self.user} in {self.room}"

class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_system = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender} in {self.room}"
