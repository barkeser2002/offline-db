import json
import asyncio
import traceback
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache
from django.core.exceptions import ValidationError
from asgiref.sync import sync_to_async
from core.models import ChatMessage
from .models import WatchParty

class WatchPartyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.room_name = self.scope['url_route']['kwargs']['room_name']

            # Security: Validate if the room exists before accepting connection
            if not await self.room_exists():
                await self.close()
                return

            self.room_group_name = 'chat_%s' % self.room_name

            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            await self.accept()

            # Update user count
            count = await self.update_user_count(1)
            await self.broadcast_user_count(count)

            # Broadcast join message
            user = self.scope.get("user")
            if user and user.is_authenticated:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': f"{user.username} joined the party.",
                        'username': 'System',
                        'is_system': True,
                    }
                )

            # Send last 50 messages
            last_messages = await self.get_last_messages()
            for msg in last_messages:
                await self.send(text_data=json.dumps({
                    'type': 'chat_message',
                    'message': msg['message'],
                    'username': msg['username'],
                    'created_at': str(msg['created_at'])
                }))

        except Exception:
            traceback.print_exc()
            raise

    async def disconnect(self, close_code):
        # If connection was rejected in connect(), room_group_name won't be set
        if not hasattr(self, 'room_group_name'):
            return

        # Update user count
        count = await self.update_user_count(-1)
        await self.broadcast_user_count(count)

        user = self.scope.get("user")
        if user and user.is_authenticated:
             await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': f"{user.username} left the party.",
                    'username': 'System',
                    'is_system': True,
                }
            )

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        try:
            if text_data is None:
                return

            try:
                data = json.loads(text_data)
            except json.JSONDecodeError:
                return

            msg_type = data.get('type')

            if msg_type == 'video_control':
                await self.handle_video_control(data)
            elif msg_type == 'typing':
                await self.handle_typing(data)
            elif 'message' in data:
                # Chat message
                user = self.scope.get('user')
                username = user.username if user and user.is_authenticated else "Anonymous"
                message = data['message']

                # Save to DB
                msg_obj = await self.save_message(username, message)

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message,
                        'username': username,
                        'created_at': str(msg_obj.created_at),
                    }
                )

        except Exception:
            traceback.print_exc()
            raise

    async def handle_typing(self, data):
        """
        Broadcast typing status.
        """
        user = self.scope.get('user')
        if user and user.is_authenticated:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_typing',
                    'username': user.username,
                    'is_typing': data.get('is_typing', False)
                }
            )

    async def chat_typing(self, event):
        """
        Send typing status to WebSocket.
        """
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'username': event['username'],
            'is_typing': event['is_typing']
        }))

    async def handle_video_control(self, data):
        """
        Broadcast video control events if the sender is the host.
        """
        if await self.is_host():
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'video_control_message',
                    'action': data.get('action'),
                    'timestamp': data.get('timestamp'),
                    'sender_id': self.scope['user'].id
                }
            )

    async def video_control_message(self, event):
        """
        Send video control event to WebSocket.
        """
        await self.send(text_data=json.dumps({
            'type': 'video_control',
            'action': event['action'],
            'timestamp': event['timestamp'],
            'sender_id': event['sender_id']
        }))

    async def chat_message(self, event):
        """
        Send chat message to WebSocket.
        """
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'username': event['username'],
            'is_system': event.get('is_system', False),
            'created_at': event.get('created_at'),
        }))

    @database_sync_to_async
    def room_exists(self):
        """
        Check if the Watch Party room exists in the database.
        """
        if not self.room_name.startswith('party_'):
            return False

        try:
            uuid_str = self.room_name.split('party_')[1]
            return WatchParty.objects.filter(uuid=uuid_str).exists()
        except (IndexError, ValueError, ValidationError):
            return False

    @database_sync_to_async
    def is_host(self):
        """
        Check if the connected user is the host of the watch party.
        """
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            return False

        # room_name is expected to be "party_{uuid}"
        try:
            if self.room_name.startswith('party_'):
                uuid_str = self.room_name.split('party_')[1]
                party = WatchParty.objects.get(uuid=uuid_str)
                return party.host == user
        except (WatchParty.DoesNotExist, IndexError, ValueError):
            pass

        return False

    @database_sync_to_async
    def save_message(self, username, message):
        user = self.scope.get("user")
        if user and not user.is_authenticated:
             user = None

        return ChatMessage.objects.create(
            room_name=self.room_name,
            username=username,
            message=message,
            user=user
        )

    @database_sync_to_async
    def get_last_messages(self):
        messages = ChatMessage.objects.filter(room_name=self.room_name).order_by('-created_at')[:50]
        return [{'username': m.username, 'message': m.message, 'created_at': m.created_at} for m in reversed(list(messages))]

    @sync_to_async
    def update_user_count(self, change):
        key = f"watch_party_count_{self.room_name}"
        try:
            count = cache.incr(key, change)
        except ValueError:
            count = 1 if change > 0 else 0
            cache.set(key, count, timeout=86400)

        return count

    @database_sync_to_async
    def update_max_participants(self, count):
        if self.room_name.startswith('party_'):
            try:
                uuid_str = self.room_name.split('party_')[1]
                party = WatchParty.objects.get(uuid=uuid_str)
                if count > party.max_participants:
                    party.max_participants = count
                    party.save(update_fields=['max_participants'])
            except (WatchParty.DoesNotExist, IndexError, ValueError):
                pass

    async def broadcast_user_count(self, count):
        # Update DB for max participants asynchronously
        asyncio.create_task(self.update_max_participants(count))

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_count',
                'count': count
            }
        )

    async def user_count(self, event):
        count = event['count']
        await self.send(text_data=json.dumps({
            'type': 'user_count',
            'count': count
        }))
