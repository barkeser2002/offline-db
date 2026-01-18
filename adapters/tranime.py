"""
TRAnimeİzle.io API Client
https://www.tranimeizle.io

API Endpoints:
- GET /anime/{slug}-izle -> Anime detay sayfası
- GET /{slug}-{episode}-bolum-izle -> Bölüm izleme sayfası
- POST /api/fansubSources -> Kaynak listesi (JSON: EpisodeId, FansubId)
- POST /api/sourcePlayer/{source_id} -> Video iframe (JSON response)
- GET /harfler/{letter}/sayfa-{page} -> Harfe göre anime listesi
"""

import json
import time
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from urllib.parse import unquote

try:
    from curl_cffi import requests as curl_requests
    HAS_CURL = True
except ImportError:
    import requests as std_requests
    HAS_CURL = False

# ─────────────────────────────────────────────────────────────────────────────
# YAPILANDIRMA
# ─────────────────────────────────────────────────────────────────────────────
BASE_URL = "https://www.tranimeizle.io"
CACHE_DIR = Path.home() / ".turkanime" / "tranime_cache"
CACHE_DURATION = 30 * 60  # 30 dakika
HTTP_TIMEOUT = 15

# Cookie - bot korumasını aşmak için gerekli
# Bu cookie kullanıcının tarayıcısından alınmalı
SESSION_COOKIE = None


def set_session_cookie(cookie_value: str):
    """Session cookie'yi ayarla."""
    global SESSION_COOKIE
    SESSION_COOKIE = unquote(cookie_value) if '%' in cookie_value else cookie_value


def _get_session():
    """HTTP session oluştur."""
    if HAS_CURL:
        session = curl_requests.Session(impersonate="chrome110")
    else:
        session = std_requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
        })
    return session


def _get_cookies() -> dict:
    """Cookie'leri döndür."""
    if SESSION_COOKIE:
        return {'.AitrWeb.Session': SESSION_COOKIE}
    return {}


# ─────────────────────────────────────────────────────────────────────────────
# CACHE YÖNETİMİ
# ─────────────────────────────────────────────────────────────────────────────
def _ensure_cache_dir():
    """Cache dizinini oluştur."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _get_cache(key: str) -> Optional[Any]:
    """Cache'den veri al."""
    cache_file = CACHE_DIR / f"{key}.json"
    if not cache_file.exists():
        return None

    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            cache = json.load(f)

        if time.time() - cache.get("timestamp", 0) > CACHE_DURATION:
            return None

        return cache.get("data")
    except Exception:
        return None


def _save_cache(key: str, data: Any):
    """Cache'e veri kaydet."""
    _ensure_cache_dir()
    cache_file = CACHE_DIR / f"{key}.json"

    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({"timestamp": time.time(), "data": data}, f, ensure_ascii=False)
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# VERİ SINIFLARI
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class TRAnimeVideo:
    """Video kaynağı."""
    source_id: str
    name: str
    fansub: str
    iframe_url: str = ""

    def get_iframe(self) -> str:
        """Video iframe URL'ini al."""
        if self.iframe_url:
            return self.iframe_url

        try:
            session = _get_session()
            resp = session.post(
                f"{BASE_URL}/api/sourcePlayer/{self.source_id}",
                impersonate="chrome110" if HAS_CURL else None,
                cookies=_get_cookies(),
                timeout=HTTP_TIMEOUT
            )
            resp.raise_for_status()
            data = resp.json()

            if 'source' in data:
                match = re.search(r'src="([^"]+)"', data['source'])
                if match:
                    self.iframe_url = match.group(1)
                    return self.iframe_url
        except Exception as e:
            print(f"[TRAnime] Video alınamadı: {e}")

        return ""

    def __repr__(self):
        return f"TRAnimeVideo({self.name}, {self.fansub})"


@dataclass
class TRAnimeEpisode:
    """Bölüm."""
    episode_id: int
    episode_number: int
    slug: str
    title: str
    fansubs: List[Tuple[str, str]] = field(default_factory=list)  # [(fid, name), ...]

    @property
    def url(self) -> str:
        return f"{BASE_URL}/{self.slug}"

    def get_sources(self, fansub_id: str = None) -> List[TRAnimeVideo]:
        """Bölümün video kaynaklarını al."""
        if not fansub_id and self.fansubs:
            fansub_id = self.fansubs[0][0]

        if not fansub_id:
            return []

        try:
            session = _get_session()
            resp = session.post(
                f"{BASE_URL}/api/fansubSources",
                json={"EpisodeId": self.episode_id, "FansubId": int(fansub_id)},
                impersonate="chrome110" if HAS_CURL else None,
                cookies=_get_cookies(),
                timeout=HTTP_TIMEOUT
            )
            resp.raise_for_status()

            # HTML parse
            sources = []
            items = re.findall(
                r'data-id="(\d+)"[^>]*>.*?<p[^>]*class="title"[^>]*>\s*(\S+)',
                resp.text, re.DOTALL
            )

            fansub_name = next((f[1] for f in self.fansubs if f[0] == fansub_id), "Unknown")

            for source_id, name in items:
                sources.append(TRAnimeVideo(
                    source_id=source_id,
                    name=name.strip(),
                    fansub=fansub_name
                ))

            return sources
        except Exception as e:
            print(f"[TRAnime] Kaynaklar alınamadı: {e}")
            return []

    def __repr__(self):
        return f"TRAnimeEpisode({self.episode_number}, {self.title})"


