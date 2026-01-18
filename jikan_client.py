import requests
import time
import threading
from typing import Optional, Dict, Any

from config import JIKAN_API_BASE, HTTP_TIMEOUT


class JikanClient:
    """
    Central client for the Jikan API.
    Handles rate limiting, retries, and error management.
    """
    def __init__(self, base_url: str = JIKAN_API_BASE, timeout: int = HTTP_TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout
        self._last_request_time = 0.0
        self._lock = threading.Lock()

    def _rate_limit(self):
        """Jikan API rate limit - max 3 requests per second."""
        with self._lock:
            now = time.time()
            elapsed = now - self._last_request_time
            if elapsed < 0.35:  # 0.33s for ~3 req/s, 0.35s for safety
                time.sleep(0.35 - elapsed)
            self._last_request_time = time.time()

    def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None, max_retries: int = 5) -> Optional[Dict[str, Any]]:
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
        for attempt in range(max_retries):
            try:
                self._rate_limit()
                response = requests.get(url, params=params, timeout=self.timeout)

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 5))
                    wait_time = max(retry_after, 2 ** attempt)
                    print(f"[JikanClient] Rate limit! Waiting {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                return response.json()

            except requests.exceptions.HTTPError as e:
                if e.response is not None and e.response.status_code == 404:
                    print(f"[JikanClient] Resource not found: {url}")
                    return None
                print(f"[JikanClient] HTTP Error ({url}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
            except requests.exceptions.Timeout:
                print(f"[JikanClient] Timeout ({url}), retrying...")
            except Exception as e:
                print(f"[JikanClient] Unexpected error ({url}): {e}")
                break

        print(f"[JikanClient] Max retries exceeded: {url}")
        return None

    def get_anime(self, mal_id: int) -> Optional[Dict[str, Any]]:
        """Gets info for a specific anime."""
        response = self._request(f"anime/{mal_id}")
        return response.get("data") if response else None

    def get_anime_episodes(self, mal_id: int) -> list:
        """Gets all episodes of an anime."""
        all_episodes = []
        page = 1
        while True:
            response = self._request(f"anime/{mal_id}/episodes", params={"page": page})
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

    def search_anime(self, query: str, limit: int = 5) -> list:
        """Searches for anime."""
        response = self._request("anime", params={"q": query, "limit": limit})
        return response.get("data", []) if response else []

    def get_season_anime(self, year: int, season: str, page: int = 1) -> Optional[Dict[str, Any]]:
        """Gets anime for a specific season."""
        return self._request(f"seasons/{year}/{season}", params={"page": page})

    def get_top_anime(self, limit: int = 10) -> list:
        """Gets top anime."""
        response = self._request("top/anime", params={"limit": limit})
        return response.get("data", []) if response else []

    def get_recommendations(self, limit: int = 10) -> list:
        """Gets anime recommendations."""
        response = self._request("recommendations/anime", params={"limit": limit})
        return response.get("data", []) if response else []

    def get_schedule(self, day: Optional[str] = None) -> list:
        """Gets weekly schedule."""
        params = {}
        if day:
            params["filter"] = day

        response = self._request("schedules", params=params)
        return response.get("data", []) if response else []

    def get_anime_relations(self, mal_id: int) -> list:
        """Gets anime relations (sequel, prequel, etc.)."""
        response = self._request(f"anime/{mal_id}/relations")
        return response.get("data", []) if response else []

    def get_anime_recommendations(self, mal_id: int) -> list:
        """Gets similar anime recommendations."""
        response = self._request(f"anime/{mal_id}/recommendations")
        return response.get("data", []) if response else []

# Global Jikan client
jikan = JikanClient()
