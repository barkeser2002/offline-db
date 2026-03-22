import bleach
from rest_framework import serializers
from .models import Notification, Badge, UserBadge, WatchLog, User

import re
import bleach
from django.contrib.auth import get_user_model

User = get_user_model()

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'bio']

    def validate_username(self, value):
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise serializers.ValidationError("Username can only contain alphanumeric characters, underscores, and hyphens.")
        return value

    def validate_bio(self, value):
        if value:
            return bleach.clean(value, tags=[], strip=True)
        return value

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

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['bio', 'username']

    def validate_username(self, value):
        import re
        if not re.match(r'^[\w-]+$', value):
            raise serializers.ValidationError("Enter a valid username. This value may contain only letters, numbers, and _/- characters.")
        return value

    def validate_bio(self, value):
        if value:
            return bleach.clean(value, tags=[], strip=True)
        return value