@dataclass
class TRAnimeAnime:
    """Anime."""
    slug: str
    title: str
    poster: str = ""
    total_episodes: int = 0
    _episodes: List[TRAnimeEpisode] = field(default_factory=list, repr=False)

    @property
    def url(self) -> str:
        return f"{BASE_URL}/anime/{self.slug}"

    @property
    def episodes(self) -> List[TRAnimeEpisode]:
        """Bölüm listesini lazy-load et."""
        if not self._episodes:
            self._episodes = get_anime_episodes(self.slug)
        return self._episodes

    def __repr__(self):
        return f"TRAnimeAnime({self.title}, {self.total_episodes} ep)"


# ─────────────────────────────────────────────────────────────────────────────
# API FONKSİYONLARI
# ─────────────────────────────────────────────────────────────────────────────
def get_anime_by_slug(slug: str) -> Optional[TRAnimeAnime]:
    """
    Slug ile anime bilgilerini al.

    Args:
        slug: Anime slug'ı (örn: "naruto-izle")
    """
    # Slug formatını düzelt
    if not slug.endswith('-izle'):
        slug = f"{slug}-izle"

    try:
        session = _get_session()
        resp = session.get(
            f"{BASE_URL}/anime/{slug}",
            impersonate="chrome110" if HAS_CURL else None,
            cookies=_get_cookies(),
            timeout=HTTP_TIMEOUT
        )
        resp.raise_for_status()

        # Bot kontrolü varsa
        if 'Bot Kontrol' in resp.text:
            print("[TRAnime] Bot kontrolü - cookie gerekli")
            return None

        # Başlık
        title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', resp.text)
        title = title_match.group(1).strip() if title_match else slug

        # Poster
        poster_match = re.search(r'<img[^>]*src="([^"]+)"[^>]*class="[^"]*thumbnail', resp.text)
        poster = poster_match.group(1) if poster_match else ""
        if poster and not poster.startswith('http'):
            poster = BASE_URL + poster

        # Bölüm sayısı
        episodes = re.findall(r'href="(/[^"]*-\d+-bolum-izle)"', resp.text)

        return TRAnimeAnime(
            slug=slug.replace('-izle', ''),
            title=title.replace(' İzle', '').strip(),
            poster=poster,
            total_episodes=len(episodes)
        )
    except Exception as e:
        print(f"[TRAnime] Anime alınamadı ({slug}): {e}")
        return None


def get_anime_episodes(anime_slug: str) -> List[TRAnimeEpisode]:
    """
    Anime bölümlerini al.

    Args:
        anime_slug: Anime slug'ı
    """
    if not anime_slug.endswith('-izle'):
        anime_slug = f"{anime_slug}-izle"

    try:
        session = _get_session()
        resp = session.get(
            f"{BASE_URL}/anime/{anime_slug}",
            impersonate="chrome110" if HAS_CURL else None,
            cookies=_get_cookies(),
            timeout=HTTP_TIMEOUT
        )
        resp.raise_for_status()

        if 'Bot Kontrol' in resp.text:
            print("[TRAnime] Bot kontrolü - cookie gerekli")
            return []

        # Bölüm linklerini bul
        episode_links = re.findall(r'href="(/([^"]*)-(\d+)-bolum-izle)"', resp.text)

        episodes = []
        seen = set()

        for full_path, slug_part, ep_num in episode_links:
            if full_path in seen:
                continue
            seen.add(full_path)

            ep_slug = full_path.lstrip('/')
            episodes.append(TRAnimeEpisode(
                episode_id=0,  # Sonradan doldurulacak
                episode_number=int(ep_num),
                slug=ep_slug,
                title=f"{ep_num}. Bölüm"
            ))

        # Bölüm numarasına göre sırala
        episodes.sort(key=lambda x: x.episode_number)

        return episodes
    except Exception as e:
        print(f"[TRAnime] Bölümler alınamadı ({anime_slug}): {e}")
        return []


