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
    
    STATUS_CHOICES = [
        ('Currently Airing', 'Currently Airing'),
        ('Finished Airing', 'Finished Airing'),
        ('Not yet aired', 'Not yet aired'),
    ]

    # Basic Info
    title = models.CharField(max_length=255)
    japanese_title = models.CharField(max_length=255, blank=True, verbose_name=_("Japanese Title"))
    english_title = models.CharField(max_length=255, blank=True, verbose_name=_("English Title"))
    synopsis = models.TextField(blank=True)
    cover_image = models.URLField(blank=True, null=True)
    banner_image = models.URLField(blank=True, null=True, verbose_name=_("Banner Image"))
    genres = models.ManyToManyField(Genre, related_name='animes', blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='TV')
    
    # Jikan API Fields
    mal_id = models.PositiveIntegerField(unique=True, null=True, blank=True, verbose_name=_("MyAnimeList ID"))
    score = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, verbose_name=_("MAL Score"))
    rank = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("MAL Rank"))
    popularity = models.PositiveIntegerField(null=True, blank=True)
    members = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("MAL Members"))
    
    # Production Info
    studio = models.CharField(max_length=255, blank=True)
    source = models.CharField(max_length=100, blank=True, help_text=_("Manga, Light Novel, Original, etc."))
    
    # Airing Info
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, blank=True)
    aired_from = models.DateField(null=True, blank=True)
    aired_to = models.DateField(null=True, blank=True)
    total_episodes = models.PositiveIntegerField(null=True, blank=True)
    duration = models.CharField(max_length=50, blank=True, help_text=_("e.g., '24 min per ep'"))
    rating = models.CharField(max_length=50, blank=True, help_text=_("e.g., 'PG-13', 'R'"))
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Anime")
        verbose_name_plural = _("Animes")
        indexes = [
            models.Index(fields=['popularity']),
            models.Index(fields=['score']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('anime_detail', args=[str(self.id)])
    
    @property
    def display_score(self):
        """Formatted score for display"""
        return f"{self.score:.2f}" if self.score else "N/A"


class Character(models.Model):
    """Character model for storing character information from Jikan API"""
    ROLE_CHOICES = [
        ('Main', 'Main'),
        ('Supporting', 'Supporting'),
    ]
    
    mal_id = models.PositiveIntegerField(unique=True, verbose_name=_("MyAnimeList Character ID"))
    name = models.CharField(max_length=255)
    name_kanji = models.CharField(max_length=255, blank=True)
    image_url = models.URLField(blank=True, null=True)
    about = models.TextField(blank=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = _("Character")
        verbose_name_plural = _("Characters")
    
    def __str__(self):
        return self.name


class AnimeCharacter(models.Model):
    """Many-to-Many through model for Anime-Character relationship with additional fields"""
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE, related_name='anime_characters')
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='anime_appearances')
    role = models.CharField(max_length=20, choices=Character.ROLE_CHOICES, default='Supporting')
    voice_actor_name = models.CharField(max_length=255, blank=True)
    voice_actor_language = models.CharField(max_length=50, blank=True, default='Japanese')
    voice_actor_image = models.URLField(blank=True, null=True)
    
    class Meta:
        unique_together = ('anime', 'character')
        ordering = ['role', 'character__name']
        verbose_name = _("Anime Character")
        verbose_name_plural = _("Anime Characters")
    
    def __str__(self):
        return f"{self.character.name} in {self.anime.title} ({self.role})"


class ExternalSource(models.Model):
    """Model for storing external video sources (HiAnime, etc.)"""
    SOURCE_TYPES = [
        ('hianime', 'HiAnime'),
        ('zoro', 'Zoro'),
        ('gogoanime', 'GogoAnime'),
        ('other', 'Other'),
    ]
    
    episode = models.ForeignKey('Episode', on_delete=models.CASCADE, related_name='external_sources')
    source_type = models.CharField(max_length=50, choices=SOURCE_TYPES)
    embed_url = models.URLField(help_text=_("Embed/iframe URL"))
    quality = models.CharField(max_length=20, blank=True)
    language = models.CharField(max_length=10, default='sub', help_text=_("sub or dub"))
    is_working = models.BooleanField(default=True)
    last_checked = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _("External Source")
        verbose_name_plural = _("External Sources")
    
    def __str__(self):
        return f"{self.episode} - {self.get_source_type_display()}"

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

    class Meta:
        indexes = [
            models.Index(fields=['created_at']),
        ]

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

