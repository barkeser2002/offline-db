import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache
from .models import Room, Participant, Message

logger = logging.getLogger(__name__)

class WatchPartyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_uuid = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'party_{self.room_uuid}'
        self.user = self.scope.get('user')

        # Verify Room Exists
        if not await self.room_exists(self.room_uuid):
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        if self.user.is_authenticated:
            # Add/Update Participant
            await self.add_participant(self.room_uuid, self.user)
            await self.broadcast_system_message(f"{self.user.username} joined the party.")
            await self.send_participants_list()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        if self.user.is_authenticated:
            await self.remove_participant(self.room_uuid, self.user)
            await self.broadcast_system_message(f"{self.user.username} left the party.")
            await self.send_participants_list()

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('type')

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
            await self.save_message(self.room_uuid, self.user, message)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
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
    def room_exists(self, uuid):
        return Room.objects.filter(uuid=uuid).exists()

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
