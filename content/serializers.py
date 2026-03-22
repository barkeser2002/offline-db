from rest_framework import serializers
from .models import (
    Subtitle,
    Anime, Episode, VideoFile, Season, Character, AnimeCharacter,
    Genre, ExternalSource, Subscription, FansubGroup
)

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name', 'slug']

class CharacterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Character
        fields = ['id', 'mal_id', 'name', 'image_url', 'about']

class AnimeCharacterSerializer(serializers.ModelSerializer):
    character = CharacterSerializer(read_only=True)
    
    class Meta:
        model = AnimeCharacter
        fields = ['id', 'character', 'role', 'voice_actor_name', 'voice_actor_language']

class FansubGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = FansubGroup
        fields = ['id', 'name', 'website']

class VideoFileSerializer(serializers.ModelSerializer):
    file_url = serializers.CharField(source='hls_path', read_only=True)
    fansub_group = FansubGroupSerializer(read_only=True)
    
    class Meta:
        model = VideoFile
        fields = [
            'id', 'file_url', 'quality', 'is_hardcoded',
            'fansub_group', 'created_at'
            # Security: Never expose encryption_key here. It is served securely via KeyServeView.
        ]

class ExternalSourceSerializer(serializers.ModelSerializer):
    source_name = serializers.CharField(source='source_type', read_only=True)
    url = serializers.CharField(source='embed_url')
    type = serializers.CharField(source='source_type', read_only=True)

    class Meta:
        model = ExternalSource
        fields = ['id', 'source_name', 'url', 'quality', 'type']

    def validate_url(self, value):
        if value and not (value.startswith('magnet:') or value.startswith('https://')):
            raise serializers.ValidationError("URL must start with 'https://' or 'magnet:'")
        return value

class EpisodeSerializer(serializers.ModelSerializer):
    aired_date = serializers.DateTimeField(source='created_at', read_only=True)
    cover_image = serializers.URLField(source='thumbnail', read_only=True)
    video_files = VideoFileSerializer(many=True, read_only=True)
    external_sources = ExternalSourceSerializer(many=True, read_only=True)
    
    class Meta:
        model = Episode
        fields = [
            'id', 'title', 'number', 'cover_image',
            'aired_date', 'video_files', 'external_sources'
        ]

class SeasonSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='title', read_only=True)
    episodes = EpisodeSerializer(many=True, read_only=True)
    
    class Meta:
        model = Season
        fields = ['id', 'number', 'name', 'episodes']

class AnimeListSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    
    class Meta:
        model = Anime
        fields = [
            'id', 'mal_id', 'title', 'cover_image', 'score', 
            'type', 'date_aired', 'genres', 'status', 'rating'
        ]
    
    date_aired = serializers.SerializerMethodField()

    def get_date_aired(self, obj):
        return obj.aired_from

class AnimeDetailSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    characters = AnimeCharacterSerializer(source='anime_characters', many=True, read_only=True)
    seasons = SeasonSerializer(many=True, read_only=True)
    is_subscribed = serializers.SerializerMethodField()
    
    class Meta:
        model = Anime
        fields = [
            'id', 'mal_id', 'title', 'japanese_title', 'english_title',
            'synopsis', 'cover_image', 'banner_image', 'score', 'rank',
            'popularity', 'members', 'studio', 'source', 'status',
            'aired_from', 'aired_to', 'total_episodes', 'duration',
            'rating', 'genres', 'characters', 'seasons', 'is_subscribed'
        ]

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user and user.is_authenticated:
            return Subscription.objects.filter(user=user, anime=obj).exists()
        return False

    def validate_cover_image(self, value):
        # Allow URL or file upload. If file, validate mime.
        if hasattr(value, 'file'):
            validate_mime_type(value.file, ['image/jpeg', 'image/png', 'image/webp', 'image/gif'])
        return value

    def validate_banner_image(self, value):
        if hasattr(value, 'file'):
            validate_mime_type(value.file, ['image/jpeg', 'image/png', 'image/webp', 'image/gif'])
        return value

class SubscriptionSerializer(serializers.ModelSerializer):
    anime = AnimeListSerializer(read_only=True)
    
    class Meta:
        model = Subscription
        fields = ['id', 'anime', 'created_at']


import magic
from rest_framework import serializers

def validate_mime_type(file, allowed_mimes):
    if hasattr(file, 'temporary_file_path'):
        mime = magic.from_file(file.temporary_file_path(), mime=True)
    else:
        # File might be InMemoryUploadedFile, read chunk
        mime = magic.from_buffer(file.read(2048), mime=True)
        file.seek(0)

    if mime not in allowed_mimes:
        raise serializers.ValidationError(f"Unsupported file type: {mime}")

class ImageUploadSerializer(serializers.Serializer):
    cover_image = serializers.ImageField(required=False)
    banner_image = serializers.ImageField(required=False)

    def validate_cover_image(self, value):
        if value:
            validate_mime_type(value, ['image/jpeg', 'image/png', 'image/webp', 'image/gif'])
        return value

    def validate_banner_image(self, value):
        if value:
            validate_mime_type(value, ['image/jpeg', 'image/png', 'image/webp', 'image/gif'])
        return value

from django.core.validators import FileExtensionValidator

class SubtitleSerializer(serializers.ModelSerializer):
    file = serializers.FileField()

    class Meta:
        model = Subtitle
        fields = ['id', 'episode', 'fansub_group', 'lang', 'file', 'created_at']

    def validate_file(self, value):
        if value:
            # Also check extension since some text files can have the same MIME type
            ext = value.name.split('.')[-1].lower()
            if ext not in ['vtt', 'srt', 'ass']:
                raise serializers.ValidationError("File extension must be vtt, srt, or ass")
            validate_mime_type(value, ['text/vtt', 'text/plain', 'application/x-subrip'])
        return value
