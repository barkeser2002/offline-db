import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels.exceptions import DenyConnection
from django.utils.html import escape
from django.core.cache import cache
from asgiref.sync import sync_to_async
from .models import Room, Participant, Message

logger = logging.getLogger(__name__)

class WatchPartyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_uuid = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'party_{self.room_uuid}'
        self.user = self.scope.get('user')

        # Require authentication for connection
        if not self.user or not self.user.is_authenticated:
            raise DenyConnection()

        # Parse query string for password
        query_string = self.scope.get('query_string', b'').decode('utf-8')
        from urllib.parse import parse_qs
        query_params = parse_qs(query_string)
        password = query_params.get('password', [''])[0]

        # Verify Room Exists and Password
        if not await self.verify_room_access(self.room_uuid, self.user, password):
            raise DenyConnection()

        # Verify Room Capacity
        if not await self.check_room_capacity(self.room_uuid, self.user):
            raise DenyConnection()

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Add/Update Participant
        await self.add_participant(self.room_uuid, self.user)
        await self.broadcast_system_message(f"{self.user.username} joined the party.")
        await self.send_participants_list()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        if self.user and self.user.is_authenticated:
            await self.remove_participant(self.room_uuid, self.user)
            await self.broadcast_system_message(f"{self.user.username} left the party.")
            await self.send_participants_list()

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('type')

        # Require authentication for all interactions
        if not self.user.is_authenticated:
            return

        # Rate Limit Check for chat and emote messages
        if msg_type in ['chat', 'emote']:
            if not await self.check_rate_limit(msg_type):
                # Silently ignore or send error?
                # Sending error might be better but let's just ignore to prevent spam
                return

        if msg_type == 'sync':
            # Video Sync (Host -> Viewers)
            if await self.is_host(self.room_uuid, self.user):
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'video_sync',
                        'timestamp': data.get('timestamp'),
                        'state': data.get('state'), # playing/paused
                        'sender_id': self.user.id
                    }
                )
        elif msg_type == 'chat':
            # Chat Message
            message = data.get('message')

            # Input Validation: Max Length
            if message and len(message) > 500:
                message = message[:500]

            # Sanitize message to prevent XSS
            if message:
                sanitized_message = escape(message)
                await self.save_message(self.room_uuid, self.user, sanitized_message)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': sanitized_message,
                        'username': self.user.username,
                        'is_system': False
                    }
                )
        elif msg_type == 'emote':
            # Emote Rain
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'emote_rain',
                    'emote': data.get('emote')
                }
            )

    # Handlers for Group Messages
    async def video_sync(self, event):
        await self.send(text_data=json.dumps(event))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def emote_rain(self, event):
        await self.send(text_data=json.dumps(event))

    async def participants_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'participants_update',
            'participants': event['participants']
        }))

    # DB Operations
    @database_sync_to_async
    def verify_room_access(self, uuid, user, password):
        try:
            room = Room.objects.get(uuid=uuid)
            if room.password and room.host != user:
                if password != room.password:
                    return False
            return True
        except Room.DoesNotExist:
            return False

    @database_sync_to_async
    def check_room_capacity(self, uuid, user):
        try:
            room = Room.objects.get(uuid=uuid)
            # Host can always join
            if room.host == user:
                return True

            # If max_participants is set, verify active participant count
            if room.max_participants > 0:
                # If user is already an active participant, they can rejoin
                if Participant.objects.filter(room_id=uuid, user=user, is_online=True).exists():
                    return True

                # Otherwise check if there's room
                active_participants = Participant.objects.filter(room_id=uuid, is_online=True).count()
                if active_participants >= room.max_participants:
                    return False

            return True
        except Room.DoesNotExist:
            return False

    @database_sync_to_async
    def is_host(self, uuid, user):
        return Room.objects.filter(uuid=uuid, host=user).exists()

    @database_sync_to_async
    def add_participant(self, uuid, user):
        Participant.objects.update_or_create(
            room_id=uuid, user=user,
            defaults={'is_online': True}
        )

    @database_sync_to_async
    def remove_participant(self, uuid, user):
        Participant.objects.filter(room_id=uuid, user=user).update(is_online=False)

    @database_sync_to_async
    def save_message(self, uuid, user, content):
        Message.objects.create(room_id=uuid, sender=user, content=content)

    async def broadcast_system_message(self, message):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': 'System',
                'is_system': True
            }
        )
    
    async def send_participants_list(self):
        participants = await self.get_participants(self.room_uuid)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'participants_update',
                'participants': participants
            }
        )

    @database_sync_to_async
    def get_participants(self, uuid):
        return list(Participant.objects.filter(room_id=uuid, is_online=True).values('user__username', 'user__id'))

    @sync_to_async
    def check_rate_limit(self, msg_type):
        if not self.user or not self.user.is_authenticated:
            return False # Should not happen as we check auth in receive

        key = f"wp_{msg_type}_limit_user_{self.user.id}"

        # Limit: 10 messages per 10 seconds (slightly more lenient than global chat)
        try:
            count = cache.incr(key)
        except ValueError:
            cache.set(key, 1, timeout=10)
            count = 1

        return count <= 10
