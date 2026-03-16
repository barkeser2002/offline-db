from rest_framework import serializers
from .models import Room
from content.serializers import EpisodeSerializer

class RoomSerializer(serializers.ModelSerializer):
    episode = EpisodeSerializer(read_only=True)
    host_username = serializers.CharField(source='host.username', read_only=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    is_private = serializers.SerializerMethodField()
    
    class Meta:
        model = Room
        fields = ['uuid', 'episode', 'host_username', 'created_at', 'is_active', 'max_participants', 'password', 'is_private']

    def get_is_private(self, obj) -> bool:
        return bool(obj.password)
