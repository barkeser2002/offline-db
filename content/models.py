import uuid
from urllib.parse import urlencode
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.conf import settings

class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        base_url = reverse('search')
        query_string = urlencode({'genre': self.name})
        return f"{base_url}?{query_string}"

class Anime(models.Model):
    TYPE_CHOICES = [
        ('TV', 'TV Series'),
        ('Movie', 'Movie'),
        ('OVA', 'OVA'),
        ('ONA', 'ONA'),
        ('Special', 'Special'),
    ]

    title = models.CharField(max_length=255)
    synopsis = models.TextField(blank=True)
    cover_image = models.URLField(blank=True, null=True)
    genres = models.ManyToManyField(Genre, related_name='animes', blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='TV')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('anime_detail', args=[str(self.id)])

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

    def get_absolute_url(self):
        return reverse('watch', args=[str(self.id)])

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

class Subscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE, related_name='subscribers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'anime')

    def __str__(self):
        return f"{self.user} subscribed to {self.anime}"

class Review(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 11)])
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'anime')

    def __str__(self):
        return f"{self.user} - {self.anime} ({self.rating}/10)"

class WatchParty(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE, related_name='watch_parties')
    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hosted_parties')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Party {self.uuid} - {self.episode}"

    def get_absolute_url(self):
        return reverse('watch_party_detail', args=[str(self.uuid)])
