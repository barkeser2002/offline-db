import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

class Anime(models.Model):
    title = models.CharField(max_length=255)
    synopsis = models.TextField(blank=True)
    cover_image = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Season(models.Model):
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE, related_name='seasons')
    number = models.PositiveIntegerField()
    title = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.anime.title} - Season {self.number}"

class Episode(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name='episodes')
    number = models.PositiveIntegerField()
    title = models.CharField(max_length=255, blank=True)
    thumbnail = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.season.anime.title} - S{self.season.number}E{self.number}"

class FansubGroup(models.Model):
    name = models.CharField(max_length=255)
    website = models.URLField(blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='fansub_groups')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class VideoFile(models.Model):
    QUALITY_CHOICES = [
        ('480p', '480p'),
        ('720p', '720p'),
        ('1080p', '1080p'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE, related_name='video_files')
    fansub_group = models.ForeignKey(FansubGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name='videos')
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='uploaded_videos')
    quality = models.CharField(max_length=10, choices=QUALITY_CHOICES)
    hls_path = models.CharField(max_length=500, help_text=_("Path to .m3u8 file"))
    encryption_key = models.CharField(max_length=255, help_text=_("AES-128 Key"))
    file_size_bytes = models.BigIntegerField(default=0, help_text=_("Total size of HLS assets in bytes"))
    is_hardcoded = models.BooleanField(default=False, help_text=_("Disables Subtitle uploads if True"))
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.episode} - {self.quality}"

class Subtitle(models.Model):
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE, related_name='subtitles')
    fansub_group = models.ForeignKey(FansubGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name='subtitles')
    lang = models.CharField(max_length=10, default='tr')
    file = models.FileField(upload_to='subtitles/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.episode} - {self.lang}"
