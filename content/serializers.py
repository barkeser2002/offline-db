from rest_framework import serializers
from .models import (
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
    url = serializers.CharField(source='embed_url', read_only=True)
    type = serializers.CharField(source='source_type', read_only=True)
    embed_url = serializers.URLField(write_only=True)

    class Meta:
        model = ExternalSource
        fields = ['id', 'source_name', 'url', 'embed_url', 'quality', 'type']

    def validate_embed_url(self, value):
        if not value.startswith('https://') and not value.startswith('magnet:'):
            raise serializers.ValidationError("URL must start with 'https://' or 'magnet:'.")
        return value

    def validate_url(self, value):
        if not (value.startswith('magnet:') or value.startswith('https://')):
            raise serializers.ValidationError("URL must start with magnet: or https://")
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


class FileUploadValidationMixin:
    """Mixin for validating cover/banner URLs to prevent malicious file uploads (e.g. storage path traversal/XSS)."""
    def validate_image_url(self, value):
        if not value:
            return value
        allowed_exts = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        # if value is a string (e.g. URLField)
        if isinstance(value, str):
            if not any(value.lower().split('?')[0].endswith(ext) for ext in allowed_exts):
                 raise serializers.ValidationError("Invalid image extension. Must be an image file.")
        # if value is an uploaded file
        elif hasattr(value, 'name'):
            import mimetypes
            mime_type, _ = mimetypes.guess_type(value.name)
            allowed_mimes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
            content_type = getattr(value, 'content_type', mime_type)
            if content_type not in allowed_mimes:
                raise serializers.ValidationError(f"Invalid image type. Allowed: {', '.join(allowed_mimes)}")
        return value

    def validate_cover_image(self, value):
        return self.validate_image_url(value)

    def validate_banner_image(self, value):
        return self.validate_image_url(value)

class AnimeListSerializer(FileUploadValidationMixin, serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    
    class Meta:
        model = Anime
        fields = [
            'id', 'mal_id', 'title', 'cover_image', 'score', 
            'type', 'date_aired', 'genres', 'status', 'rating'
        ]
    
    date_aired = serializers.SerializerMethodField()

    def get_date_aired(self, obj) -> str | None:
        if obj.aired_from:
            return obj.aired_from.isoformat()
        return None

class AnimeDetailSerializer(FileUploadValidationMixin, serializers.ModelSerializer):
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

    def get_is_subscribed(self, obj) -> bool:
        request = self.context.get('request')
        if getattr(self, 'swagger_fake_view', False) or not request:
            return False
        user = request.user
        if user and user.is_authenticated:
            return Subscription.objects.filter(user=user, anime=obj).exists()
        return False

class SubscriptionSerializer(serializers.ModelSerializer):
    anime = AnimeListSerializer(read_only=True)
    
    class Meta:
        model = Subscription
        fields = ['id', 'anime', 'created_at']

import mimetypes

class SubtitleSerializer(serializers.ModelSerializer):
    class Meta:
        from .models import Subtitle
        model = Subtitle
        fields = ['id', 'episode', 'lang', 'file', 'created_at']

    def validate_file(self, value):
        allowed_mimes = ['text/plain', 'text/vtt', 'application/x-subrip', 'application/octet-stream']
        mime_type, _ = mimetypes.guess_type(value.name)

        # Check if the file's extension suggests a valid mime type or if its actual content_type is allowed
        content_type = getattr(value, 'content_type', mime_type)
        if content_type and content_type not in allowed_mimes:
            # specifically allow srt/vtt extensions as a fallback
            if not (value.name.endswith('.srt') or value.name.endswith('.vtt')):
                raise serializers.ValidationError(f"Invalid file type. Allowed: vtt, srt")

        # Additionally validate the extension for security
        if not (value.name.endswith('.srt') or value.name.endswith('.vtt') or value.name.endswith('.txt')):
             raise serializers.ValidationError("File must be .srt, .vtt, or .txt")
        return value
