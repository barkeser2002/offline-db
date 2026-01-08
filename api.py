#!/usr/bin/env python3
"""
Anime Offline DB - Web API & Player

Kullanım:
    python api.py

Endpoints:
    GET /                           - Ana sayfa (sezon listesi)
    GET /player?mal_id=X            - Anime oynatıcı
    GET /player?mal_id=X&ep=Y       - Belirli bölüm
    GET /api/anime/<mal_id>         - Anime bilgileri (JSON)
    GET /api/episodes/<mal_id>      - Bölüm listesi (JSON)
    GET /api/stream/<mal_id>/<ep>   - Video stream URL (JSON)
    GET /api/seasons                - Tüm sezonlar (JSON)
    GET /api/seasons/<year>/<season>- Sezon anime listesi (JSON)
    POST /api/sync/season           - Sezon senkronizasyonu
"""

import json
import os
import re
import subprocess
import time
import requests
from flask import Flask, request, jsonify, render_template_string, redirect, url_for
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, cast, Optional, List, Tuple
from functools import partial
from threading import Thread
import threading

# Local Modules
import main
from config import (
    JIKAN_API_BASE, JIKAN_RATE_LIMIT, API_HOST, API_PORT, MAX_WORKERS, ADAPTERS
)
import db
from adapters import anizle, animecix, animely, tranime, turkanime

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL PARALEL İŞLEM YÖNETİCİSİ
# ─────────────────────────────────────────────────────────────────────────────
# Büyük worker havuzu - 50-200 arası paralel işlem
PARALLEL_WORKERS = min(MAX_WORKERS, 200)  # Config'den al, max 200
VIDEO_WORKERS = min(MAX_WORKERS, 100)     # Video işlemleri için

# Global executor havuzları (reusable)
_main_executor: Optional[ThreadPoolExecutor] = None
_video_executor: Optional[ThreadPoolExecutor] = None

def get_main_executor() -> ThreadPoolExecutor:
    """Ana paralel işlem havuzu."""
    global _main_executor
    if _main_executor is None:
        _main_executor = ThreadPoolExecutor(max_workers=PARALLEL_WORKERS)
    return _main_executor

def get_video_executor() -> ThreadPoolExecutor:
    """Video işlemleri için paralel havuz."""
    global _video_executor
    if _video_executor is None:
        _video_executor = ThreadPoolExecutor(max_workers=VIDEO_WORKERS)
    return _video_executor

app = Flask(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# LIVE FETCH HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def ensure_anime_data(mal_id):
    """Anime verisi eksikse veya yoksa tamamla."""
    anime = db.get_anime_by_mal_id(mal_id)
    if not anime:
        print(f"[Info] Anime {mal_id} DB'de yok, indiriliyor...")
        main.update_anime_by_mal_id(mal_id)
        return db.get_anime_by_mal_id(mal_id)
    return anime

def ensure_episode_videos(mal_id, episode_num, anime_db_id, force_refresh: bool = False):
    """
    Bölüm videoları yoksa canlı çek (Tüm kaynaklardan).
    
    Args:
        mal_id: MAL ID
        episode_num: Bölüm numarası
        anime_db_id: Anime DB ID
        force_refresh: True ise mevcut videoları temizleyip yeniden çek
    """
    
    # Force refresh ise mevcut videoları temizle
    if force_refresh:
        conn = db.get_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE vl FROM video_links vl
                JOIN episodes e ON vl.episode_id = e.id
                WHERE e.anime_id = %s AND e.episode_number = %s
            """, (anime_db_id, episode_num))
            conn.commit()
            cursor.close()
            conn.close()
            print(f"[Live] Force refresh - eski videolar silindi")
    
    # 1. Kaynakları DB'den al
    conn = db.get_connection()
    if not conn: return
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT asrc.source_slug, asrc.source_id as src_db_id, asrc.source_anime_id, s.name as source_name, s.id as source_tbl_id
        FROM anime_sources asrc 
        JOIN sources s ON asrc.source_id = s.id 
        WHERE asrc.anime_id = %s AND s.is_active = 1
    """, (anime_db_id,))
    sources = cursor.fetchall()
    
    # Anime başlıklarını al (adaptör araması için)
    cursor.execute("""SELECT title, title_english, title_japanese FROM animes WHERE id = %s""", (anime_db_id,))
    anime_row = cursor.fetchone()
    cursor.close()
    conn.close()
    
    anime_title = anime_row.get('title') if anime_row else None
    anime_title_en = anime_row.get('title_english') if anime_row else None
    anime_title_jp = anime_row.get('title_japanese') if anime_row else None

    # Kaynak yoksa adaptörlerde ara ve ekle
    if not sources:
        print(f"[Live] Kaynak yok, adaptörlerde aranıyor...")
        adapter_matches = main.search_in_adapters(anime_title, anime_title_en, anime_title_jp)
        
        if adapter_matches:
            conn = db.get_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                for adapter_name, (source_anime_id, source_slug, source_title) in adapter_matches.items():
                    source_id = db.get_source_id(adapter_name)
                    if source_id:
                        db.insert_or_update_anime_source(anime_db_id, source_id, source_anime_id, source_slug, source_title)
                        print(f"[Live] {adapter_name} kaynağı eklendi: {source_title}")
                cursor.close()
                conn.close()
                
                # Kaynakları tekrar çek
                conn = db.get_connection()
                if conn:
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("""
                        SELECT asrc.source_slug, asrc.source_id as src_db_id, asrc.source_anime_id, s.name as source_name, s.id as source_tbl_id
                        FROM anime_sources asrc 
                        JOIN sources s ON asrc.source_id = s.id 
                        WHERE asrc.anime_id = %s AND s.is_active = 1
                    """, (anime_db_id,))
                    sources = cursor.fetchall()
                    cursor.close()
                    conn.close()
    
    if not sources:
        print(f"[Live] Hiçbir kaynakta bulunamadı")
        return

    # Helper: Tek bir kaynağı işle
    def fetch_source(src):
        name = src['source_name']
        slug = src['source_slug']
        s_id = src['source_tbl_id']
        ext_id = src['source_anime_id']
        found_videos = []
        
        try:
            if name == 'anizle':
                # Anizle Direct Prediction
                ep_slug = f"{slug}-{episode_num}-bolum"
                streams = anizle.get_episode_streams(ep_slug)
                for st in streams:
                     found_videos.append({
                        "url": st.get('url') or st.get('videoUrl'),
                        "label": st.get('label', 'Anizle'),
                        "fansub": "Anizle"
                     })

            elif name == 'animecix':
                # AnimeCiX List Check
                anime = animecix.CixAnime(id=ext_id, title="")
                target_url = None
                # Hızlı erişim için başlık/sıra kontrolü
                for i, ep in enumerate(anime.episodes):
                    if i + 1 == episode_num:
                        target_url = ep.url
                        break
                    match = re.search(r'(\d+)\.?\s*[Bb]ölüm', ep.title)
                    if match and int(match.group(1)) == episode_num:
                        target_url = ep.url
                        break
                
                if target_url:
                    streams = animecix._video_streams(target_url)
                    for st in streams:
                        found_videos.append({
                            "url": st.get("url"),
                            "label": st.get("label", "default"),
                            "fansub": "AnimeCiX"
                        })

            elif name == 'animely':
                 # Animely - DEVRE DIŞI
                 pass

            elif name == 'tranime':
                # TRAnime Direct Prediction
                ep_slug = f"{slug}-{episode_num}-bolum-izle"
                ep_details = tranime.get_episode_details(ep_slug)
                if ep_details:
                     sources_tr = ep_details.get_sources()
                     for s in sources_tr:
                         iframe = s.get_iframe()
                         if iframe:
                             found_videos.append({
                                 "url": iframe,
                                 "label": s.name,
                                 "fansub": s.fansub
                             })

            elif name == 'turkanime':
                # TurkAnime - CF bypass ile
                ep_slug = f"{slug}-{episode_num}-bolum"
                streams = turkanime.get_episode_streams(ep_slug)
                for st in streams:
                    if st.url:
                        found_videos.append({
                            "url": st.url,
                            "label": st.quality,
                            "fansub": st.fansub
                        })

        except Exception as e:
            print(f"[Live] {name} hatası: {e}")
            
        return s_id, found_videos

    # Paralel Çalıştır - Yüksek hız için büyük worker havuzu
    total_found = 0
    results = []
    
    with ThreadPoolExecutor(max_workers=min(len(sources) * 2, VIDEO_WORKERS)) as executor:
        futures = [executor.submit(fetch_source, src) for src in sources]
        for future in as_completed(futures):
            try:
                res = future.result(timeout=30)
                if res:
                    results.append(res)
            except Exception as e:
                print(f"[Live] Worker hatası: {e}")

    # Veritabanına kaydet
    if results:
        conn = db.get_connection()
        if not conn: return
        
        # Bölüm ID'sini bul veya oluştur (Dictionary Cursor Kullan)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM episodes WHERE anime_id = %s AND episode_number = %s", (anime_db_id, episode_num))
        ep_row = cursor.fetchone()
        
        if not ep_row:
             cursor.execute("INSERT INTO episodes (anime_id, episode_number, title) VALUES (%s, %s, %s)",
                            (anime_db_id, episode_num, f"{episode_num}. Bölüm"))
             last_id = cursor.lastrowid
             if last_id is None:
                 print("[DB Error] Failed to insert episode")
                 return
             ep_id = int(last_id)
        else:
             ep_id = int(cast(Dict[str, Any], ep_row)['id'])
        
        cursor.close()
        
        # Linkleri ekle
        cursor = conn.cursor()
        for source_tbl_id, videos in results:
            for v in videos:
                if not v['url']: continue
                
                label = str(v['label'] or "default")
                fansub = str(v['fansub'] or "Unknown")
                
                # Anizle label parse fix
                if fansub == "Anizle" and " - " in label:
                     parts = label.split(" - ", 1)
                     fansub = parts[0]
                     quality = parts[1]
                else:
                    quality = label

                try:
                    cursor.execute("""
                        INSERT INTO video_links (episode_id, source_id, fansub, quality, video_url, iframe_url)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            video_url = VALUES(video_url),
                            updated_at = CURRENT_TIMESTAMP
                    """, (ep_id, int(source_tbl_id), fansub, quality, str(v['url']), ""))
                    total_found += 1
                except Exception as e:
                    print(f"[DB Error] {e}")

        conn.commit()
        conn.close()
        print(f"[Live] Toplam {total_found} yeni video eklendi.")


# ─────────────────────────────────────────────────────────────────────────────
# YT-DLP İLE EN İYİ KALİTE BULMA & LİNK DOĞRULAMA
# ─────────────────────────────────────────────────────────────────────────────

