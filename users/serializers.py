import bleach
from rest_framework import serializers
from .models import Notification, Badge, UserBadge, WatchLog, User

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['bio']

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

import bleach
import re
from django.core.exceptions import ValidationError

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        from django.contrib.auth import get_user_model
        model = get_user_model()
        fields = ['username', 'bio']

    def validate_username(self, value):
        if not re.match(r'^[\w-]+$', value):
            raise serializers.ValidationError("Enter a valid username. This value may contain only letters, numbers, and _/- characters.")
        return value

    def validate_bio(self, value):
        if value:
            return bleach.clean(value, tags=[], strip=True)
        return value
