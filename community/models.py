from django.db import models
from django.contrib.auth.models import User
from content.models import Episode

class FansubGroup(models.Model):
    name = models.CharField(max_length=255)
    members = models.ManyToManyField(User, related_name='fansub_groups', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Subtitle(models.Model):
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE, related_name='subtitles')
    fansub_group = models.ForeignKey(FansubGroup, on_delete=models.SET_NULL, null=True, blank=True)
    language = models.CharField(max_length=50, default='tr') # 'en', 'tr'
    file = models.FileField(upload_to='subtitles/')
    is_softsub = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.episode} - {self.language}"
