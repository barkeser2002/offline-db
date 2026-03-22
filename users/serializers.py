from django.utils.html import strip_tags
from rest_framework import serializers
from .models import Notification, Badge, UserBadge, WatchLog, User

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'bio', 'is_premium', 'date_joined']
        read_only_fields = ['id', 'username', 'email', 'is_premium', 'date_joined']

    def validate_bio(self, value):
        if value:
            return strip_tags(value).strip()
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