def check_video_link_alive(video_url: str, timeout: int = 15) -> Tuple[bool, Optional[dict]]:
    """
    Video linkinin aktif olup olmadığını kontrol et.
    Returns: (is_alive: bool, stream_info: dict or None)
    
    yt-dlp.exe ile linki kontrol eder:
    - Çalışıyorsa: (True, {url, quality, type})
    - Çalışmıyorsa: (False, None)
    """
    try:
        # HLS linkleri için hızlı HEAD check
        if ".m3u8" in video_url:
            try:
                resp = requests.head(video_url, timeout=5, allow_redirects=True)
                if resp.status_code == 200:
                    return True, {"url": video_url, "quality": "HLS", "ext": "m3u8", "type": "hls"}
                else:
                    return False, None
            except Exception:
                # HEAD başarısız - yt-dlp ile dene
                pass
        
        # yt-dlp ile detaylı kontrol
        result = subprocess.run(
            ["yt-dlp.exe", "-j", "--no-warnings", "--no-download", video_url],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if result.returncode != 0:
            # Hata mesajını kontrol et
            stderr = result.stderr.lower()
            if "video unavailable" in stderr or "404" in stderr or "removed" in stderr or "private" in stderr:
                return False, None
            
            # HLS/m3u8 linkleri için fallback
            if ".m3u8" in video_url:
                return True, {"url": video_url, "quality": "HLS", "ext": "m3u8", "type": "hls"}
            
            return False, None
        
        data = json.loads(result.stdout)
        
        # URL varsa çalışıyor demek
        if data.get("url") or data.get("formats"):
            formats = data.get("formats", [])
            
            if not formats:
                url = data.get("url", video_url)
                return True, {"url": url, "quality": "default", "ext": "mp4", "type": "direct"}
            
            # En iyi formatı seç
            best_format = None
            best_height = 0
            
            for fmt in formats:
                height = fmt.get("height") or 0
                vcodec = fmt.get("vcodec", "none")
                
                if vcodec == "none":
                    continue
                
                if height > best_height:
                    best_height = height
                    best_format = fmt
            
            if best_format:
                return True, {
                    "url": best_format.get("url", video_url),
                    "quality": f"{best_height}p" if best_height else "best",
                    "ext": best_format.get("ext", "mp4"),
                    "type": "direct"
                }
            
            # Fallback
            if "requested_formats" in data:
                video_fmt = data["requested_formats"][0]
                return True, {
                    "url": video_fmt.get("url", video_url),
                    "quality": f"{video_fmt.get('height', 0)}p",
                    "ext": video_fmt.get("ext", "mp4"),
                    "type": "direct"
                }
            
            return True, {"url": data.get("url", video_url), "quality": "default", "ext": "mp4", "type": "direct"}
        
        return False, None
        
    except subprocess.TimeoutExpired:
        # Timeout - linki şüpheli say ama silme
        if ".m3u8" in video_url:
            return True, {"url": video_url, "quality": "HLS", "ext": "m3u8", "type": "hls"}
        return True, {"url": video_url, "quality": "unknown", "ext": "mp4", "type": "direct"}
    except json.JSONDecodeError:
        # JSON parse hatası - muhtemelen çalışmıyor
        return False, None
    except FileNotFoundError:
        # yt-dlp.exe bulunamadı - yt-dlp dene
        try:
            result = subprocess.run(
                ["yt-dlp", "-j", "--no-warnings", "--no-download", video_url],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if data.get("url") or data.get("formats"):
                    return True, {"url": data.get("url", video_url), "quality": "default", "ext": "mp4", "type": "direct"}
            return False, None
        except Exception:
            return False, None
    except Exception as e:
        print(f"[LinkCheck] Hata: {e}")
        return False, None


def remove_dead_video_link(video_link_id: int):
    """Ölü video linkini veritabanından kaldır (is_active = FALSE)."""
    try:
        conn = db.get_connection()
        if not conn:
            return
        
        cursor = conn.cursor()
        # Soft delete - tamamen silmek yerine pasif yap
        cursor.execute("""
            UPDATE video_links 
            SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP 
            WHERE id = %s
        """, (video_link_id,))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"[LinkCheck] Video link {video_link_id} pasif yapıldı (ölü link)")
    except Exception as e:
        print(f"[LinkCheck] DB hatası: {e}")


def get_best_stream_url(video_url: str) -> Optional[dict]:
    """
    yt-dlp ile video URL'sinden en iyi kaliteyi bul.
    Returns: {"url": direct_url, "quality": "1080p", "ext": "mp4"}
    """
    try:
        # yt-dlp ile format listesini al
        result = subprocess.run(
            ["yt-dlp", "-j", "--no-warnings", video_url],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            # HLS/m3u8 linkleri direkt kullanılabilir
            if ".m3u8" in video_url:
                return {"url": video_url, "quality": "HLS", "ext": "m3u8", "type": "hls"}
            return None
        
        data = json.loads(result.stdout)
        
        # En iyi formatı seç
        formats = data.get("formats", [])
        if not formats:
            url = data.get("url", video_url)
            return {"url": url, "quality": "default", "ext": "mp4", "type": "direct"}
        
        # Video + audio olan formatları filtrele
        best_format = None
        best_height = 0
        
        for fmt in formats:
            height = fmt.get("height") or 0
            vcodec = fmt.get("vcodec", "none")
            acodec = fmt.get("acodec", "none")
            
            # Video codec'i olmalı
            if vcodec == "none":
                continue
            
            if height > best_height:
                best_height = height
                best_format = fmt
        
        if best_format:
            return {
                "url": best_format.get("url", video_url),
                "quality": f"{best_height}p" if best_height else "best",
                "ext": best_format.get("ext", "mp4"),
                "type": "direct"
            }
        
        # Fallback: requested_formats veya url
        if "requested_formats" in data:
            video_fmt = data["requested_formats"][0]
            return {
                "url": video_fmt.get("url", video_url),
                "quality": f"{video_fmt.get('height', 0)}p",
                "ext": video_fmt.get("ext", "mp4"),
                "type": "direct"
            }
        
        return {"url": data.get("url", video_url), "quality": "default", "ext": "mp4", "type": "direct"}
        
    except subprocess.TimeoutExpired:
        # Timeout - direkt URL döndür
        if ".m3u8" in video_url:
            return {"url": video_url, "quality": "HLS", "ext": "m3u8", "type": "hls"}
        return {"url": video_url, "quality": "unknown", "ext": "mp4", "type": "direct"}
    except Exception as e:
        print(f"[yt-dlp] Hata: {e}")
        if ".m3u8" in video_url:
            return {"url": video_url, "quality": "HLS", "ext": "m3u8", "type": "hls"}
        return None


# ─────────────────────────────────────────────────────────────────────────────
# JIKAN API - SEZON ANIME LİSTESİ (RATE LIMIT: 3/saniye, 60/dakika)
# ─────────────────────────────────────────────────────────────────────────────

# Rate limiter için global değişkenler
_jikan_last_request_time = 0.0
_jikan_rate_lock = threading.Lock()

def _apply_jikan_rate_limit():
    """Jikan API rate limit - saniyede max 3 istek."""
    global _jikan_last_request_time
    with _jikan_rate_lock:
        now = time.time()
        elapsed = now - _jikan_last_request_time
        if elapsed < 0.35:  # ~3 istek/saniye için güvenli aralık
            time.sleep(0.35 - elapsed)
        _jikan_last_request_time = time.time()


def fetch_season_anime(year: int, season: str, page: int = 1, max_retries: int = 5) -> Optional[dict]:
    """
    Jikan API'den sezon anime listesini çek.
    429 (Too Many Requests) hatası aldığında bekleyip tekrar dener.
    
    season: winter, spring, summer, fall
    """
    for attempt in range(max_retries):
        try:
            _apply_jikan_rate_limit()  # Rate limit uygula
            
            url = f"{JIKAN_API_BASE}/seasons/{year}/{season}"
            params = {"page": page, "limit": 25}
            response = requests.get(url, params=params, timeout=30)
            
            # 429 Too Many Requests - bekle ve tekrar dene
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 5))
                wait_time = max(retry_after, 2 ** attempt + 1)
                print(f"[Jikan] Rate limit! {wait_time}s bekleniyor... (deneme {attempt+1}/{max_retries})")
                time.sleep(wait_time)
                continue
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 429:
                wait_time = 2 ** attempt + 2
                print(f"[Jikan] Rate limit! {wait_time}s bekleniyor... (deneme {attempt+1}/{max_retries})")
                time.sleep(wait_time)
                continue
            print(f"[Jikan] Sezon çekme hatası ({year}/{season}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return None
        except requests.exceptions.Timeout:
            print(f"[Jikan] Timeout ({year}/{season} s.{page}), tekrar deneniyor...")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            return None
        except Exception as e:
            print(f"[Jikan] Sezon çekme hatası ({year}/{season}): {e}")
            return None
    
    print(f"[Jikan] Max deneme aşıldı ({year}/{season} s.{page})")
    return None


def fetch_all_season_anime(year: int, season: str, save_to_db: bool = True) -> list:
    """
    Bir sezonun tüm anime'lerini çek (tüm sayfalar).
    
    Args:
        year: Yıl (ör: 2026)
        season: Sezon (winter, spring, summer, fall)
        save_to_db: True ise eksik anime'leri DB'ye kaydet
    
    Returns:
        Anime listesi
    """
    all_anime = []
    page = 1
    
    # Mevcut DB'deki MAL ID'ler
    existing_ids = set(db.get_all_mal_ids()) if save_to_db else set()
    saved_count = 0
    
    while True:
        print(f"[Jikan] {year}/{season} sayfa {page} çekiliyor...")
        result = fetch_season_anime(year, season, page)
        
        if not result:
            break
            
        data = result.get("data", [])
        if not data:
            break
        
        # Her anime için temel bilgileri DB'ye kaydet (eksik olanları)
        if save_to_db:
            for anime_data in data:
                mal_id = anime_data.get("mal_id")
                if mal_id and mal_id not in existing_ids:
                    try:
                        # Anime bilgilerini parse et
                        parsed = _parse_jikan_anime_basic(anime_data)
                        if parsed:
                            anime_db_id = db.insert_or_update_anime(parsed)
                            if anime_db_id:
                                existing_ids.add(mal_id)
                                saved_count += 1
                    except Exception as e:
                        print(f"[Jikan] DB kayıt hatası ({mal_id}): {e}")
        
        all_anime.extend(data)
        
        pagination = result.get("pagination", {})
        if not pagination.get("has_next_page", False):
            break
        
        page += 1
        time.sleep(JIKAN_RATE_LIMIT)  # Rate limit
    
    if save_to_db and saved_count > 0:
        print(f"[Jikan] {saved_count} yeni anime DB'ye kaydedildi")
    
    return all_anime


def _parse_jikan_anime_basic(jikan_data: dict) -> Optional[dict]:
    """Jikan sezon verisinden temel anime bilgilerini parse et."""
    if not jikan_data:
        return None
    
    mal_id = jikan_data.get("mal_id")
    if not mal_id:
        return None
    
    # Yayın tarihleri
    aired = jikan_data.get("aired", {}) or {}
    aired_from = aired.get("from")
    aired_to = aired.get("to")
    
    if aired_from:
        aired_from = aired_from[:10]  # YYYY-MM-DD
    if aired_to:
        aired_to = aired_to[:10]
    
    # Cover
    images = jikan_data.get("images", {}) or {}
    jpg_images = images.get("jpg", {}) or {}
    cover_url = jpg_images.get("large_image_url") or jpg_images.get("image_url", "")
    
    # Trailer
    trailer_data = jikan_data.get("trailer", {}) or {}
    trailer_url = trailer_data.get("embed_url", "")
    
    return {
        "mal_id": mal_id,
        "title": jikan_data.get("title", ""),
        "title_english": jikan_data.get("title_english"),
        "title_japanese": jikan_data.get("title_japanese"),
        "type": jikan_data.get("type"),
        "source": jikan_data.get("source"),
        "episodes": jikan_data.get("episodes") or 0,
        "status": jikan_data.get("status"),
        "airing": jikan_data.get("airing", False),
        "aired_from": aired_from,
        "aired_to": aired_to,
        "duration": jikan_data.get("duration"),
        "rating": jikan_data.get("rating"),
        "score": jikan_data.get("score"),
        "scored_by": jikan_data.get("scored_by"),
        "rank": jikan_data.get("rank"),
        "popularity": jikan_data.get("popularity"),
        "members": jikan_data.get("members"),
        "favorites": jikan_data.get("favorites"),
        "synopsis": jikan_data.get("synopsis"),
        "background": jikan_data.get("background"),
        "season": jikan_data.get("season"),
        "year": jikan_data.get("year"),
        "cover_url": cover_url,
        "trailer_url": trailer_url,
    }


def get_available_seasons() -> list:
    """Mevcut sezonları listele (2000'den bugüne)."""
    import datetime
    current_year = datetime.datetime.now().year
    seasons = ["winter", "spring", "summer", "fall"]
    
    result = []
    for year in range(current_year, 1999, -1):
        for season in seasons:
            result.append({"year": year, "season": season})
    
    return result


# ─────────────────────────────────────────────────────────────────────────────
# HTML TEMPLATES
# ─────────────────────────────────────────────────────────────────────────────

HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Anime Offline DB</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', sans-serif; 
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        h1 { text-align: center; margin-bottom: 30px; color: #e94560; }
        
        .search-box {
            display: flex;
            justify-content: center;
            margin-bottom: 30px;
            gap: 10px;
        }
        .search-box input {
            padding: 12px 20px;
            width: 300px;
            border: none;
            border-radius: 25px;
            background: rgba(255,255,255,0.1);
            color: #fff;
            font-size: 16px;
        }
        .search-box input::placeholder { color: rgba(255,255,255,0.5); }
        .search-box button {
            padding: 12px 30px;
            border: none;
            border-radius: 25px;
            background: #e94560;
            color: #fff;
            cursor: pointer;
            font-size: 16px;
            transition: transform 0.2s;
        }
        .search-box button:hover { transform: scale(1.05); }
        
        .seasons {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
        }
        .season-card {
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .season-card:hover {
            background: rgba(233, 69, 96, 0.2);
            transform: translateY(-5px);
        }
        .season-card h3 { color: #e94560; margin-bottom: 5px; }
        .season-card p { color: rgba(255,255,255,0.7); font-size: 14px; }
        
        .stats {
            display: flex;
            justify-content: center;
            gap: 40px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        .stat {
            text-align: center;
            padding: 20px;
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            min-width: 150px;
        }
        .stat h2 { color: #e94560; font-size: 32px; }
        .stat p { color: rgba(255,255,255,0.7); }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 Anime Offline DB</h1>
        
        <div class="stats">
            <div class="stat">
                <h2>{{ stats.anime_count }}</h2>
                <p>Anime</p>
            </div>
            <div class="stat">
                <h2>{{ stats.episode_count }}</h2>
                <p>Bölüm</p>
            </div>
            <div class="stat">
                <h2>{{ stats.video_count }}</h2>
                <p>Video Link</p>
            </div>
        </div>
        
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="MAL ID veya Anime adı...">
            <button onclick="searchAnime()">Ara</button>
        </div>
        
        <h2 style="margin-bottom: 20px;">📅 Sezonlar</h2>
        <div class="seasons">
            {% for s in seasons[:40] %}
            <div class="season-card" onclick="location.href='/season/{{ s.year }}/{{ s.season }}'">
                <h3>{{ s.year }}</h3>
                <p>{{ s.season|capitalize }}</p>
            </div>
            {% endfor %}
        </div>
    </div>
    
    <script>
        function searchAnime() {
            const val = document.getElementById('searchInput').value.trim();
            if (!val) return;
            
            if (/^\\d+$/.test(val)) {
                location.href = '/player?mal_id=' + val;
            } else {
                location.href = '/search?q=' + encodeURIComponent(val);
            }
        }
        
        document.getElementById('searchInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') searchAnime();
        });
    </script>
</body>
</html>
"""

PLAYER_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ anime.title }} - Anime Player</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', sans-serif; 
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%);
            min-height: 100vh;
            color: #fff;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        
        .header {
            display: flex;
            align-items: center;
            gap: 20px;
            margin-bottom: 20px;
        }
        .header img {
            width: 120px;
            height: 170px;
            object-fit: cover;
            border-radius: 10px;
        }
        .header-info h1 { color: #e94560; margin-bottom: 10px; font-size: 1.5em; }
        .header-info p { color: rgba(255,255,255,0.7); margin-bottom: 5px; }
        .back-btn {
            display: inline-block;
            padding: 8px 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
            color: #fff;
            text-decoration: none;
            margin-bottom: 10px;
        }
        .back-btn:hover { background: rgba(255,255,255,0.2); }
        
        .player-container {
            background: #000;
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 20px;
            position: relative;
        }
        #videoPlayer {
            width: 100%;
            max-height: 75vh;
            display: block;
        }
        
        .player-controls {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: linear-gradient(transparent, rgba(0,0,0,0.9));
            padding: 20px;
            opacity: 0;
            transition: opacity 0.3s;
        }
        .player-container:hover .player-controls { opacity: 1; }
        
        .progress-bar {
            width: 100%;
            height: 5px;
            background: rgba(255,255,255,0.3);
            border-radius: 3px;
            cursor: pointer;
            margin-bottom: 10px;
        }
        .progress-bar .progress {
            height: 100%;
            background: #e94560;
            border-radius: 3px;
            width: 0%;
            transition: width 0.1s;
        }
        
        .control-buttons {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .ctrl-btn {
            background: none;
            border: none;
            color: #fff;
            font-size: 20px;
            cursor: pointer;
            padding: 5px;
        }
        .ctrl-btn:hover { color: #e94560; }
        
        .time-display {
            font-size: 12px;
            color: rgba(255,255,255,0.8);
        }
        
        .volume-control {
            display: flex;
            align-items: center;
            gap: 5px;
            margin-left: auto;
        }
        .volume-slider {
            width: 80px;
            height: 4px;
            -webkit-appearance: none;
            background: rgba(255,255,255,0.3);
            border-radius: 2px;
        }
        .volume-slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 12px;
            height: 12px;
            background: #e94560;
            border-radius: 50%;
            cursor: pointer;
        }
        
        .fullscreen-btn { margin-left: 15px; }
        
        .source-selector {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
            flex-wrap: wrap;
            align-items: center;
        }
        .source-selector label {
            font-size: 14px;
            color: rgba(255,255,255,0.7);
        }
        .source-btn {
            padding: 8px 16px;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 20px;
            color: #fff;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.2s;
        }
        .source-btn.active { 
            background: linear-gradient(135deg, #e94560, #8b5cf6);
            border-color: transparent;
        }
        .source-btn:hover { 
            background: rgba(233, 69, 96, 0.3);
            border-color: #e94560;
        }
        .source-btn .quality-badge {
            background: rgba(0,0,0,0.3);
            padding: 2px 6px;
            border-radius: 10px;
            font-size: 10px;
            margin-left: 5px;
        }
        
        .episodes-section h3 {
            margin-bottom: 15px;
            color: #e94560;
        }
        .episodes {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        .ep-btn {
            width: 50px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(255,255,255,0.1);
            border: none;
            border-radius: 8px;
            color: #fff;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
            transition: all 0.2s;
        }
        .ep-btn:hover { background: rgba(233, 69, 96, 0.5); transform: scale(1.1); }
        .ep-btn.active { background: #e94560; }
        .ep-btn.has-video { border: 2px solid #4CAF50; }
        
        .loading {
            display: none;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(0,0,0,0.8);
            padding: 20px 40px;
            border-radius: 10px;
            z-index: 100;
        }
        .loading.show { display: block; }
        .loading .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid rgba(255,255,255,0.2);
            border-top-color: #e94560;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        
        .error-message {
            display: none;
            text-align: center;
            padding: 40px;
            color: #e94560;
        }
        .error-message.show { display: block; }
        
        .player-placeholder {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 400px;
            background: #111;
            color: rgba(255,255,255,0.5);
            font-size: 18px;
        }
        
        /* Iframe Player */
        .iframe-container {
            position: relative;
            width: 100%;
            padding-top: 56.25%; /* 16:9 */
            display: none;
        }
        .iframe-container.show { display: block; }
        .iframe-container iframe {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            border: none;
        }
        
        /* Native Video */
        .video-container {
            display: none;
        }
        .video-container.show { display: block; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-btn">← Ana Sayfa</a>
        
        <div class="header">
            {% if anime.cover_local %}
            <img src="/covers/{{ anime.cover_local.split('/')[-1] }}" alt="{{ anime.title }}">
            {% elif anime.cover_url %}
            <img src="{{ anime.cover_url }}" alt="{{ anime.title }}">
            {% endif %}
            <div class="header-info">
                <h1>{{ anime.title }}</h1>
                <p>📺 {{ anime.type or 'TV' }} | 📅 {{ anime.year or '?' }} | ⭐ {{ anime.score or '?' }}</p>
                <p>📝 {{ anime.episodes or '?' }} Bölüm | MAL ID: {{ anime.mal_id }}</p>
                <div style="margin-top: 10px; font-size: 13px; opacity: 0.8; max-height: 60px; overflow-y: auto;">
                    {{ anime.synopsis[:300] if anime.synopsis else '' }}...
                </div>
            </div>
        </div>
        
        <div class="player-container" id="playerContainer">
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <div>Video yükleniyor...</div>
            </div>
            
            <div class="error-message" id="errorMessage">
                ❌ Video yüklenemedi
                <br><small>Farklı bir kaynak deneyin</small>
            </div>
            
            <div class="player-placeholder" id="placeholder">
                🎬 Bir bölüm seçin veya kaynak bekleyin...
            </div>
            
            <!-- Native HTML5 Video + HLS.js -->
            <div class="video-container" id="videoContainer">
                <video id="videoPlayer" controls playsinline>
                    Tarayıcınız video oynatmayı desteklemiyor.
                </video>
            </div>
            
            <!-- Iframe Player (Embed için) -->
            <div class="iframe-container" id="iframeContainer">
                <iframe id="iframePlayer" allowfullscreen allow="autoplay; encrypted-media"></iframe>
            </div>
        </div>
        
        <div class="source-selector" id="sourceSelector">
            <label>🎬 Kaynaklar:</label>
        </div>
        
        <div class="episodes-section">
            <h3>📺 Bölümler</h3>
            <div class="episodes" id="episodeList">
                {% for ep in episodes %}
                <button class="ep-btn {% if ep.episode_number == current_ep %}active{% endif %} {% if ep.has_video %}has-video{% endif %}"
                        onclick="loadEpisode({{ ep.episode_number }})"
                        title="{{ ep.title }}">
                    {{ ep.episode_number }}
                </button>
                {% endfor %}
            </div>
        </div>
    </div>
    
    <!-- HLS.js for HLS streams -->
    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
    
    <script>
        const malId = {{ anime.mal_id }};
        let currentEp = {{ current_ep }};
        let currentVideos = [];
        let hls = null;
        
        const videoPlayer = document.getElementById('videoPlayer');
        const iframePlayer = document.getElementById('iframePlayer');
        const videoContainer = document.getElementById('videoContainer');
        const iframeContainer = document.getElementById('iframeContainer');
        const placeholder = document.getElementById('placeholder');
        const loading = document.getElementById('loading');
        const errorMessage = document.getElementById('errorMessage');
        const sourceSelector = document.getElementById('sourceSelector');
        
        // Sayfa yüklendiğinde
        document.addEventListener('DOMContentLoaded', function() {
            if (currentEp > 0) {
                loadEpisode(currentEp);
            }
        });
        
        async function loadEpisode(epNum) {
            currentEp = epNum;
            
            // Aktif butonu güncelle
            document.querySelectorAll('.ep-btn').forEach(btn => {
                btn.classList.toggle('active', parseInt(btn.textContent) === epNum);
            });
            
            // URL güncelle
            history.pushState({}, '', `/player?mal_id=${malId}&ep=${epNum}`);
            
            // Reset UI
            hideAll();
            loading.classList.add('show');
            
            try {
                const response = await fetch(`/api/stream/${malId}/${epNum}`);
                const data = await response.json();
                
                loading.classList.remove('show');
                
                if (data.videos && data.videos.length > 0) {
                    currentVideos = data.videos;
                    updateSourceSelector(data.videos);
                    playVideo(data.videos[0]);
                } else {
                    showError('Bu bölüm için video bulunamadı');
                }
            } catch (error) {
                console.error('Video yükleme hatası:', error);
                loading.classList.remove('show');
                showError('Video yüklenirken hata oluştu');
            }
        }
        
        function updateSourceSelector(videos) {
            // Fansub'a göre grupla
            const grouped = {};
            videos.forEach(v => {
                const key = v.fansub || 'Bilinmeyen';
                if (!grouped[key]) grouped[key] = [];
                grouped[key].push(v);
            });
            
            let html = '<label>🎬 Kaynaklar:</label>';
            let index = 0;
            
            for (const [fansub, vids] of Object.entries(grouped)) {
                vids.forEach(v => {
                    const quality = v.quality || 'Auto';
                    const isActive = index === 0 ? 'active' : '';
                    html += `<button class="source-btn ${isActive}" onclick="selectSource(${index})" data-index="${index}">
                        ${fansub} <span class="quality-badge">${quality}</span>
                    </button>`;
                    index++;
                });
            }
            
            sourceSelector.innerHTML = html;
        }
        
        function selectSource(index) {
            if (index >= 0 && index < currentVideos.length) {
                // Aktif butonu güncelle
                document.querySelectorAll('.source-btn').forEach(btn => {
                    btn.classList.toggle('active', parseInt(btn.dataset.index) === index);
                });
                
                playVideo(currentVideos[index]);
            }
        }
        
        function playVideo(video) {
            hideAll();
            
            const streamUrl = video.stream_url || video.video_url;
            console.log('Playing:', streamUrl, 'Type:', video.type);
            
            // URL tipini belirle
            const isHLS = streamUrl.includes('.m3u8') || video.type === 'hls';
            const isEmbed = streamUrl.includes('iframe') || 
                           streamUrl.includes('embed') || 
                           streamUrl.includes('player') ||
                           streamUrl.includes('sibnet') ||
                           streamUrl.includes('tau-video') ||
                           streamUrl.includes('anizmplayer');
            
            if (isEmbed && !isHLS) {
                // Embed/Iframe player
                playIframe(streamUrl);
            } else if (isHLS) {
                // HLS Stream
                playHLS(streamUrl);
            } else {
                // Direct MP4/Video
                playDirect(streamUrl);
            }
        }
        
        function playIframe(url) {
            iframeContainer.classList.add('show');
            iframePlayer.src = url;
        }
        
        function playHLS(url) {
            videoContainer.classList.add('show');
            
            // Önceki HLS instance'ı temizle
            if (hls) {
                hls.destroy();
                hls = null;
            }
            
            if (Hls.isSupported()) {
                hls = new Hls({
                    debug: false,
                    enableWorker: true,
                    lowLatencyMode: true,
                    backBufferLength: 90
                });
                
                hls.loadSource(url);
                hls.attachMedia(videoPlayer);
                
                hls.on(Hls.Events.MANIFEST_PARSED, function() {
                    videoPlayer.play().catch(e => console.log('Autoplay engellendi:', e));
                });
                
                hls.on(Hls.Events.ERROR, function(event, data) {
                    if (data.fatal) {
                        console.error('HLS Fatal Error:', data);
                        switch(data.type) {
                            case Hls.ErrorTypes.NETWORK_ERROR:
                                // Ağ hatası - yeniden dene
                                console.log('Network error, trying to recover...');
                                hls.startLoad();
                                break;
                            case Hls.ErrorTypes.MEDIA_ERROR:
                                // Media hatası - kurtarmaya çalış
                                console.log('Media error, trying to recover...');
                                hls.recoverMediaError();
                                break;
                            default:
                                showError('Video oynatılamadı - farklı kaynak deneyin');
                                break;
                        }
                    }
                });
            } else if (videoPlayer.canPlayType('application/vnd.apple.mpegurl')) {
                // Safari native HLS
                videoPlayer.src = url;
                videoPlayer.addEventListener('loadedmetadata', function() {
                    videoPlayer.play().catch(e => console.log('Autoplay engellendi:', e));
                });
            } else {
                showError('Tarayıcınız HLS desteklemiyor');
            }
        }
        
        function playDirect(url) {
            videoContainer.classList.add('show');
            
            if (hls) {
                hls.destroy();
                hls = null;
            }
            
            videoPlayer.src = url;
            videoPlayer.load();
            videoPlayer.play().catch(e => console.log('Autoplay engellendi:', e));
            
            videoPlayer.onerror = function() {
                showError('Video oynatılamadı - farklı kaynak deneyin');
            };
        }
        
        function hideAll() {
            videoContainer.classList.remove('show');
            iframeContainer.classList.remove('show');
            placeholder.style.display = 'none';
            errorMessage.classList.remove('show');
            loading.classList.remove('show');
            
            // Video durdur
            videoPlayer.pause();
            videoPlayer.src = '';
            iframePlayer.src = '';
        }
        
        function showError(msg) {
            errorMessage.innerHTML = `❌ ${msg}<br><small>Farklı bir kaynak deneyin</small>`;
            errorMessage.classList.add('show');
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            if (e.target.tagName === 'INPUT') return;
            
            switch(e.key) {
                case 'ArrowRight':
                    if (e.shiftKey && currentEp < {{ episodes|length }}) {
                        loadEpisode(currentEp + 1);
                    } else {
                        videoPlayer.currentTime += 10;
                    }
                    break;
                case 'ArrowLeft':
                    if (e.shiftKey && currentEp > 1) {
                        loadEpisode(currentEp - 1);
                    } else {
                        videoPlayer.currentTime -= 10;
                    }
                    break;
                case ' ':
                    e.preventDefault();
                    videoPlayer.paused ? videoPlayer.play() : videoPlayer.pause();
                    break;
                case 'f':
                    toggleFullscreen();
                    break;
            }
        });
        
        function toggleFullscreen() {
            const container = document.getElementById('playerContainer');
            if (document.fullscreenElement) {
                document.exitFullscreen();
            } else {
                container.requestFullscreen();
            }
        }
    </script>
</body>
</html>
"""

SEASON_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ year }} {{ season|capitalize }} - Anime Listesi</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', sans-serif; 
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
        }
        .header h1 { color: #e94560; }
        .back-btn {
            padding: 10px 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
            color: #fff;
            text-decoration: none;
        }
        .back-btn:hover { background: rgba(255,255,255,0.2); }
        
        .sync-btn {
            padding: 10px 20px;
            background: #4CAF50;
            border: none;
            border-radius: 20px;
            color: #fff;
            cursor: pointer;
            font-size: 14px;
        }
        .sync-btn:hover { background: #45a049; }
        .sync-btn:disabled { background: #666; cursor: not-allowed; }
        
        .anime-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 20px;
        }
        .anime-card {
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            overflow: hidden;
            cursor: pointer;
            transition: all 0.3s;
        }
        .anime-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(233, 69, 96, 0.3);
        }
        .anime-card img {
            width: 100%;
            height: 250px;
            object-fit: cover;
        }
        .anime-card .info {
            padding: 10px;
        }
        .anime-card h3 {
            font-size: 14px;
            margin-bottom: 5px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .anime-card p {
            font-size: 12px;
            color: rgba(255,255,255,0.6);
        }
        .anime-card .score {
            color: #FFD700;
        }
        
        .in-db { border: 2px solid #4CAF50; }
        .not-in-db { border: 2px solid rgba(255,255,255,0.1); }
        
        .status-bar {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
            font-size: 14px;
        }
        .status-bar span { color: rgba(255,255,255,0.7); }
        .status-bar .green { color: #4CAF50; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <a href="/" class="back-btn">← Ana Sayfa</a>
                <h1 style="margin-top: 10px;">{{ year }} {{ season|capitalize }}</h1>
            </div>
            <button class="sync-btn" onclick="syncSeason()" id="syncBtn">
                🔄 Tümünü Senkronize Et
            </button>
        </div>
        
        <div class="status-bar">
            <span>Toplam: <strong>{{ anime_list|length }}</strong></span>
            <span class="green">Veritabanında: <strong id="inDbCount">{{ in_db_count }}</strong></span>
        </div>
        
        <div class="anime-grid">
            {% for anime in anime_list %}
            <div class="anime-card {{ 'in-db' if anime.in_db else 'not-in-db' }}" 
                 onclick="location.href='/player?mal_id={{ anime.mal_id }}'">
                <img src="{{ anime.image }}" alt="{{ anime.title }}" loading="lazy">
                <div class="info">
                    <h3 title="{{ anime.title }}">{{ anime.title }}</h3>
                    <p>
                        <span class="score">⭐ {{ anime.score or '?' }}</span> |
                        {{ anime.type or 'TV' }}
                    </p>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
    
    <script>
        async function syncSeason() {
            const btn = document.getElementById('syncBtn');
            btn.disabled = true;
            btn.textContent = '⏳ Senkronize ediliyor...';
            
            try {
                const response = await fetch('/api/sync/season', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ year: {{ year }}, season: '{{ season }}' })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    alert(`✅ ${data.synced} anime senkronize edildi!`);
                    location.reload();
                } else {
                    alert('❌ Hata: ' + data.error);
                }
            } catch (error) {
                alert('❌ Bağlantı hatası');
            }
            
            btn.disabled = false;
            btn.textContent = '🔄 Tümünü Senkronize Et';
        }
    </script>
</body>
</html>
"""

SEARCH_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Arama: {{ query }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', sans-serif; 
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .back-btn {
            display: inline-block;
            padding: 10px 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
            color: #fff;
            text-decoration: none;
            margin-bottom: 20px;
        }
        h1 { color: #e94560; margin-bottom: 20px; }
        
        .results {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 20px;
        }
        .anime-card {
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            overflow: hidden;
            cursor: pointer;
            transition: all 0.3s;
        }
        .anime-card:hover { transform: translateY(-5px); }
        .anime-card img {
            width: 100%;
            height: 250px;
            object-fit: cover;
        }
        .anime-card .info { padding: 10px; }
        .anime-card h3 { font-size: 14px; margin-bottom: 5px; }
        .anime-card p { font-size: 12px; color: rgba(255,255,255,0.6); }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-btn">← Ana Sayfa</a>
        <h1>🔍 "{{ query }}" için sonuçlar</h1>
        
        <div class="results">
            {% for anime in results %}
            <div class="anime-card" onclick="location.href='/player?mal_id={{ anime.mal_id }}'">
                <img src="{{ anime.cover_url or anime.cover_local or '' }}" alt="{{ anime.title }}">
                <div class="info">
                    <h3>{{ anime.title }}</h3>
                    <p>⭐ {{ anime.score or '?' }} | MAL: {{ anime.mal_id }}</p>
                </div>
            </div>
            {% endfor %}
        </div>
        
        {% if not results %}
        <p style="text-align: center; color: rgba(255,255,255,0.5);">Sonuç bulunamadı.</p>
        {% endif %}
    </div>
</body>
</html>
"""


# ─────────────────────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/info")
def info_page():
    """Anime bilgi ve JSON çıktısı."""
    mal_id = request.args.get("mal_id", type=int)
    if not mal_id:
        return jsonify({"error": "mal_id required"}), 400
    
    anime = ensure_anime_data(mal_id)
    if not anime:
        return jsonify({"error": "Anime not found"}), 404
        
    return jsonify(anime)


@app.route("/")
def home():
    """Ana sayfa."""
    # İstatistikleri çek
    conn = db.get_connection()
    stats = {"anime_count": 0, "episode_count": 0, "video_count": 0}
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT COUNT(*) as count FROM animes")
        res = cursor.fetchone()
        if res:
             stats["anime_count"] = int(cast(Dict[str, Any], res)["count"])

        cursor.execute("SELECT COUNT(*) as count FROM episodes")
        res = cursor.fetchone()
        if res:
             stats["episode_count"] = int(cast(Dict[str, Any], res)["count"])

        cursor.execute("SELECT COUNT(*) as count FROM video_links")
        res = cursor.fetchone()
        if res:
             stats["video_count"] = int(cast(Dict[str, Any], res)["count"])
        
        cursor.close()
        conn.close()
    
    seasons = get_available_seasons()
    
    return render_template_string(HOME_TEMPLATE, stats=stats, seasons=seasons)


@app.route("/player")
def player():
    """Anime oynatıcı sayfası."""
    mal_id = request.args.get("mal_id", type=int)
    ep = request.args.get("ep", 1, type=int)
    
    if not mal_id:
        return redirect("/")
    
    # Anime bilgilerini çek (Helper kullan)
    anime_raw = ensure_anime_data(mal_id)
    
    if not anime_raw:
        return "Anime bulunamadı", 404
    
    anime = cast(Dict[str, Any], anime_raw)
    
    # Bölümleri çek
    conn = db.get_connection()
    episodes = []
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT e.*, 
                   (SELECT COUNT(*) FROM video_links WHERE episode_id = e.id) as video_count
            FROM episodes e
            WHERE e.anime_id = %s
            ORDER BY e.episode_number
        """, (int(anime["id"]),))
        
        rows = cursor.fetchall()
        for row in rows:
            row_dict = cast(Dict[str, Any], row)
            episodes.append({
                "episode_number": row_dict["episode_number"],
                "title": row_dict["title"],
                "has_video": (row_dict["video_count"] or 0) > 0
            })
        
        cursor.close()
        conn.close()
    
    # Eğer bölüm yoksa, en az total episode kadar placeholder oluştur
    total_eps = anime.get("episodes")
    if not episodes and total_eps:
        episodes = [{"episode_number": i, "title": f"{i}. Bölüm", "has_video": False} 
                    for i in range(1, int(total_eps) + 1)]
    
    return render_template_string(PLAYER_TEMPLATE, 
                                  anime=anime, 
                                  episodes=episodes, 
                                  current_ep=ep)


@app.route("/season/<int:year>/<season>")
def season_page(year, season):
    """Sezon anime listesi sayfası."""
    # Jikan'dan sezon listesini çek
    anime_list_raw = fetch_all_season_anime(year, season)
    
    # Veritabanındaki MAL ID'leri
    db_mal_ids = set(db.get_all_mal_ids())
    
    anime_list = []
    in_db_count = 0
    
    for anime in anime_list_raw:
        mal_id = anime.get("mal_id")
        in_db = mal_id in db_mal_ids
        if in_db:
            in_db_count += 1
        
        images = anime.get("images", {}).get("jpg", {})
        
        anime_list.append({
            "mal_id": mal_id,
            "title": anime.get("title", ""),
            "image": images.get("large_image_url") or images.get("image_url", ""),
            "score": anime.get("score"),
            "type": anime.get("type"),
            "in_db": in_db
        })
    
    return render_template_string(SEASON_TEMPLATE,
                                  year=year,
                                  season=season,
                                  anime_list=anime_list,
                                  in_db_count=in_db_count)


@app.route("/search")
def search_page():
    """Arama sayfası."""
    query = request.args.get("q", "")
    
    if not query:
        return redirect("/")
    
    results = db.get_anime_by_title(query) or []
    
    return render_template_string(SEARCH_TEMPLATE, query=query, results=results)


@app.route("/covers/<filename>")
def serve_cover(filename):
    """Cover resimlerini sun."""
    from flask import send_from_directory
    return send_from_directory("covers", filename)


# ─────────────────────────────────────────────────────────────────────────────
# API ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/dbanimelist")
def api_db_anime_list():
    """
    Veritabanındaki tüm anime'lerin kısa listesi (hızlı çekilebilir).
    
    Response:
    {
        "count": 150,
        "animes": [
            {
                "mal_id": 21,
                "title": "One Punch Man",
                "title_english": "One Punch Man",
                "cover": "http://host:port/covers/21.jpg",
                "type": "TV",
                "episodes": 12,
                "status": "Finished Airing",
                "score": 8.5,
                "year": 2015,
                "season": "fall"
            },
            ...
        ]
    }
    """
    conn = db.get_connection()
    if not conn:
        return jsonify({"error": "DB bağlantı hatası"}), 500
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT mal_id, title, title_english, title_japanese,
               type, episodes, status, score, year, season,
               cover_local, rating, popularity
        FROM animes
        ORDER BY mal_id
    """)
    
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Cover URL'lerini oluştur
    host = request.host_url.rstrip('/')
    animes = []
    for row in rows:
        r = cast(Dict[str, Any], row)
        mal_id = r.get("mal_id")
        
        # Cover URL
        cover_local = r.get("cover_local", "")
        if cover_local:
            cover_url = f"{host}/covers/{mal_id}.jpg"
        else:
            cover_url = None
        
        animes.append({
            "mal_id": mal_id,
            "title": r.get("title"),
            "title_english": r.get("title_english"),
            "title_japanese": r.get("title_japanese"),
            "cover": cover_url,
            "type": r.get("type"),
            "episodes": r.get("episodes"),
            "status": r.get("status"),
            "score": float(r["score"]) if r.get("score") else None,
            "year": r.get("year"),
            "season": r.get("season"),
            "rating": r.get("rating"),
            "popularity": r.get("popularity")
        })
    
    return jsonify({
        "count": len(animes),
        "animes": animes
    })


@app.route("/api/json")
def api_json_endpoint():
    """
    Anime bilgileri ve video linkleri için tek endpoint.
    
    Parametreler:
        malid: MAL ID (zorunlu)
        episode: Bölüm numarası (opsiyonel)
    
    Episode yoksa:
        - Anime hakkındaki tüm bilgiler (DB'de yoksa çekilir)
        - Bölüm listesi (yoksa Jikan'dan çekilir)
        - Her bölümün video sayısı
    
    Episode varsa:
        - Anime bilgileri
        - Bölüm video linkleri (adaptörlerden çekilir, çalışanlar kontrol edilir)
    
    Örnek:
        /api/json?malid=21              -> Anime bilgileri + bölüm listesi
        /api/json?malid=21&episode=1    -> Anime + 1. bölüm video linkleri
    """
    from main import update_anime_by_mal_id
    
    mal_id = request.args.get("malid", type=int)
    episode = request.args.get("episode", type=int)
    
    if not mal_id:
        return jsonify({"error": "malid parametresi gerekli", "usage": "/api/json?malid=21&episode=1"}), 400
    
    # Anime bilgilerini çek
    anime_raw = db.get_anime_by_mal_id(mal_id)
    
    # DB'de yoksa önce anime bilgilerini ve bölümleri çek
    if not anime_raw:
        print(f"[API JSON] {mal_id} DB'de yok, çekiliyor...")
        result = update_anime_by_mal_id(mal_id, skip_videos=True)
        if not result:
            return jsonify({"error": "Anime bulunamadı", "mal_id": mal_id}), 404
        anime_raw = db.get_anime_by_mal_id(mal_id)
        if not anime_raw:
            return jsonify({"error": "Anime çekilemedi", "mal_id": mal_id}), 500
    
    anime = cast(Dict[str, Any], anime_raw)
    anime_db_id = int(anime["id"])
    
    # Cover URL
    host = request.host_url.rstrip('/')
    cover_url = f"{host}/covers/{mal_id}.jpg" if anime.get("cover_local") else anime.get("cover_url")
    
    # Temel anime bilgileri
    anime_info = {
        "mal_id": mal_id,
        "title": anime.get("title"),
        "title_english": anime.get("title_english"),
        "title_japanese": anime.get("title_japanese"),
        "type": anime.get("type"),
        "source": anime.get("source"),
        "episodes": anime.get("episodes"),
        "status": anime.get("status"),
        "airing": anime.get("airing"),
        "aired_from": str(anime.get("aired_from")) if anime.get("aired_from") else None,
        "aired_to": str(anime.get("aired_to")) if anime.get("aired_to") else None,
        "duration": anime.get("duration"),
        "rating": anime.get("rating"),
        "score": float(anime["score"]) if anime.get("score") else None,
        "scored_by": anime.get("scored_by"),
        "rank": anime.get("rank"),
        "popularity": anime.get("popularity"),
        "members": anime.get("members"),
        "favorites": anime.get("favorites"),
        "synopsis": anime.get("synopsis"),
        "background": anime.get("background"),
        "season": anime.get("season"),
        "year": anime.get("year"),
        "cover": cover_url,
        "trailer_url": anime.get("trailer_url")
    }
    
    # Episode yoksa -> Anime bilgileri + bölüm listesi
    if episode is None:
        conn = db.get_connection()
        if not conn:
            return jsonify({"error": "DB bağlantı hatası"}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Bölüm listesi
        cursor.execute("""
            SELECT e.episode_number, e.title,
                   (SELECT COUNT(*) FROM video_links vl WHERE vl.episode_id = e.id AND vl.is_active = TRUE) as video_count
            FROM episodes e
            WHERE e.anime_id = %s
            ORDER BY e.episode_number
        """, (anime_db_id,))
        
        episodes_list = []
        for row in cursor.fetchall():
            r = cast(Dict[str, Any], row)
            episodes_list.append({
                "episode": r["episode_number"],
                "title": r.get("title"),
                "video_count": r.get("video_count", 0)
            })
        
        # Bölüm yoksa tekrar güncelle (belki yeni eklendi)
        if not episodes_list:
            print(f"[API JSON] {mal_id} bölüm yok, tekrar güncelleniyor...")
            cursor.close()
            conn.close()
            update_anime_by_mal_id(mal_id, skip_videos=True)
            
            # Tekrar çek
            conn = db.get_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT e.episode_number, e.title,
                           (SELECT COUNT(*) FROM video_links vl WHERE vl.episode_id = e.id AND vl.is_active = TRUE) as video_count
                    FROM episodes e
                    WHERE e.anime_id = %s
                    ORDER BY e.episode_number
                """, (anime_db_id,))
                
                for row in cursor.fetchall():
                    r = cast(Dict[str, Any], row)
                    episodes_list.append({
                        "episode": r["episode_number"],
                        "title": r.get("title"),
                        "video_count": r.get("video_count", 0)
                    })
                cursor.close()
                conn.close()
        
        # Türler
        conn = db.get_connection()
        genres = []
        studios = []
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT g.name FROM genres g
                JOIN anime_genres ag ON g.id = ag.genre_id
                WHERE ag.anime_id = %s
            """, (anime_db_id,))
            genres = [cast(Dict[str, Any], r)["name"] for r in cursor.fetchall()]
            
            # Stüdyolar
            cursor.execute("""
                SELECT s.name FROM studios s
                JOIN anime_studios ast ON s.id = ast.studio_id
                WHERE ast.anime_id = %s
            """, (anime_db_id,))
            studios = [cast(Dict[str, Any], r)["name"] for r in cursor.fetchall()]
            
            cursor.close()
            conn.close()
        
        return jsonify({
            "success": True,
            "anime": anime_info,
            "genres": genres,
            "studios": studios,
            "episodes": episodes_list,
            "total_episodes": len(episodes_list)
        })
    
    # Episode varsa -> Video linkleri ile birlikte
    else:
        # Önce DB'den video linklerini çek
        videos = db.get_video_links(anime_id=anime_db_id, episode_number=episode)
        
        if not videos:
            # DB'de video yok - adaptörlerden çekmeyi dene
            print(f"[API] {mal_id} ep.{episode} için video yok, adaptörlerden çekiliyor...")
            ensure_episode_videos(mal_id, episode, anime_db_id)
            videos = db.get_video_links(anime_id=anime_db_id, episode_number=episode)
        
        if not videos:
            return jsonify({
                "success": True,
                "anime": anime_info,
                "episode": episode,
                "videos": [],
                "message": "Bu bölüm için video bulunamadı"
            })
        
        # Video linklerini kontrol et ve çalışanları bul
        working_videos = []
        dead_videos = []
        
        def check_and_process_video(video):
            video_dict = cast(Dict[str, Any], video)
            video_url = video_dict.get("video_url", "")
            video_id = video_dict.get("id")
            
            # Link canlı mı kontrol et
            is_alive, stream_info = check_video_link_alive(video_url, timeout=10)
            
            if is_alive and stream_info:
                return {
                    "alive": True,
                    "video_id": video_id,
                    "data": {
                        "fansub": video_dict.get("fansub"),
                        "quality": stream_info.get("quality", "unknown"),
                        "original_url": video_url,
                        "stream_url": stream_info.get("url", video_url),
                        "type": stream_info.get("type", "direct"),
                        "source": video_dict.get("source_name", "unknown")
                    }
                }
            else:
                return {
                    "alive": False,
                    "video_id": video_id,
                    "url": video_url
                }
        
        # Paralel kontrol
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(check_and_process_video, v) for v in videos]
            for future in as_completed(futures):
                result = future.result()
                if result:
                    if result.get("alive"):
                        working_videos.append(result["data"])
                    else:
                        dead_videos.append(result)
        
        # Ölü linkleri pasif yap
        if dead_videos:
            def cleanup():
                for dv in dead_videos:
                    if dv.get("video_id"):
                        remove_dead_video_link(dv["video_id"])
            Thread(target=cleanup, daemon=True).start()
            
            # Ölü link varsa ve çalışan az ise adaptörden yeniden çek
            if len(working_videos) < 2:
                print(f"[API] {mal_id} ep.{episode} için çalışan video az, adaptörlerden yenileniyor...")
                ensure_episode_videos(mal_id, episode, anime_db_id, force_refresh=True)
                
                # Yeni eklenen videoları kontrol et
                new_videos = db.get_video_links(anime_id=anime_db_id, episode_number=episode)
                for v in new_videos:
                    v_dict = cast(Dict[str, Any], v)
                    # Zaten kontrol ettiğimiz videoları atla
                    if any(wv.get("original_url") == v_dict.get("video_url") for wv in working_videos):
                        continue
                    
                    is_alive, stream_info = check_video_link_alive(v_dict.get("video_url", ""), timeout=8)
                    if is_alive and stream_info:
                        working_videos.append({
                            "fansub": v_dict.get("fansub"),
                            "quality": stream_info.get("quality", "unknown"),
                            "original_url": v_dict.get("video_url"),
                            "stream_url": stream_info.get("url", v_dict.get("video_url")),
                            "type": stream_info.get("type", "direct"),
                            "source": v_dict.get("source_name", "unknown")
                        })
        
        # Kaliteye göre sırala
        def quality_sort(v):
            q = v.get("quality", "")
            match = re.search(r"(\d+)", str(q))
            return int(match.group(1)) if match else 0
        
        working_videos.sort(key=quality_sort, reverse=True)
        
        return jsonify({
            "success": True,
            "anime": anime_info,
            "episode": episode,
            "videos": working_videos,
            "video_count": len(working_videos),
            "dead_count": len(dead_videos)
        })


@app.route("/api/anime/<int:mal_id>")
def api_anime(mal_id):
    """Anime bilgilerini döndür."""
    anime = db.get_anime_by_mal_id(mal_id)
    if not anime:
        return jsonify({"error": "Anime bulunamadı"}), 404
    return jsonify(anime)


@app.route("/api/episodes/<int:mal_id>")
def api_episodes(mal_id):
    """Bölüm listesini döndür."""
    anime_raw = db.get_anime_by_mal_id(mal_id)
    if not anime_raw:
        return jsonify({"error": "Anime bulunamadı"}), 404
    
    anime = cast(Dict[str, Any], anime_raw)
    
    conn = db.get_connection()
    if not conn:
        return jsonify({"error": "DB bağlantı hatası"}), 500
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT e.episode_number, e.title,
               (SELECT COUNT(*) FROM video_links WHERE episode_id = e.id) as video_count
        FROM episodes e
        WHERE e.anime_id = %s
        ORDER BY e.episode_number
    """, (int(anime["id"]),))
    
    episodes = [cast(Dict[str, Any], r) for r in cursor.fetchall()]
    cursor.close()
    conn.close()
    
    return jsonify({"mal_id": mal_id, "episodes": episodes})


@app.route("/api/stream/<int:mal_id>/<int:episode>")
def api_stream(mal_id, episode):
    """
    Bölüm video stream URL'lerini döndür.
    yt-dlp ile en iyi kaliteyi bul.
    """
    anime_raw = ensure_anime_data(mal_id)
    if not anime_raw:
        return jsonify({"error": "Anime bulunamadı"}), 404
    
    anime = cast(Dict[str, Any], anime_raw)
    
    # Canlı bölüm fetch (eğer yoksa)
    if "id" in anime:
        ensure_episode_videos(mal_id, episode, int(anime["id"]))
    
    # Video linklerini çek
    videos = []
    if "id" in anime:
        videos = db.get_video_links(anime_id=int(anime["id"]), episode_number=episode)
    
    if not videos:
        return jsonify({"mal_id": mal_id, "episode": episode, "videos": []})
    
    result_videos = []
    dead_links = []
    
    # Her video için link kontrolü yap ve en iyi kaliteyi bul (paralel)
    def process_video_with_validation(video):
        video_url = video["video_url"]
        video_id = video.get("id")
        
        # Link canlı mı kontrol et
        is_alive, stream_info = check_video_link_alive(video_url)
        
        if not is_alive:
            # Ölü link - silme listesine ekle
            return {"dead": True, "video_id": video_id, "url": video_url}
        
        if stream_info:
            return {
                "dead": False,
                "fansub": video["fansub"],
                "quality": stream_info.get("quality", "unknown"),
                "video_url": video_url,
                "stream_url": stream_info["url"],
                "type": stream_info.get("type", "direct")
            }
        
        # Fallback - direkt URL döndür
        return {
            "dead": False,
            "fansub": video["fansub"],
            "quality": "unknown",
            "video_url": video_url,
            "stream_url": video_url,
            "type": "direct"
        }
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_video_with_validation, v) for v in videos]
        for future in as_completed(futures):
            result = future.result()
            if result:
                if result.get("dead"):
                    dead_links.append(result)
                else:
                    result_videos.append(result)
    
    # Ölü linkleri veritabanından kaldır (arka planda)
    if dead_links:
        def cleanup_dead():
            for dl in dead_links:
                if dl.get("video_id"):
                    remove_dead_video_link(dl["video_id"])
                    print(f"[LinkCheck] Ölü link temizlendi: {dl.get('url', 'unknown')}")
        
        # Cleanup'ı arka planda yap
        Thread(target=cleanup_dead, daemon=True).start()
    
    # Kaliteye göre sırala (yüksek önce)
    def quality_sort_key(v):
        q = v.get("quality", "")
        match = re.search(r"(\d+)", q)
        return int(match.group(1)) if match else 0
    
    result_videos.sort(key=quality_sort_key, reverse=True)
    
    return jsonify({
        "mal_id": mal_id,
        "episode": episode,
        "videos": result_videos
    })


@app.route("/api/seasons")
def api_seasons():
    """Mevcut sezonları listele."""
    return jsonify(get_available_seasons()[:100])


@app.route("/api/seasons/<int:year>/<season>")
def api_season_anime(year, season):
    """Sezon anime listesini döndür."""
    anime_list = fetch_all_season_anime(year, season)
    
    result = []
    for anime in anime_list:
        result.append({
            "mal_id": anime.get("mal_id"),
            "title": anime.get("title"),
            "score": anime.get("score"),
            "type": anime.get("type"),
            "episodes": anime.get("episodes"),
        })
    
    return jsonify({
        "year": year,
        "season": season,
        "count": len(result),
        "anime": result
    })


@app.route("/api/sync/season", methods=["POST"])
def api_sync_season():
    """
    Sezon anime'lerini senkronize et (PARALEL - video çekmez).
    
    Body:
    {
        "year": 2024,
        "season": "winter",
        "parallel": 20,        // Paralel işlem sayısı (varsayılan: 20)
        "include_existing": false  // Zaten var olanları da güncelle
    }
    """
    data = request.get_json() or {}
    year = data.get("year")
    season = data.get("season")
    parallel = min(data.get("parallel", 20), 50)  # Max 50 paralel
    include_existing = data.get("include_existing", False)
    
    if not year or not season:
        return jsonify({"error": "year ve season gerekli"}), 400
    
    # Import main modülünü
    from main import update_anime_by_mal_id, load_anime_ids
    
    # Sezon anime'lerini çek
    anime_list = fetch_all_season_anime(year, season)
    anime_ids_map = load_anime_ids()
    
    # Veritabanındaki MAL ID'ler
    existing_ids = set(db.get_all_mal_ids())
    
    # Güncellenecek anime listesi
    to_sync = []
    for anime in anime_list:
        mal_id = anime.get("mal_id")
        if not mal_id:
            continue
        if mal_id in existing_ids and not include_existing:
            continue
        
        # Extra ID'leri bul
        extra_ids = None
        for anidb_id, ids in anime_ids_map.items():
            if ids.get("mal_id") == mal_id:
                extra_ids = {
                    "anidb_id": int(anidb_id),
                    "anilist_id": ids.get("anilist_id"),
                    "tvdb_id": ids.get("tvdb_id"),
                    "imdb_id": ids.get("imdb_id")
                }
                break
        
        to_sync.append((mal_id, extra_ids))
    
    if not to_sync:
        return jsonify({
            "success": True,
            "message": "Güncellenecek anime bulunamadı",
            "synced": 0,
            "errors": 0,
            "total": len(anime_list),
            "skipped": len(anime_list)
        })
    
    synced = 0
    errors = 0
    results_lock = threading.Lock()
    
    def sync_single(item):
        nonlocal synced, errors
        mal_id, extra_ids = item
        
        try:
            # skip_videos=True - video linkleri çekilmez!
            result = update_anime_by_mal_id(mal_id, extra_ids, skip_videos=True)
            with results_lock:
                if result:
                    synced += 1
                else:
                    errors += 1
            return result
        except Exception as e:
            print(f"[Sync] Hata ({mal_id}): {e}")
            with results_lock:
                errors += 1
            return False
    
    # Paralel senkronizasyon
    print(f"[Sync] {len(to_sync)} anime senkronize edilecek ({parallel} paralel)...")
    
    with ThreadPoolExecutor(max_workers=parallel) as executor:
        futures = [executor.submit(sync_single, item) for item in to_sync]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"[Sync] Future hatası: {e}")
    
    return jsonify({
        "success": True,
        "synced": synced,
        "errors": errors,
        "total": len(anime_list),
        "skipped": len(anime_list) - len(to_sync)
    })


# ─────────────────────────────────────────────────────────────────────────────
# AYRI SENKRONİZASYON ENDPOİNT'LERİ (PARALEL & YÜKSEK HIZLI)
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/sync/anime-info", methods=["POST"])
def api_sync_anime_info():
    """
    Sadece anime bilgilerini senkronize et (paralel - 30-50 eşzamanlı).
    
    Body:
    {
        "mal_ids": [1, 20, 21, ...],  // Belirli MAL ID'ler
        "year": 2024,                  // veya sezon
        "season": "winter",
        "batch_size": 50               // Paralel batch boyutu
    }
    """
    data = request.get_json() or {}
    mal_ids = data.get("mal_ids", [])
    year = data.get("year")
    season = data.get("season")
    batch_size = min(data.get("batch_size", 50), 100)  # Max 100 paralel
    
    # MAL ID listesi oluştur
    if not mal_ids and year and season:
        anime_list = fetch_all_season_anime(year, season)
        mal_ids = [a.get("mal_id") for a in anime_list if a.get("mal_id")]
    
    if not mal_ids:
        return jsonify({"error": "mal_ids veya year/season gerekli"}), 400
    
    results = {"success": 0, "failed": 0, "skipped": 0, "details": []}
    existing_ids = set(db.get_all_mal_ids())
    
    def sync_single_anime(mal_id: int) -> dict:
        """Tek anime bilgisini senkronize et."""
        try:
            if mal_id in existing_ids:
                return {"mal_id": mal_id, "status": "skipped", "reason": "exists"}
            
            # Jikan'dan bilgi çek
            jikan_data = main.fetch_anime_from_jikan(mal_id)
            if not jikan_data:
                return {"mal_id": mal_id, "status": "failed", "reason": "jikan_error"}
            
            # Parse et
            anime_data = main.parse_jikan_data(jikan_data)
            if not anime_data:
                return {"mal_id": mal_id, "status": "failed", "reason": "parse_error"}
            
            # DB'ye ekle (video olmadan)
            anime_id = db.insert_or_update_anime(anime_data)
            if not anime_id:
                return {"mal_id": mal_id, "status": "failed", "reason": "db_error"}
            
            # Türler, temalar vs.
            for genre in jikan_data.get("genres", []):
                genre_id = db.insert_or_get_genre(genre.get("mal_id", 0), genre.get("name", ""))
                if genre_id:
                    db.link_anime_genre(anime_id, genre_id)
            
            return {"mal_id": mal_id, "status": "success", "anime_id": anime_id}
            
        except Exception as e:
            return {"mal_id": mal_id, "status": "failed", "reason": str(e)}
    
    # Paralel işlem
    with ThreadPoolExecutor(max_workers=batch_size) as executor:
        futures = {executor.submit(sync_single_anime, mid): mid for mid in mal_ids}
        for future in as_completed(futures):
            try:
                result = future.result(timeout=60)
                results["details"].append(result)
                if result["status"] == "success":
                    results["success"] += 1
                elif result["status"] == "skipped":
                    results["skipped"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                mid = futures[future]
                results["failed"] += 1
                results["details"].append({"mal_id": mid, "status": "failed", "reason": str(e)})
    
    return jsonify(results)


@app.route("/api/sync/covers", methods=["POST"])
def api_sync_covers():
    """
    Sadece cover resimlerini indir (paralel - 50-100 eşzamanlı).
    
    Body:
    {
        "mal_ids": [1, 20, 21, ...],   // Belirli MAL ID'ler
        "missing_only": true,          // Sadece eksik olanlar
        "batch_size": 100              // Paralel batch boyutu
    }
    """
    data = request.get_json() or {}
    mal_ids = data.get("mal_ids", [])
    missing_only = data.get("missing_only", True)
    batch_size = min(data.get("batch_size", 100), 200)  # Max 200 paralel
    
    # Tüm anime'ler için cover sync
    if not mal_ids:
        conn = db.get_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            if missing_only:
                cursor.execute("SELECT mal_id, cover_url FROM animes WHERE cover_local IS NULL OR cover_local = ''")
            else:
                cursor.execute("SELECT mal_id, cover_url FROM animes WHERE cover_url IS NOT NULL")
            rows = cursor.fetchall()
            mal_ids = [(cast(Dict[str, Any], r)["mal_id"], cast(Dict[str, Any], r)["cover_url"]) for r in rows]
            cursor.close()
            conn.close()
    
    if not mal_ids:
        return jsonify({"error": "İndirilecek cover bulunamadı"}), 404
    
    results = {"success": 0, "failed": 0, "total": len(mal_ids)}
    
    def download_cover(item) -> bool:
        """Tek cover indir."""
        try:
            if isinstance(item, tuple):
                mal_id, cover_url = item
            else:
                mal_id = item
                anime = db.get_anime_by_mal_id(mal_id)
                if anime:
                    anime_dict = cast(Dict[str, Any], anime)
                    cover_url = anime_dict.get("cover_url")
                else:
                    cover_url = None
            
            if not cover_url:
                return False
            
            # İndir
            local_path = main.download_cover(str(cover_url), int(mal_id))
            if local_path:
                # DB güncelle
                conn = db.get_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE animes SET cover_local = %s WHERE mal_id = %s", (local_path, mal_id))
                    conn.commit()
                    cursor.close()
                    conn.close()
                return True
            return False
        except Exception:
            return False
    
    # Paralel indirme
    with ThreadPoolExecutor(max_workers=batch_size) as executor:
        futures = [executor.submit(download_cover, item) for item in mal_ids]
        for future in as_completed(futures):
            try:
                if future.result(timeout=30):
                    results["success"] += 1
                else:
                    results["failed"] += 1
            except Exception:
                results["failed"] += 1
    
    return jsonify(results)


@app.route("/api/sync/videos", methods=["POST"])
def api_sync_videos():
    """
    Video stream'lerini paralel senkronize et (30-100 eşzamanlı, tüm adapterlar).
    
    Body:
    {
        "mal_ids": [1, 20, 21, ...],   // Belirli MAL ID'ler
        "episodes": [1, 2, 3, ...],    // Belirli bölümler (opsiyonel)
        "adapters": ["anizle", "animecix", "tranime"],  // Kullanılacak adapterlar
        "batch_size": 50,              // Paralel batch boyutu
        "force": false                 // Var olanları güncelle
    }
    """
    data = request.get_json() or {}
    mal_ids = data.get("mal_ids", [])
    episodes = data.get("episodes", [])  # Boşsa tümü
    adapter_names = data.get("adapters", list(ADAPTERS.keys()))
    batch_size = min(data.get("batch_size", 50), 100)
    force = data.get("force", False)
    
    if not mal_ids:
        return jsonify({"error": "mal_ids gerekli"}), 400
    
    results = {
        "success": 0, 
        "failed": 0, 
        "videos_found": 0,
        "details": []
    }
    
    def fetch_videos_for_anime(mal_id: int) -> dict:
        """Tek anime için tüm bölüm videolarını çek."""
        anime = db.get_anime_by_mal_id(mal_id)
        if not anime:
            return {"mal_id": mal_id, "status": "failed", "reason": "anime_not_found"}
        
        anime_dict = cast(Dict[str, Any], anime)
        anime_db_id = int(anime_dict["id"])
        total_eps = anime_dict.get("episodes") or 24
        
        target_episodes = episodes if episodes else list(range(1, total_eps + 1))
        found_videos = 0
        
        # Kaynakları al
        conn = db.get_connection()
        if not conn:
            return {"mal_id": mal_id, "status": "failed", "reason": "db_error"}
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT asrc.source_slug, asrc.source_anime_id, s.name as source_name, s.id as source_tbl_id
            FROM anime_sources asrc 
            JOIN sources s ON asrc.source_id = s.id 
            WHERE asrc.anime_id = %s
        """, (anime_db_id,))
        sources = [cast(Dict[str, Any], r) for r in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        if not sources:
            return {"mal_id": mal_id, "status": "failed", "reason": "no_sources"}
        
        # Filtreleme
        sources = [s for s in sources if s["source_name"] in adapter_names]
        
        # Her bölüm için paralel fetch
        def fetch_episode_videos(ep_num: int) -> int:
            nonlocal found_videos
            try:
                ensure_episode_videos(mal_id, ep_num, anime_db_id)
                return 1
            except Exception:
                return 0
        
        with ThreadPoolExecutor(max_workers=min(len(target_episodes), 20)) as ep_executor:
            futures = [ep_executor.submit(fetch_episode_videos, ep) for ep in target_episodes]
            for f in as_completed(futures):
                found_videos += f.result()
        
        return {"mal_id": mal_id, "status": "success", "episodes_processed": len(target_episodes)}
    
    # Ana paralel işlem
    with ThreadPoolExecutor(max_workers=batch_size) as executor:
        futures = {executor.submit(fetch_videos_for_anime, mid): mid for mid in mal_ids}
        for future in as_completed(futures):
            try:
                result = future.result(timeout=300)  # 5 dk timeout
                results["details"].append(result)
                if result["status"] == "success":
                    results["success"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                mid = futures[future]
                results["failed"] += 1
                results["details"].append({"mal_id": mid, "status": "failed", "reason": str(e)})
    
    return jsonify(results)


@app.route("/api/sync/adapter/<adapter_name>", methods=["POST"])
def api_sync_single_adapter(adapter_name: str):
    """
    Tek bir adapter için toplu video sync (paralel).
    
    Body:
    {
        "mal_ids": [1, 20, 21, ...],
        "batch_size": 50
    }
    """
    if adapter_name not in ADAPTERS:
        return jsonify({"error": f"Bilinmeyen adapter: {adapter_name}"}), 400
    
    data = request.get_json() or {}
    mal_ids = data.get("mal_ids", [])
    batch_size = min(data.get("batch_size", 50), 100)
    
    results = {"adapter": adapter_name, "success": 0, "failed": 0}
    
    def process_anime_adapter(mal_id: int) -> bool:
        """Tek anime için belirli adapter'dan video çek."""
        try:
            anime = db.get_anime_by_mal_id(mal_id)
            if not anime:
                return False
            
            anime_dict = cast(Dict[str, Any], anime)
            anime_db_id = int(anime_dict["id"])
            
            # Bu adapter için kaynak var mı?
            conn = db.get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT asrc.source_slug, asrc.source_anime_id, s.id as source_tbl_id
                FROM anime_sources asrc 
                JOIN sources s ON asrc.source_id = s.id 
                WHERE asrc.anime_id = %s AND s.name = %s
            """, (anime_db_id, adapter_name))
            source = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not source:
                return False
            
            source_dict = cast(Dict[str, Any], source)
            
            # Tüm bölümleri çek
            total_eps = anime_dict.get("episodes") or 24
            for ep in range(1, total_eps + 1):
                ensure_episode_videos(mal_id, ep, anime_db_id)
            
            return True
        except Exception:
            return False
    
    with ThreadPoolExecutor(max_workers=batch_size) as executor:
        futures = [executor.submit(process_anime_adapter, mid) for mid in mal_ids]
        for future in as_completed(futures):
            if future.result():
                results["success"] += 1
            else:
                results["failed"] += 1
    
    return jsonify(results)


@app.route("/api/sync/batch", methods=["POST"])
def api_sync_batch():
    """
    Toplu senkronizasyon - anime bilgisi, cover ve video'yu birlikte.
    En hızlı paralel işlem (50-200 worker).
    
    Body:
    {
        "mal_ids": [1, 20, ...],
        "sync_info": true,
        "sync_covers": true,
        "sync_videos": true,
        "adapters": ["anizle", "animecix"],
        "workers": 100
    }
    """
    data = request.get_json() or {}
    mal_ids = data.get("mal_ids", [])
    sync_info = data.get("sync_info", True)
    sync_covers = data.get("sync_covers", True)
    sync_videos = data.get("sync_videos", True)
    adapter_names = data.get("adapters", list(ADAPTERS.keys()))
    workers = min(data.get("workers", 100), 200)
    
    if not mal_ids:
        return jsonify({"error": "mal_ids gerekli"}), 400
    
    results = {
        "total": len(mal_ids),
        "info": {"success": 0, "failed": 0},
        "covers": {"success": 0, "failed": 0},
        "videos": {"success": 0, "failed": 0}
    }
    
    existing_ids = set(db.get_all_mal_ids())
    
    def full_sync_anime(mal_id: int) -> dict:
        """Tek anime için tam senkronizasyon."""
        result = {"mal_id": mal_id, "info": False, "cover": False, "videos": False}
        
        try:
            # 1. Anime bilgisi
            if sync_info and mal_id not in existing_ids:
                jikan_data = main.fetch_anime_from_jikan(mal_id)
                if jikan_data:
                    anime_data = main.parse_jikan_data(jikan_data)
                    if anime_data:
                        anime_id = db.insert_or_update_anime(anime_data)
                        if anime_id:
                            result["info"] = True
                            
                            # Türler
                            for genre in jikan_data.get("genres", []):
                                gid = db.insert_or_get_genre(genre.get("mal_id", 0), genre.get("name", ""))
                                if gid:
                                    db.link_anime_genre(anime_id, gid)
            elif mal_id in existing_ids:
                result["info"] = True  # Zaten var
            
            # 2. Cover
            if sync_covers:
                anime = db.get_anime_by_mal_id(mal_id)
                if anime:
                    anime_dict = cast(Dict[str, Any], anime)
                    if anime_dict.get("cover_url") and not anime_dict.get("cover_local"):
                        local_path = main.download_cover(anime_dict["cover_url"], mal_id)
                        if local_path:
                            conn = db.get_connection()
                            if conn:
                                cursor = conn.cursor()
                                cursor.execute("UPDATE animes SET cover_local = %s WHERE mal_id = %s", 
                                             (local_path, mal_id))
                                conn.commit()
                                cursor.close()
                                conn.close()
                                result["cover"] = True
                    else:
                        result["cover"] = True  # Zaten var veya yok
            
            # 3. Video'lar
            if sync_videos:
                anime = db.get_anime_by_mal_id(mal_id)
                if anime:
                    anime_dict = cast(Dict[str, Any], anime)
                    anime_db_id = int(anime_dict["id"])
                    total_eps = anime_dict.get("episodes") or 12
                    
                    for ep in range(1, min(total_eps + 1, 50)):  # Max 50 bölüm
                        try:
                            ensure_episode_videos(mal_id, ep, anime_db_id)
                        except Exception:
                            pass
                    result["videos"] = True
            
            return result
            
        except Exception as e:
            return result
    
    # Büyük paralel işlem
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(full_sync_anime, mid) for mid in mal_ids]
        for future in as_completed(futures):
            try:
                r = future.result(timeout=300)
                if r["info"]:
                    results["info"]["success"] += 1
                else:
                    results["info"]["failed"] += 1
                if r["cover"]:
                    results["covers"]["success"] += 1
                else:
                    results["covers"]["failed"] += 1
                if r["videos"]:
                    results["videos"]["success"] += 1
                else:
                    results["videos"]["failed"] += 1
            except Exception:
                results["info"]["failed"] += 1
                results["covers"]["failed"] += 1
                results["videos"]["failed"] += 1
    
    return jsonify(results)


@app.route("/api/adapters/status")
def api_adapters_status():
    """Tüm adapter'ların durumunu göster."""
    status = {}
    
    for name, enabled in ADAPTERS.items():
        status[name] = {
            "enabled": enabled,
            "available": False
        }
        
        # Her adapter için basit test
        try:
            if name == "anizle":
                # Anizle test
                status[name]["available"] = len(anizle.load_anime_database()) > 0
            elif name == "animecix":
                # AnimeCiX test
                status[name]["available"] = True  # Basit
            elif name == "animely":
                # Animely test
                status[name]["available"] = len(animely.get_anime_list()) > 0
            elif name == "tranime":
                # TRAnime test
                status[name]["available"] = True
        except Exception:
            status[name]["available"] = False
    
    return jsonify({
        "adapters": status,
        "parallel_workers": PARALLEL_WORKERS,
        "video_workers": VIDEO_WORKERS
    })


# ─────────────────────────────────────────────────────────────────────────────
# VIDEO LİNK DOĞRULAMA VE TEMİZLEME ENDPOINTLERİ
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/validate/link", methods=["POST"])
def api_validate_single_link():
    """
    Tek bir video linkini doğrula.
    
    Body:
    {
        "url": "https://...",
        "remove_if_dead": false   // Ölüyse DB'den kaldır
    }
    
    Response:
    {
        "url": "...",
        "is_alive": true/false,
        "stream_info": {...} or null
    }
    """
    data = request.get_json() or {}
    url = data.get("url")
    remove_if_dead = data.get("remove_if_dead", False)
    
    if not url:
        return jsonify({"error": "URL gerekli"}), 400
    
    is_alive, stream_info = check_video_link_alive(url)
    
    result = {
        "url": url,
        "is_alive": is_alive,
        "stream_info": stream_info
    }
    
    # Eğer ölüyse ve remove_if_dead true ise DB'den kaldır
    if not is_alive and remove_if_dead:
        conn = db.get_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE video_links SET is_active = FALSE WHERE video_url = %s", (url,))
            affected = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            result["removed_count"] = affected
    
    return jsonify(result)


@app.route("/api/validate/anime/<int:mal_id>", methods=["POST"])
def api_validate_anime_links(mal_id: int):
    """
    Belirli anime'nin tüm video linklerini doğrula ve ölüleri kaldır.
    
    Body:
    {
        "episode": 1,              // Opsiyonel - belirli bölüm
        "parallel": 10,            // Paralel worker sayısı
        "remove_dead": true        // Ölü linkleri DB'den kaldır
    }
    
    Response:
    {
        "mal_id": 123,
        "total_checked": 50,
        "alive": 45,
        "dead": 5,
        "removed": 5 (if remove_dead)
    }
    """
    data = request.get_json() or {}
    episode = data.get("episode")
    parallel = min(data.get("parallel", 10), 50)
    remove_dead = data.get("remove_dead", True)
    
    anime = db.get_anime_by_mal_id(mal_id)
    if not anime:
        return jsonify({"error": "Anime bulunamadı"}), 404
    
    anime_dict = cast(Dict[str, Any], anime)
    anime_db_id = int(anime_dict["id"])
    
    # Video linklerini çek
    conn = db.get_connection()
    if not conn:
        return jsonify({"error": "DB bağlantı hatası"}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    if episode:
        cursor.execute("""
            SELECT vl.id, vl.video_url, vl.fansub, e.episode_number
            FROM video_links vl
            JOIN episodes e ON vl.episode_id = e.id
            WHERE e.anime_id = %s AND e.episode_number = %s AND vl.is_active = TRUE
        """, (anime_db_id, episode))
    else:
        cursor.execute("""
            SELECT vl.id, vl.video_url, vl.fansub, e.episode_number
            FROM video_links vl
            JOIN episodes e ON vl.episode_id = e.id
            WHERE e.anime_id = %s AND vl.is_active = TRUE
        """, (anime_db_id,))
    
    links = [cast(Dict[str, Any], r) for r in cursor.fetchall()]
    cursor.close()
    conn.close()
    
    if not links:
        return jsonify({
            "mal_id": mal_id,
            "total_checked": 0,
            "alive": 0,
            "dead": 0,
            "message": "Aktif video link bulunamadı"
        })
    
    alive_count = 0
    dead_count = 0
    dead_link_ids = []
    
    def check_link(link):
        is_alive, _ = check_video_link_alive(link["video_url"])
        return {
            "id": link["id"],
            "url": link["video_url"],
            "episode": link["episode_number"],
            "is_alive": is_alive
        }
    
    # Paralel kontrol
    with ThreadPoolExecutor(max_workers=parallel) as executor:
        futures = [executor.submit(check_link, l) for l in links]
        for future in as_completed(futures):
            result = future.result()
            if result["is_alive"]:
                alive_count += 1
            else:
                dead_count += 1
                dead_link_ids.append(result["id"])
    
    removed_count = 0
    
    # Ölü linkleri kaldır
    if remove_dead and dead_link_ids:
        conn = db.get_connection()
        if conn:
            cursor = conn.cursor()
            for link_id in dead_link_ids:
                cursor.execute("UPDATE video_links SET is_active = FALSE WHERE id = %s", (link_id,))
            conn.commit()
            removed_count = cursor.rowcount
            cursor.close()
            conn.close()
    
    return jsonify({
        "mal_id": mal_id,
        "total_checked": len(links),
        "alive": alive_count,
        "dead": dead_count,
        "removed": removed_count if remove_dead else 0
    })


@app.route("/api/validate/batch", methods=["POST"])
def api_validate_batch_links():
    """
    Toplu video link doğrulama (tüm DB veya belirli anime'ler).
    
    Body:
    {
        "mal_ids": [1, 20, 21],    // Opsiyonel - boş ise tümü
        "limit": 1000,             // Max kaç link kontrol edilsin
        "parallel": 30,            // Paralel worker sayısı
        "remove_dead": true        // Ölü linkleri DB'den kaldır
    }
    
    Response:
    {
        "total_checked": 1000,
        "alive": 950,
        "dead": 50,
        "removed": 50
    }
    """
    data = request.get_json() or {}
    mal_ids = data.get("mal_ids", [])
    limit = min(data.get("limit", 1000), 10000)  # Max 10K
    parallel = min(data.get("parallel", 30), 100)
    remove_dead = data.get("remove_dead", True)
    
    conn = db.get_connection()
    if not conn:
        return jsonify({"error": "DB bağlantı hatası"}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    if mal_ids:
        # Belirli anime'ler
        placeholders = ",".join(["%s"] * len(mal_ids))
        cursor.execute(f"""
            SELECT vl.id, vl.video_url, a.mal_id
            FROM video_links vl
            JOIN episodes e ON vl.episode_id = e.id
            JOIN animes a ON e.anime_id = a.id
            WHERE a.mal_id IN ({placeholders}) AND vl.is_active = TRUE
            LIMIT %s
        """, (*mal_ids, limit))
    else:
        # Tüm aktif linkler
        cursor.execute("""
            SELECT vl.id, vl.video_url, a.mal_id
            FROM video_links vl
            JOIN episodes e ON vl.episode_id = e.id
            JOIN animes a ON e.anime_id = a.id
            WHERE vl.is_active = TRUE
            ORDER BY vl.updated_at ASC
            LIMIT %s
        """, (limit,))
    
    links = [cast(Dict[str, Any], r) for r in cursor.fetchall()]
    cursor.close()
    conn.close()
    
    if not links:
        return jsonify({
            "total_checked": 0,
            "alive": 0,
            "dead": 0,
            "removed": 0,
            "message": "Kontrol edilecek link bulunamadı"
        })
    
    alive_count = 0
    dead_count = 0
    dead_link_ids = []
    
    def check_link(link):
        is_alive, _ = check_video_link_alive(link["video_url"], timeout=10)
        return {"id": link["id"], "is_alive": is_alive}
    
    # Paralel kontrol
    print(f"[LinkValidation] {len(links)} link kontrol ediliyor ({parallel} paralel)...")
    
    with ThreadPoolExecutor(max_workers=parallel) as executor:
        futures = [executor.submit(check_link, l) for l in links]
        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            if result["is_alive"]:
                alive_count += 1
            else:
                dead_count += 1
                dead_link_ids.append(result["id"])
            
            # Progress log
            if (i + 1) % 100 == 0:
                print(f"[LinkValidation] İlerleme: {i+1}/{len(links)} (Canlı: {alive_count}, Ölü: {dead_count})")
    
    removed_count = 0
    
    # Ölü linkleri kaldır
    if remove_dead and dead_link_ids:
        conn = db.get_connection()
        if conn:
            cursor = conn.cursor()
            for link_id in dead_link_ids:
                cursor.execute("UPDATE video_links SET is_active = FALSE WHERE id = %s", (link_id,))
            conn.commit()
            removed_count = len(dead_link_ids)
            cursor.close()
            conn.close()
            print(f"[LinkValidation] {removed_count} ölü link pasif yapıldı")
    
    return jsonify({
        "total_checked": len(links),
        "alive": alive_count,
        "dead": dead_count,
        "removed": removed_count if remove_dead else 0
    })


@app.route("/api/cleanup/dead-links", methods=["POST"])
def api_cleanup_dead_links():
    """
    Ölü olarak işaretlenmiş linkleri kalıcı olarak sil.
    
    Body:
    {
        "permanent": false,        // True ise tamamen sil, false ise sadece say
        "older_than_days": 7       // X günden önce pasif yapılmış olanlar
    }
    """
    data = request.get_json() or {}
    permanent = data.get("permanent", False)
    older_than_days = data.get("older_than_days", 7)
    
    conn = db.get_connection()
    if not conn:
        return jsonify({"error": "DB bağlantı hatası"}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    # Kaç tane ölü link var?
    cursor.execute("""
        SELECT COUNT(*) as count FROM video_links 
        WHERE is_active = FALSE 
        AND updated_at < DATE_SUB(NOW(), INTERVAL %s DAY)
    """, (older_than_days,))
    
    result = cast(Dict[str, Any], cursor.fetchone())
    dead_count = int(result["count"])
    
    deleted_count = 0
    
    if permanent and dead_count > 0:
        cursor.execute("""
            DELETE FROM video_links 
            WHERE is_active = FALSE 
            AND updated_at < DATE_SUB(NOW(), INTERVAL %s DAY)
        """, (older_than_days,))
        conn.commit()
        deleted_count = cursor.rowcount
        print(f"[Cleanup] {deleted_count} ölü link kalıcı olarak silindi")
    
    cursor.close()
    conn.close()
    
    return jsonify({
        "dead_links_found": dead_count,
        "deleted": deleted_count if permanent else 0,
        "message": f"{dead_count} ölü link bulundu" + (f", {deleted_count} kalıcı olarak silindi" if permanent else "")
    })


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"""
╔════════════════════════════════════════════════════════════╗
║           🎬 Anime Offline DB - Web API                     ║
╠════════════════════════════════════════════════════════════╣
║  http://{API_HOST}:{API_PORT}/                              ║
║  http://{API_HOST}:{API_PORT}/player?mal_id=1               ║
║  http://{API_HOST}:{API_PORT}/api/stream/1/1                ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    app.run(host=API_HOST, port=API_PORT, debug=True, threaded=True)
