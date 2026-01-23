import json
import asyncio
import traceback
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache
from django.core.exceptions import ValidationError
from asgiref.sync import sync_to_async
from core.models import ChatMessage
from users.services import check_chat_badges
# from .models import WatchParty # Removed

# WatchPartyConsumer removed. Use apps.watchparty.consumers instead.
