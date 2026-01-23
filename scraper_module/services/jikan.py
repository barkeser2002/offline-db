import time
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from django.conf import settings
from django.core.cache import cache
from curl_cffi.requests import AsyncSession, RequestsError

logger = logging.getLogger(__name__)

JIKAN_API_BASE = getattr(settings, 'JIKAN_API_BASE', 'https://api.jikan.moe/v4')
HTTP_TIMEOUT = getattr(settings, 'HTTP_TIMEOUT', 30)

class JikanClient:
    """
    Central client for the Jikan API (Async).
    Handles rate limiting, retries, and error management.
    
    Extended with:
    - Character fetching
    - Data parsing for Django models
    - Model sync functionality
    """

    CACHE_TTL = 3600  # 1 hour cache

    def __init__(self, base_url: str = JIKAN_API_BASE, timeout: int = HTTP_TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout
        self._last_request_time = 0.0
        self._lock = None

    async def _get_lock(self):
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def _rate_limit(self):
        """Jikan API rate limit - max 3 requests per second."""
        lock = await self._get_lock()
        async with lock:
            now = time.time()
            elapsed = now - self._last_request_time
            if elapsed < 0.35:  # 0.33s for ~3 req/s, 0.35s for safety
                await asyncio.sleep(0.35 - elapsed)
            self._last_request_time = time.time()

    async def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = 5,
    ) -> Optional[Dict[str, Any]]:
        """
        Sends a safe request to the Jikan API.

        Args:
            endpoint: API endpoint (e.g. "anime/21")
            params: Request parameters
            max_retries: Maximum number of retries

        Returns:
            JSON response or None on error
        """
        url = f"{self.base_url}/{endpoint}"

        async with AsyncSession(timeout=self.timeout) as session:
            for attempt in range(max_retries):
                try:
                    await self._rate_limit()
                    response = await session.get(url, params=params)

                    if response.status_code == 429:
                        retry_after = int(response.headers.get("Retry-After", 5))
                        wait_time = max(retry_after, 2**attempt)
                        logger.warning(
                            f"[JikanClient] Rate limit! Waiting {wait_time}s... (attempt {attempt + 1}/{max_retries})"
                        )
                        await asyncio.sleep(wait_time)
                        continue

                    if response.status_code == 404:
                        logger.info(f"[JikanClient] Resource not found: {url}")
                        return None

                    response.raise_for_status()
                    return response.json()

                except RequestsError as e:
                    logger.error(f"[JikanClient] Request Error ({url}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2**attempt)
                except Exception as e:
                    logger.error(f"[JikanClient] Unexpected error ({url}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2**attempt)
                    else:
                        break

        logger.error(f"[JikanClient] Max retries exceeded: {url}")
        return None

    async def get_anime(self, mal_id: int) -> Optional[Dict[str, Any]]:
        """Gets full info for a specific anime."""
        # Check cache first
        cache_key = f"jikan:anime:{mal_id}"
        cached = cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for anime {mal_id}")
            return cached

        response = await self._request(f"anime/{mal_id}/full")
        data = response.get("data") if response else None
        
        if data:
            cache.set(cache_key, data, self.CACHE_TTL)
        
        return data

    async def get_anime_episodes(self, mal_id: int) -> list:
        """Gets all episodes of an anime."""
        all_episodes = []
        page = 1
        while True:
            response = await self._request(f"anime/{mal_id}/episodes", params={"page": page})
            if not response or "data" not in response:
                break

            episodes = response.get("data", [])
            if episodes:
                all_episodes.extend(episodes)

            pagination = response.get("pagination", {})
            if not pagination.get("has_next_page", False):
                break
            page += 1

        return all_episodes

    async def get_anime_characters(self, mal_id: int) -> List[Dict[str, Any]]:
        """Gets characters for an anime with voice actors."""
        cache_key = f"jikan:characters:{mal_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        response = await self._request(f"anime/{mal_id}/characters")
        data = response.get("data", []) if response else []
        
        if data:
            cache.set(cache_key, data, self.CACHE_TTL)
        
        return data

    async def search_anime(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for anime by title."""
        cache_key = f"jikan:search:{query}:{limit}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        response = await self._request("anime", params={
            'q': query,
            'limit': min(limit, 25),
            'sfw': 'true'
        })
        data = response.get("data", []) if response else []
        
        if data:
            cache.set(cache_key, data, 300)  # 5 min cache for search
        
        return data

    # ==================== Data Parsing Methods ====================

    def parse_anime_data(self, jikan_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Jikan API response to match Django Anime model fields.
        
        Returns a dict ready for Anime model update.
        """
        # Extract studio name (first studio in list)
        studios = jikan_data.get('studios', [])
        studio_name = studios[0]['name'] if studios else ''

        # Parse airing dates
        aired = jikan_data.get('aired', {})
        aired_from = None
        aired_to = None

        if aired.get('from'):
            try:
                aired_from = datetime.fromisoformat(aired['from'].replace('Z', '+00:00')).date()
            except (ValueError, TypeError):
                pass

        if aired.get('to'):
            try:
                aired_to = datetime.fromisoformat(aired['to'].replace('Z', '+00:00')).date()
            except (ValueError, TypeError):
                pass

        return {
            'mal_id': jikan_data.get('mal_id'),
            'title': jikan_data.get('title', ''),
            'japanese_title': jikan_data.get('title_japanese', '') or '',
            'english_title': jikan_data.get('title_english', '') or '',
            'synopsis': jikan_data.get('synopsis', '') or '',
            'cover_image': jikan_data.get('images', {}).get('jpg', {}).get('large_image_url', ''),
            'banner_image': jikan_data.get('images', {}).get('jpg', {}).get('large_image_url', ''),
            'score': Decimal(str(jikan_data.get('score', 0))) if jikan_data.get('score') else None,
            'rank': jikan_data.get('rank'),
            'popularity': jikan_data.get('popularity'),
            'members': jikan_data.get('members'),
            'studio': studio_name,
            'source': jikan_data.get('source', '') or '',
            'status': jikan_data.get('status', '') or '',
            'type': jikan_data.get('type', 'TV') or 'TV',
            'aired_from': aired_from,
            'aired_to': aired_to,
            'total_episodes': jikan_data.get('episodes'),
            'duration': jikan_data.get('duration', '') or '',
            'rating': jikan_data.get('rating', '') or '',
        }

    def parse_character_data(self, jikan_char: Dict[str, Any]) -> Dict[str, Any]:
        """Parse character data from Jikan API response."""
        character = jikan_char.get('character', {})
        voice_actors = jikan_char.get('voice_actors', [])

        # Get Japanese voice actor if available
        jp_va = next((va for va in voice_actors if va.get('language') == 'Japanese'), None)

        va_image = ''
        if jp_va and jp_va.get('person', {}).get('images', {}).get('jpg'):
            va_image = jp_va['person']['images']['jpg'].get('image_url', '')

        return {
            'character': {
                'mal_id': character.get('mal_id'),
                'name': character.get('name', ''),
                'image_url': character.get('images', {}).get('jpg', {}).get('image_url', ''),
            },
            'role': jikan_char.get('role', 'Supporting'),
            'voice_actor_name': jp_va['person']['name'] if jp_va else '',
            'voice_actor_language': 'Japanese' if jp_va else '',
            'voice_actor_image': va_image,
        }

    # ==================== Model Sync Methods ====================

    async def sync_anime_to_db(self, anime_instance, mal_id: Optional[int] = None):
        """
        Sync anime instance with Jikan API data.
        
        Args:
            anime_instance: Anime model instance to update
            mal_id: MAL ID to fetch (uses anime_instance.mal_id if not provided)
        """
        from content.models import Anime, Character, AnimeCharacter, Genre

        mal_id = mal_id or anime_instance.mal_id
        if not mal_id:
            raise ValueError("MAL ID is required for sync")

        # Fetch anime data
        jikan_data = await self.get_anime(mal_id)
        if not jikan_data:
            raise ValueError(f"Anime with MAL ID {mal_id} not found on Jikan")

        # Update anime fields
        parsed_data = self.parse_anime_data(jikan_data)
        for field, value in parsed_data.items():
            if value is not None:
                setattr(anime_instance, field, value)

        anime_instance.save()
        logger.info(f"Synced anime '{anime_instance.title}' with MAL data")

        # Sync genres
        for genre_data in jikan_data.get('genres', []):
            genre, _ = Genre.objects.get_or_create(
                name=genre_data['name'],
                defaults={'slug': genre_data['name'].lower().replace(' ', '-')}
            )
            anime_instance.genres.add(genre)

        # Sync characters (limit to 15 main characters)
        characters_data = await self.get_anime_characters(mal_id)
        for char_data in characters_data[:15]:
            parsed_char = self.parse_character_data(char_data)

            character, _ = Character.objects.update_or_create(
                mal_id=parsed_char['character']['mal_id'],
                defaults={
                    'name': parsed_char['character']['name'],
                    'image_url': parsed_char['character']['image_url'],
                }
            )

            AnimeCharacter.objects.update_or_create(
                anime=anime_instance,
                character=character,
                defaults={
                    'role': parsed_char['role'],
                    'voice_actor_name': parsed_char['voice_actor_name'],
                    'voice_actor_language': parsed_char['voice_actor_language'],
                    'voice_actor_image': parsed_char['voice_actor_image'],
                }
            )

        logger.info(f"Synced {len(characters_data[:15])} characters for {anime_instance.title}")
        return anime_instance


# Global Jikan client
jikan = JikanClient()

