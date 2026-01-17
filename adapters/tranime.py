"""
TRAnimeİzle.io API Client
https://www.tranimeizle.io
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


@dataclass  
class TRAnimeEpisode:
    """Bölüm."""
    episode_id: int
    episode_number: int
    slug: str
    title: str
    fansubs: List[Tuple[str, str]] = field(default_factory=list)
    
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
                cookies=_get_cookies(),
                timeout=HTTP_TIMEOUT
            )
            resp.raise_for_status()
            
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


# ─────────────────────────────────────────────────────────────────────────────
# API FONKSİYONLARI
# ─────────────────────────────────────────────────────────────────────────────
def get_anime_by_slug(slug: str) -> Optional[TRAnimeAnime]:
    """Slug ile anime bilgilerini al."""
    if not slug.endswith('-izle'):
        slug = f"{slug}-izle"
    
    try:
        session = _get_session()
        resp = session.get(
            f"{BASE_URL}/anime/{slug}",
            cookies=_get_cookies(),
            timeout=HTTP_TIMEOUT
        )
        resp.raise_for_status()
        
        if 'Bot Kontrol' in resp.text:
            return None
        
        title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', resp.text)
        title = title_match.group(1).strip() if title_match else slug
        
        poster_match = re.search(r'<img[^>]*src="([^"]+)"[^>]*class="[^"]*thumbnail', resp.text)
        poster = poster_match.group(1) if poster_match else ""
        if poster and not poster.startswith('http'):
            poster = BASE_URL + poster
        
        episodes = re.findall(r'href="(/[^"]*-\d+-bolum-izle)"', resp.text)
        
        return TRAnimeAnime(
            slug=slug.replace('-izle', ''),
            title=title.replace(' İzle', '').strip(),
            poster=poster,
            total_episodes=len(episodes)
        )
    except Exception:
        return None


def get_anime_episodes(anime_slug: str) -> List[TRAnimeEpisode]:
    """Anime bölümlerini al."""
    if not anime_slug.endswith('-izle'):
        anime_slug = f"{anime_slug}-izle"
    
    try:
        session = _get_session()
        resp = session.get(
            f"{BASE_URL}/anime/{anime_slug}",
            cookies=_get_cookies(),
            timeout=HTTP_TIMEOUT
        )
        resp.raise_for_status()
        
        if 'Bot Kontrol' in resp.text:
            return []
        
        episode_links = re.findall(r'href="(/([^"]*)-(\d+)-bolum-izle)"', resp.text)
        
        episodes = []
        seen = set()
        
        for full_path, slug_part, ep_num in episode_links:
            if full_path in seen:
                continue
            seen.add(full_path)
            
            ep_slug = full_path.lstrip('/')
            episodes.append(TRAnimeEpisode(
                episode_id=0,
                episode_number=int(ep_num),
                slug=ep_slug,
                title=f"{ep_num}. Bölüm"
            ))
        
        episodes.sort(key=lambda x: x.episode_number)
        return episodes
    except Exception:
        return []


def get_episode_details(episode_slug: str) -> Optional[TRAnimeEpisode]:
    """Bölüm detaylarını al."""
    try:
        session = _get_session()
        resp = session.get(
            f"{BASE_URL}/{episode_slug}",
            cookies=_get_cookies(),
            timeout=HTTP_TIMEOUT
        )
        resp.raise_for_status()
        
        if 'Bot Kontrol' in resp.text:
            return None
        
        ep_id_match = re.search(r'id="EpisodeId"[^>]*value="(\d+)"', resp.text)
        if not ep_id_match:
            return None
        
        episode_id = int(ep_id_match.group(1))
        
        ep_num_match = re.search(r'-(\d+)-bolum-izle', episode_slug)
        episode_number = int(ep_num_match.group(1)) if ep_num_match else 0
        
        fansubs = re.findall(r'data-fid="(\d+)"[^>]*data-fad="([^"]+)"', resp.text)
        
        return TRAnimeEpisode(
            episode_id=episode_id,
            episode_number=episode_number,
            slug=episode_slug,
            title=f"{episode_number}. Bölüm",
            fansubs=fansubs
        )
    except Exception:
        return None


def search_anime(query: str, limit: int = 10) -> List[Tuple[str, str]]:
    """Anime ara."""
    query_lower = query.lower().strip()
    if not query_lower:
        return []
    
    # Try direct search first
    try:
        session = _get_session()
        search_url = f"{BASE_URL}/arama?q={query}"
        resp = session.get(search_url, timeout=HTTP_TIMEOUT)
        if resp.status_code == 200 and 'Bot Kontrol' not in resp.text:
            results = []
            pattern = r'href="/anime/([^"]+)"[^>]*>([^<]+)</a>'
            matches = re.findall(pattern, resp.text)
            for slug, title in matches:
                clean_slug = slug.replace('-izle', '').strip()
                clean_title = title.strip()
                if clean_title and clean_slug and clean_slug not in [r[0] for r in results]:
                    results.append((clean_slug, clean_title))
                    if len(results) >= limit: break
            if results: return results
    except Exception:
        pass

    return []


def search_tranime(query: str, limit: int = 10) -> List[Tuple[str, str]]:
    return search_anime(query, limit)

def get_episode_streams(episode_slug: str) -> List[Dict[str, str]]:
    """Get streams for an episode slug (local project compatibility)."""
    details = get_episode_details(episode_slug)
    streams = []
    if details:
        for f_id, f_name in details.fansubs:
            sources = details.get_sources(f_id)
            for s in sources:
                iframe = s.get_iframe()
                if iframe:
                    streams.append({
                        "url": iframe,
                        "quality": "default",
                        "label": s.name,
                        "fansub": f_name
                    })
    return streams
