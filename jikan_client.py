import requests
import time
import threading
from typing import Optional, Dict, Any

from config import JIKAN_API_BASE, HTTP_TIMEOUT


class JikanClient:
    """
    Jikan API için merkezi bir istemci.
    Rate limiting, yeniden deneme ve hata yönetimini yönetir.
    """
    def __init__(self, base_url: str = JIKAN_API_BASE, timeout: int = HTTP_TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout
        self._last_request_time = 0.0
        self._lock = threading.Lock()

    def _rate_limit(self):
        """Jikan API rate limit - saniyede max 3 istek."""
        with self._lock:
            now = time.time()
            elapsed = now - self._last_request_time
            if elapsed < 0.35:  # ~3 istek/saniye için 0.33s, güvenlik için 0.35s
                time.sleep(0.35 - elapsed)
            self._last_request_time = time.time()

    def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None, max_retries: int = 5) -> Optional[Dict[str, Any]]:
        """
        Jikan API'ye güvenli bir istek gönderir.

        Args:
            endpoint: API endpoint (örn. "anime/21")
            params: İstek parametreleri
            max_retries: Maksimum yeniden deneme sayısı

        Returns:
            JSON yanıtı veya hata durumunda None
        """
        url = f"{self.base_url}/{endpoint}"
        for attempt in range(max_retries):
            try:
                self._rate_limit()
                response = requests.get(url, params=params, timeout=self.timeout)

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 5))
                    wait_time = max(retry_after, 2 ** attempt)
                    print(f"[JikanClient] Rate limit! {wait_time}s bekleniyor... (deneme {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                return response.json()

            except requests.exceptions.HTTPError as e:
                if e.response is not None and e.response.status_code == 404:
                    print(f"[JikanClient] Kaynak bulunamadı: {url}")
                    return None
                print(f"[JikanClient] HTTP Hatası ({url}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
            except requests.exceptions.Timeout:
                print(f"[JikanClient] Timeout ({url}), tekrar deneniyor...")
            except Exception as e:
                print(f"[JikanClient] Beklenmedik hata ({url}): {e}")
                break

        print(f"[JikanClient] Maksimum deneme aşıldı: {url}")
        return None

    def get_anime(self, mal_id: int) -> Optional[Dict[str, Any]]:
        """Belirli bir anime'nin bilgilerini alır."""
        response = self._request(f"anime/{mal_id}")
        return response.get("data") if response else None

    def get_anime_episodes(self, mal_id: int) -> list:
        """Bir anime'nin tüm bölümlerini alır."""
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
        """Anime arar."""
        response = self._request("anime", params={"q": query, "limit": limit})
        return response.get("data", []) if response else []

    def get_season_anime(self, year: int, season: str, page: int = 1) -> Optional[Dict[str, Any]]:
        """Belirli bir sezonun anime'lerini alır."""
        return self._request(f"seasons/{year}/{season}", params={"page": page})

    def get_top_anime(self, limit: int = 10) -> list:
        """En popüler anime'leri alır."""
        response = self._request("top/anime", params={"limit": limit})
        return response.get("data", []) if response else []

    def get_recommendations(self, limit: int = 10) -> list:
        """Anime önerilerini alır."""
        response = self._request("recommendations/anime", params={"limit": limit})
        return response.get("data", []) if response else []

# Global Jikan istemcisi
jikan = JikanClient()
