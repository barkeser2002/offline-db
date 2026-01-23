import time
import asyncio
from typing import Optional, Dict, Any
from django.conf import settings
from curl_cffi.requests import AsyncSession, RequestsError

JIKAN_API_BASE = getattr(settings, 'JIKAN_API_BASE', 'https://api.jikan.moe/v4')
HTTP_TIMEOUT = getattr(settings, 'HTTP_TIMEOUT', 30)

class JikanClient:
    """
    Central client for the Jikan API (Async).
    Handles rate limiting, retries, and error management.
    """

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
                        print(
                            f"[JikanClient] Rate limit! Waiting {wait_time}s... (attempt {attempt + 1}/{max_retries})"
                        )
                        await asyncio.sleep(wait_time)
                        continue

                    if response.status_code == 404:
                        print(f"[JikanClient] Resource not found: {url}")
                        return None

                    response.raise_for_status()
                    return response.json()

                except RequestsError as e:
                    print(f"[JikanClient] Request Error ({url}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2**attempt)
                except Exception as e:
                    print(f"[JikanClient] Unexpected error ({url}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2**attempt)
                    else:
                        break

        print(f"[JikanClient] Max retries exceeded: {url}")
        return None

    async def get_anime(self, mal_id: int) -> Optional[Dict[str, Any]]:
        """Gets info for a specific anime."""
        response = await self._request(f"anime/{mal_id}")
        return response.get("data") if response else None

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

# Global Jikan client
jikan = JikanClient()
