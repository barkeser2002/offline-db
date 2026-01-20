import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]

        if self.user.is_authenticated:
            self.group_name = f"user_{self.user.id}"

            logger.info(f"User {self.user.id} connecting to notifications.")

            # Join user group
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )

            await self.accept()
        else:
            logger.warning("Unauthenticated user tried to connect to notifications.")
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'user') and self.user.is_authenticated:
            # Leave user group
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            logger.info(f"User {self.user.id} disconnected from notifications.")

    async def notification_message(self, event):
        # Send notification to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'title': event['title'],
            'message': event['message'],
            'link': event.get('link', ''),
        }))
