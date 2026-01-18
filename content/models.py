import uuid
from django.db import models
from django.utils.text import slugify

class Anime(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='covers/', blank=True, null=True)

    # SEO Fields
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True, help_text="Comma separated keywords")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class Episode(models.Model):
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE, related_name='episodes')
    number = models.FloatField()
    title = models.CharField(max_length=255, blank=True)

    # Video Pipeline
    source_file = models.FileField(upload_to='raw_uploads/', blank=True, null=True)
    hls_playlist = models.CharField(max_length=500, blank=True, help_text="Path to master.m3u8")
    is_processed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['number']
        unique_together = ['anime', 'number']

    def __str__(self):
        return f"{self.anime.title} - EP {self.number}"

class VideoKey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE, related_name='keys')
    key_content = models.BinaryField(help_text="AES-128 Key bytes")
    iv = models.BinaryField(null=True, blank=True, help_text="Initialization Vector if needed")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Key for {self.episode}"
