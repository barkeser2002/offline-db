import bleach
from rest_framework import serializers
from .models import Notification, Badge, UserBadge, WatchLog, User

class WatchLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WatchLog
        fields = ['episode', 'duration', 'watched_at']
        read_only_fields = ['watched_at']

class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ['id', 'slug', 'name', 'description', 'icon_url']

class UserBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer(read_only=True)

    class Meta:
        model = UserBadge
        fields = ['id', 'badge', 'awarded_at']

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'link', 'is_read', 'created_at']
        read_only_fields = ['id', 'title', 'message', 'link', 'created_at']

import bleach
import re
from django.core.exceptions import ValidationError

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        from django.contrib.auth import get_user_model
        model = get_user_model()
        fields = ['username', 'bio', 'is_public']

    def validate_username(self, value):
        if not re.match(r'^[\w-]+$', value):
            raise serializers.ValidationError("Enter a valid username. This value may contain only letters, numbers, and _/- characters.")
        return value

    def validate_bio(self, value):
        if value:
            return bleach.clean(value, tags=[], strip=True)
        return value

from .models import Follow, UserAnimeList
from content.models import Anime

class FollowSerializer(serializers.ModelSerializer):
    follower_username = serializers.CharField(source='follower.username', read_only=True)
    following_username = serializers.CharField(source='following.username', read_only=True)

    class Meta:
        model = Follow
        fields = ['id', 'follower', 'follower_username', 'following', 'following_username', 'created_at']
        read_only_fields = ['id', 'follower', 'created_at']

class UserAnimeListSerializer(serializers.ModelSerializer):
    anime_title = serializers.CharField(source='anime.title', read_only=True)

    class Meta:
        model = UserAnimeList
        fields = ['id', 'user', 'anime', 'anime_title', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

class ActivitySerializer(serializers.Serializer):
    activity_type = serializers.CharField()
    user = serializers.CharField(source='user.username', read_only=True)
    created_at = serializers.DateTimeField()
    details = serializers.DictField()
