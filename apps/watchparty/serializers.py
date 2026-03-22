from rest_framework import serializers
from .models import Room
from content.serializers import EpisodeSerializer

import bleach

class RoomSerializer(serializers.ModelSerializer):
    episode = EpisodeSerializer(read_only=True)
    host_username = serializers.CharField(source='host.username', read_only=True)
    
    class Meta:
        model = Room
        fields = ['uuid', 'episode', 'host_username', 'created_at', 'is_active', 'max_participants']

    def validate_max_participants(self, value):
        if value < 0:
            raise serializers.ValidationError("max_participants cannot be negative.")
        return value
