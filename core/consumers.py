import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache
from asgiref.sync import sync_to_async
from .models import ChatMessage

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Update user count
        count = await self.update_user_count(1)
        await self.broadcast_user_count(count)

        # Send last 50 messages
        last_messages = await self.get_last_messages()
        for msg in last_messages:
            await self.send(text_data=json.dumps({
                'type': 'chat_message',
                'message': msg['message'],
                'username': msg['username'],
                'created_at': str(msg['created_at'])
            }))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        # Update user count
        count = await self.update_user_count(-1)
        await self.broadcast_user_count(count)

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        user = self.scope.get("user")
        if user and user.is_authenticated:
            username = user.username
        else:
            username = text_data_json.get('username', 'Anonymous')

        # Save to DB
        await self.save_message(username, message)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username,
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        username = event.get('username', 'Anonymous')

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message,
            'username': username
        }))

    async def user_count(self, event):
        count = event['count']
        await self.send(text_data=json.dumps({
            'type': 'user_count',
            'count': count
        }))

    async def broadcast_user_count(self, count):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_count',
                'count': count
            }
        )

    @sync_to_async
    def update_user_count(self, change):
        key = f"chat_count_{self.room_name}"
        # We use a primitive locking by atomic incr/decr
        # However, initial value might be tricky. cache.incr raises ValueError if key missing.
        try:
            # Atomic increment/decrement
            return cache.incr(key, change)
        except ValueError:
            # Key does not exist, set it.
            # If we are incrementing, start at 1. If decrementing (shouldn't happen first), 0.
            new_value = 1 if change > 0 else 0
            cache.set(key, new_value, timeout=86400) # 24h timeout
            return new_value

    @database_sync_to_async
    def save_message(self, username, message):
        user = self.scope.get("user")
        if user and not user.is_authenticated:
             user = None

        ChatMessage.objects.create(
            room_name=self.room_name,
            username=username,
            message=message,
            user=user
        )

    @database_sync_to_async
    def get_last_messages(self):
        messages = ChatMessage.objects.filter(room_name=self.room_name).order_by('-created_at')[:50]
        return [{'username': m.username, 'message': m.message, 'created_at': m.created_at} for m in reversed(list(messages))]