def get_episode_details(episode_slug: str) -> Optional[TRAnimeEpisode]:
    """
    Bölüm detaylarını al (episode_id ve fansub listesi).

    Args:
        episode_slug: Bölüm slug'ı (örn: "naruto-4-bolum-izle")
    """
    try:
        session = _get_session()
        resp = session.get(
            f"{BASE_URL}/{episode_slug}",
            impersonate="chrome110" if HAS_CURL else None,
            cookies=_get_cookies(),
            timeout=HTTP_TIMEOUT
        )
        resp.raise_for_status()

        if 'Bot Kontrol' in resp.text:
            print("[TRAnime] Bot kontrolü - cookie gerekli")
            return None

        # Episode ID
        ep_id_match = re.search(r'id="EpisodeId"[^>]*value="(\d+)"', resp.text)
        if not ep_id_match:
            return None

        episode_id = int(ep_id_match.group(1))

        # Bölüm numarası
        ep_num_match = re.search(r'-(\d+)-bolum-izle', episode_slug)
        episode_number = int(ep_num_match.group(1)) if ep_num_match else 0

        # Fansub listesi
        fansubs = re.findall(r'data-fid="(\d+)"[^>]*data-fad="([^"]+)"', resp.text)

        return TRAnimeEpisode(
            episode_id=episode_id,
            episode_number=episode_number,
            slug=episode_slug,
            title=f"{episode_number}. Bölüm",
            fansubs=fansubs
        )
    except Exception as e:
        print(f"[TRAnime] Bölüm detayları alınamadı ({episode_slug}): {e}")
        return None


def search_by_letter(letter: str, page: int = 1) -> List[Tuple[str, str]]:
    """
    Harfe göre anime ara.

    Args:
        letter: Harf (a-z veya #)
        page: Sayfa numarası

    Returns:
        [(slug, title), ...]
    """
    try:
        session = _get_session()
        resp = session.get(
            f"{BASE_URL}/harfler/{letter.lower()}/sayfa-{page}",
            impersonate="chrome110" if HAS_CURL else None,
            cookies=_get_cookies(),
            timeout=HTTP_TIMEOUT
        )
        resp.raise_for_status()

        if 'Bot Kontrol' in resp.text:
            print("[TRAnime] Bot kontrolü - cookie gerekli")
            return []

        # Anime linklerini bul
        results = []
        matches = re.findall(r'href="/anime/([^"]+)"[^>]*>.*?<h\d[^>]*>([^<]+)</h\d>', resp.text, re.DOTALL)

        for slug, title in matches:
            clean_slug = slug.replace('-izle', '')
            clean_title = title.strip()
            if clean_title and clean_slug not in [r[0] for r in results]:
                results.append((clean_slug, clean_title))

        return results
    except Exception as e:
        print(f"[TRAnime] Arama hatası: {e}")
        return []


def search_anime(query: str, limit: int = 10) -> List[Tuple[str, str]]:
    """
    Anime ara (harfler sayfasından).

    Not: Site arama özelliği bot korumalı olduğundan,
    harfler sayfasından filtreleme yapılır.

    Args:
        query: Arama sorgusu
        limit: Maksimum sonuç sayısı

    Returns:
        [(slug, title), ...]
    """
    query_lower = query.lower().strip()

    if not query_lower:
        return []

    # İlk harfi al
    first_letter = query_lower[0]
    if not first_letter.isalpha():
        first_letter = '#'

    # Cache kontrol
    cache_key = f"search_{first_letter}"
    cached = _get_cache(cache_key)

    if cached is None:
        # Tüm sayfaları çek (max 5 sayfa)
        all_results = []
        for page in range(1, 6):
            results = search_by_letter(first_letter, page)
            if not results:
                break
            all_results.extend(results)
            time.sleep(0.3)  # Rate limit

        _save_cache(cache_key, all_results)
        cached = all_results

    # Filtrele
    matches = []
    for slug, title in cached:
        if query_lower in title.lower() or query_lower in slug.lower():
            matches.append((slug, title))
            if len(matches) >= limit:
                break

    return matches


def search_tranime(query: str, limit: int = 10) -> List[Tuple[str, str]]:
    """
    Anime ara - adapter uyumluluğu için alias.
    """
    return search_anime(query, limit)


# ─────────────────────────────────────────────────────────────────────────────
# TEST
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== TRAnimeİzle.io API Test ===\n")

    # Cookie ayarla (test için)
    # set_session_cookie("YOUR_COOKIE_HERE")

    # Anime bilgisi
    print("[1] Anime bilgisi...")
    anime = get_anime_by_slug("naruto")
    if anime:
        print(f"    {anime.title} - {anime.total_episodes} bölüm")
        print(f"    URL: {anime.url}")

    # Bölümler
    print("\n[2] Bölümler...")
    if anime:
        episodes = anime.episodes
        print(f"    Toplam: {len(episodes)} bölüm")
        if episodes:
            print(f"    İlk: {episodes[0]}")

    # Bölüm detayı
    print("\n[3] Bölüm detayı...")
    if anime and anime.episodes:
        ep = get_episode_details(anime.episodes[0].slug)
        if ep:
            print(f"    Episode ID: {ep.episode_id}")
            print(f"    Fansubs: {ep.fansubs}")

            # Kaynaklar
            sources = ep.get_sources()
            print(f"    Kaynaklar: {len(sources)}")
            for s in sources[:3]:
                print(f"      - {s.name}")

    # Arama
    print("\n[4] Arama...")
    results = search_anime("one piece", limit=5)
    print(f"    Sonuç: {len(results)}")
    for slug, title in results:
        print(f"      - {title}")

    print("\n=== Test Tamamlandı ===")
