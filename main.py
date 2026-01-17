#!/usr/bin/env python3
"""
Anime Offline Database Manager

Usage:
    python main.py --init                      # Initialize database
    python main.py --update "Naruto"           # Update by title
    python main.py --mal_id 20                 # Update by MAL ID
    python main.py --bulk                      # Bulk update from anime_ids.json
    python main.py --bulk --limit 100          # Update first 100 animes
    python main.py --videos 20                 # Show video links for MAL ID
"""

import argparse
import json
import os
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, Optional, cast

import requests

# Project modules
from config import (
    COVER_DIR, UPDATED_IDS_FILE, ADAPTERS, HTTP_TIMEOUT
)
import db
from jikan_client import jikan

# Adapters
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adapters import animecix, animely, anizle, tranime, turkanime


# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def load_anime_ids() -> dict:
    """Load anime_ids.json file."""
    try:
        with open("anime_ids.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("[ERROR] anime_ids.json not found!")
        return {}
    except json.JSONDecodeError:
        print("[ERROR] anime_ids.json invalid JSON!")
        return {}


def load_updated_ids() -> set:
    """Load updated MAL IDs."""
    try:
        with open(UPDATED_IDS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def save_updated_ids(updated_ids: set):
    """Save updated MAL IDs."""
    with open(UPDATED_IDS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(updated_ids), f)


def download_cover(url: str, mal_id: int) -> str:
    """Download cover image and return local path."""
    if not url:
        return ""

    Path(COVER_DIR).mkdir(parents=True, exist_ok=True)

    ext = url.split(".")[-1].split("?")[0]
    if ext not in ["jpg", "jpeg", "png", "webp"]:
        ext = "jpg"

    local_path = f"{COVER_DIR}/{mal_id}.{ext}"

    try:
        response = requests.get(url, timeout=HTTP_TIMEOUT)
        response.raise_for_status()

        with open(local_path, "wb") as f:
            f.write(response.content)

        return local_path
    except Exception as e:
        print(f"[ERROR] Could not download cover ({mal_id}): {e}")
        return ""


def similarity_score(query: str, text: str) -> float:
    """Calculate similarity score between two strings."""
    if not text:
        return 0.0
    query_lower = query.lower()
    text_lower = text.lower()

    if query_lower == text_lower:
        return 1.0
    if query_lower in text_lower:
        return 0.9

    return SequenceMatcher(None, query_lower, text_lower).ratio()


def parse_jikan_data(jikan_data: dict, extra_ids: Optional[Dict[str, Any]] = None) -> dict:
    """Convert Jikan data to database format."""
    if not jikan_data:
        return {}

    # Airing dates
    aired = jikan_data.get("aired", {}) or {}
    aired_from = aired.get("from")
    aired_to = aired.get("to")

    if aired_from:
        aired_from = aired_from[:10]  # YYYY-MM-DD
    if aired_to:
        aired_to = aired_to[:10]

    # Broadcast
    broadcast_data = jikan_data.get("broadcast", {}) or {}
    broadcast = broadcast_data.get("string", "")

    # Trailer
    trailer_data = jikan_data.get("trailer", {}) or {}
    trailer_url = trailer_data.get("embed_url", "")

    # Cover
    images = jikan_data.get("images", {}) or {}
    jpg_images = images.get("jpg", {}) or {}
    cover_url = jpg_images.get("large_image_url") or jpg_images.get("image_url", "")

    anime_data = {
        "mal_id": jikan_data.get("mal_id"),
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
        "broadcast": broadcast,
        "cover_url": cover_url,
        "trailer_url": trailer_url,
    }

    # Extra IDs (from anime_ids.json)
    if extra_ids:
        anime_data["anidb_id"] = extra_ids.get("anidb_id")
        anime_data["anilist_id"] = extra_ids.get("anilist_id")
        anime_data["tvdb_id"] = extra_ids.get("tvdb_id")
        anime_data["imdb_id"] = extra_ids.get("imdb_id")

    return anime_data


def get_jikan_related_data(jikan_data: dict) -> dict:
    """Extract related data from Jikan response (genres, themes, studios, etc.)."""
    return {
        "titles": jikan_data.get("titles", []),
        "genres": jikan_data.get("genres", []),
        "themes": jikan_data.get("themes", []),
        "studios": jikan_data.get("studios", []),
        "producers": jikan_data.get("producers", []),
        "licensors": jikan_data.get("licensors", []),
    }


# ─────────────────────────────────────────────────────────────────────────────
# ADAPTER OPERATIONS
# ─────────────────────────────────────────────────────────────────────────────

def search_in_single_adapter(adapter_func, adapter_name, search_terms, threshold=0.5):
    """Search in a single adapter and return the best match."""
    if not ADAPTERS.get(adapter_name):
        return None
    
    try:
        for term in search_terms:
            try:
                results = adapter_func(term)
                if results:
                    # Find best match for current term
                    best_score = 0
                    best_match = None
                    for result in results:
                        score = similarity_score(term, result[1])
                        if score > best_score:
                            best_score = score
                            best_match = result
                    if best_score > threshold:
                        return best_match
            except Exception:
                continue
    except Exception as e:
        print(f"[{adapter_name}] Search error: {e}")
    
    return None


def create_romanji_from_japanese(japanese_text: str) -> str:
    """
    Basit Romanji dönüşümü (hiragana/katakana -> romanji).
    Bu tam doğru değil ama temel dönüşümler yapar.
    """
    if not japanese_text:
        return ""
    
    # Hiragana -> romanji mapping
    hiragana_map = {
        'あ': 'a', 'い': 'i', 'う': 'u', 'え': 'e', 'お': 'o',
        'か': 'ka', 'き': 'ki', 'く': 'ku', 'け': 'ke', 'こ': 'ko',
        'さ': 'sa', 'し': 'shi', 'す': 'su', 'せ': 'se', 'そ': 'so',
        'た': 'ta', 'ち': 'chi', 'つ': 'tsu', 'て': 'te', 'と': 'to',
        'な': 'na', 'に': 'ni', 'ぬ': 'nu', 'ね': 'ne', 'の': 'no',
        'は': 'ha', 'ひ': 'hi', 'ふ': 'fu', 'へ': 'he', 'ほ': 'ho',
        'ま': 'ma', 'み': 'mi', 'む': 'mu', 'め': 'me', 'も': 'mo',
        'や': 'ya', 'ゆ': 'yu', 'よ': 'yo',
        'ら': 'ra', 'り': 'ri', 'る': 'ru', 'れ': 're', 'ろ': 'ro',
        'わ': 'wa', 'を': 'wo', 'ん': 'n',
        'が': 'ga', 'ぎ': 'gi', 'ぐ': 'gu', 'げ': 'ge', 'ご': 'go',
        'ざ': 'za', 'じ': 'ji', 'ず': 'zu', 'ぜ': 'ze', 'ぞ': 'zo',
        'だ': 'da', 'ぢ': 'ji', 'づ': 'zu', 'で': 'de', 'ど': 'do',
        'ば': 'ba', 'び': 'bi', 'ぶ': 'bu', 'べ': 'be', 'ぼ': 'bo',
        'ぱ': 'pa', 'ぴ': 'pi', 'ぷ': 'pu', 'ぺ': 'pe', 'ぽ': 'po',
        'ゃ': 'ya', 'ゅ': 'yu', 'ょ': 'yo', 'っ': 'tsu', 'ー': '-'
    }
    
    # Katakana -> romanji mapping (hiragana'ya dönüştürüp map et)
    katakana_map = {}
    for hira, roma in hiragana_map.items():
        kata = chr(ord(hira) + 0x60)  # Hiragana -> Katakana
        katakana_map[kata] = roma
    
    # Combine maps
    char_map = {**hiragana_map, **katakana_map}
    
    result = ""
    for char in japanese_text:
        if char in char_map:
            result += char_map[char]
        elif char.isalnum() or char in [' ', '-']:
            result += char
        # Diğer karakterleri ignore et
    
    return result.strip()


def search_in_adapters(title: Optional[str], title_english: Optional[str] = None, title_japanese: Optional[str] = None) -> dict:
    """
    Search anime in all adapters with multi-language support.
    Returns: {adapter_name: (source_id, source_slug, source_title)}
    
    Search priority by adapter:
    - AnimeCiX: Romanji (title) -> English -> Japanese
    - Anizle: Romanji (title) -> Japanese -> English  
    - TRAnime: English -> Romanji (title) -> Japanese
    - TurkAnime: Romanji (title) -> English -> Japanese
    """
    results = {}
    
    # Romanji (title), English, Japanese
    romanji = title
    english = title_english  
    japanese = title_japanese
    
    # Eğer Romanji yoksa Japanese'dan oluşturmaya çalış
    if not romanji and japanese:
        romanji = create_romanji_from_japanese(japanese)
    
    if not any([romanji, english, japanese]):
        return results

    # AnimeCiX - Prefers Romanji/English
    search_terms_cix = [t for t in [romanji, english, japanese] if t]
    match = search_in_single_adapter(animecix.search_animecix, "animecix", search_terms_cix)
    if match:
        results["animecix"] = (match[0], match[0], match[1])

    # Anizle - Prefers Romanji/Japanese
    search_terms_anizle = [t for t in [romanji, japanese, english] if t]
    match = search_in_single_adapter(lambda term: anizle.search_anizle(term, limit=10, timeout=10), "anizle", search_terms_anizle)
    if match:
        results["anizle"] = (match[0], match[0], match[1])

    # TRAnime - Prefers English/Romanji
    search_terms_tranime = [t for t in [english, romanji, japanese] if t]
    match = search_in_single_adapter(lambda term: tranime.search_tranime(term, limit=10), "tranime", search_terms_tranime)
    if match:
        results["tranime"] = (match[0], match[0], match[1])

    # TurkAnime - Prefers Romanji
    if ADAPTERS.get("turkanime"):
        search_terms_turk = [t for t in [romanji, english, japanese] if t]
        try:
            for term in search_terms_turk:
                try:
                    ta_results = turkanime.search_anime(term)
                    if ta_results:
                        best_score = 0
                        best_match = None
                        for result in ta_results:
                            score = similarity_score(term, result[2])
                            if score > best_score:
                                best_score = score
                                best_match = result
                        if best_score > 0.5:
                            results["turkanime"] = (best_match[0], best_match[1], best_match[2])
                            break
                except Exception:
                    break
        except Exception as e:
            print(f"[TurkAnime] Search error: {e}")

    return results


def fetch_episodes_from_animecix(source_id: str) -> list:
    """Fetch episodes and video links from AnimeCiX."""
    try:
        anime = animecix.CixAnime(id=source_id, title="")
        episodes = anime.episodes

        result = []
        for i, ep in enumerate(episodes):
            ep_num = i + 1
            match = re.search(r'(\d+)\.?\s*[Bb]ölüm', ep.title)
            if match:
                ep_num = int(match.group(1))

            videos = []
            if ep.url:
                try:
                    streams = animecix._video_streams(ep.url)
                    for stream in streams:
                        videos.append({
                            "url": stream.get("url", ""),
                            "quality": stream.get("label", "default"),
                            "fansub": "AnimeCiX"
                        })
                except Exception as ve:
                    print(f"[AnimeCiX] Video fetch error ({ep_num}): {ve}")

            result.append({
                "number": ep_num,
                "title": ep.title,
                "url": ep.url,
                "videos": videos
            })
        return result
    except Exception as e:
        print(f"[AnimeCiX] Episode fetch error: {e}")
        return []


def fetch_episodes_from_anizle(slug: str) -> list:
    """Fetch episodes and video links from Anizle."""
    try:
        episodes = anizle.get_anime_episodes(slug)

        result = []
        for ep_slug, ep_title in episodes:
            match = re.search(r'-(\d+)-bolum', ep_slug)
            ep_num = int(match.group(1)) if match else 0

            videos = []
            try:
                streams = anizle.get_episode_streams(ep_slug)
                for stream in streams:
                    url = stream.get("url") or stream.get("videoUrl", "")
                    if url:
                        label = stream.get("label", "")
                        fansub = "Anizle"
                        quality = "default"
                        if " - " in label:
                            parts = label.split(" - ", 1)
                            fansub = parts[0]
                            quality = parts[1] if len(parts) > 1 else "default"
                        else:
                            quality = label or "default"

                        videos.append({
                            "url": url,
                            "quality": quality,
                            "fansub": fansub
                        })
            except Exception as ve:
                print(f"[Anizle] Video fetch error ({ep_num}): {ve}")

            result.append({
                "number": ep_num,
                "title": ep_title,
                "slug": ep_slug,
                "videos": videos
            })
        return result
    except Exception as e:
        print(f"[Anizle] Episode fetch error: {e}")
        return []


# ─────────────────────────────────────────────────────────────────────────────
# CORE UPDATE FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def update_anime_by_mal_id(mal_id: int, extra_ids: Optional[Dict[str, Any]] = None, skip_videos: bool = True) -> bool:
    """
    Update anime by MAL ID.

    1. Fetch anime info from Jikan API
    2. Download cover image
    3. Save to database
    4. Save related data (genres, themes, studios)
    5. Fetch and save episode list from Jikan
    6. Search and link adapters (without fetching videos)
    """
    print(f"\n[{mal_id}] Updating...")

    jikan_data = jikan.get_anime(mal_id)
    if not jikan_data:
        print(f"[{mal_id}] Anime not found!")
        return False

    anime_data = parse_jikan_data(jikan_data, extra_ids or {})
    related_data = get_jikan_related_data(jikan_data)

    cover_url = anime_data.get("cover_url")
    if cover_url:
        local_cover = download_cover(cover_url, mal_id)
        anime_data["cover_local"] = local_cover
        print(f"[{mal_id}] Cover downloaded: {local_cover}")

    anime_id = db.insert_or_update_anime(anime_data)
    if not anime_id:
        print(f"[{mal_id}] Database save error!")
        return False

    print(f"[{mal_id}] {anime_data.get('title')} - DB ID: {anime_id}")

    # Related data
    if related_data.get("titles"):
        db.insert_anime_titles(anime_id, related_data["titles"])

    for genre in related_data.get("genres", []):
        genre_id = db.insert_or_get_genre(genre.get("name"))
        if genre_id:
            db.link_anime_genre(anime_id, genre_id)

    for theme in related_data.get("themes", []):
        theme_id = db.insert_or_get_theme(theme.get("name"))
        if theme_id:
            db.link_anime_theme(anime_id, theme_id)

    for studio in related_data.get("studios", []):
        studio_id = db.insert_or_get_studio(studio.get("name"))
        if studio_id:
            db.link_anime_studio(anime_id, studio_id)

    for producer in related_data.get("producers", []):
        producer_id = db.insert_or_get_producer(producer.get("name"))
        if producer_id:
            db.link_anime_producer(anime_id, producer_id, "producer")

    for licensor in related_data.get("licensors", []):
        licensor_id = db.insert_or_get_producer(licensor.get("name"))
        if licensor_id:
            db.link_anime_producer(anime_id, licensor_id, "licensor")

    # Fetch episodes from Jikan
    total_episodes = jikan_data.get("episodes") or 0
    print(f"[{mal_id}] Fetching episodes...")
    episodes = jikan.get_anime_episodes(mal_id)

    if episodes:
        for ep in episodes:
            ep_num = ep.get("mal_id")
            ep_title = ep.get("title") or ep.get("title_japanese") or f"Episode {ep_num}"
            if ep_num:
                db.insert_or_update_episode(anime_id, ep_num, ep_title)
        print(f"[{mal_id}] ✓ {len(episodes)} episodes saved")
    elif total_episodes > 0:
        print(f"[{mal_id}] No episode details, creating {total_episodes} placeholders...")
        for ep_num in range(1, total_episodes + 1):
            db.insert_or_update_episode(anime_id, ep_num, f"Episode {ep_num}")
        print(f"[{mal_id}] ✓ {total_episodes} episodes created")

    # Search in adapters
    print(f"[{mal_id}] Searching in adapters...")
    adapter_matches = search_in_adapters(
        anime_data.get("title"),
        anime_data.get("title_english"),
        anime_data.get("title_japanese")
    )

    for adapter_name, (source_anime_id, source_slug, source_title) in adapter_matches.items():
        print(f"[{mal_id}] {adapter_name}: {source_title}")
        source_id = db.get_source_id(adapter_name)
        if source_id and source_anime_id:  # source_anime_id None değilse kaydet
            db.insert_or_update_anime_source(anime_id, source_id, source_anime_id, source_slug, source_title)

    print(f"[{mal_id}] ✓ Anime info, cover and episodes saved.")
    return True


def update_anime_by_title(title: str) -> bool:
    """Update anime by searching title."""
    print(f"\nSearching: {title}")
    anime_ids = load_anime_ids()

    try:
        results = jikan.search_anime(title)
        if not results:
            print(f"'{title}' not found!")
            return False

        if len(results) == 1:
            selected = results[0]
        else:
            print("\nFound results:")
            for i, anime in enumerate(results):
                print(f"  {i+1}. [{anime.get('mal_id')}] {anime.get('title')}")

            choice = input("\nChoice (1-5, default 1): ").strip()
            idx = int(choice) - 1 if choice.isdigit() else 0
            selected = results[max(0, min(idx, len(results)-1))]

        mal_id = selected.get("mal_id")
        print(f"\nSelected: [{mal_id}] {selected.get('title')}")

        extra_ids = None
        for anidb_id, ids in anime_ids.items():
            if ids.get("mal_id") == mal_id:
                extra_ids = {
                    "anidb_id": int(anidb_id),
                    "anilist_id": ids.get("anilist_id"),
                    "tvdb_id": ids.get("tvdb_id"),
                    "imdb_id": ids.get("imdb_id")
                }
                break

        return update_anime_by_mal_id(mal_id, extra_ids)

    except Exception as e:
        print(f"Search error: {e}")
        return False


def update_anime_by_mal_id(mal_id: int, extra_ids: Optional[Dict[str, Any]] = None) -> bool:
    """Update anime by MAL ID."""
    print(f"\nUpdating: [{mal_id}]")

    try:
        # Fetch from Jikan
        jikan_data = jikan.get_anime(mal_id)
        if not jikan_data:
            print(f"[{mal_id}] Jikan data not found!")
            return False

        anime_data = parse_jikan_data(jikan_data, extra_ids)
        related_data = get_jikan_related_data(jikan_data)

        if not anime_data:
            print(f"[{mal_id}] Parse error!")
            return False

        # Download cover
        cover_url = anime_data.get("cover_url")
        if cover_url:
            local_cover = download_cover(cover_url, mal_id)
            anime_data["cover_local"] = local_cover
            print(f"[{mal_id}] Cover downloaded: {local_cover}")

        anime_id = db.insert_or_update_anime(anime_data)
        if not anime_id:
            print(f"[{mal_id}] Database save error!")
            return False

        print(f"[{mal_id}] {anime_data.get('title')} - DB ID: {anime_id}")

        # Related data
        if related_data.get("titles"):
            db.insert_anime_titles(anime_id, related_data["titles"])

        for genre in related_data.get("genres", []):
            genre_id = db.insert_or_get_genre(genre.get("name"))
            if genre_id:
                db.link_anime_genre(anime_id, genre_id)

        for theme in related_data.get("themes", []):
            theme_id = db.insert_or_get_theme(theme.get("name"))
            if theme_id:
                db.link_anime_theme(anime_id, theme_id)

        for studio in related_data.get("studios", []):
            studio_id = db.insert_or_get_studio(studio.get("name"))
            if studio_id:
                db.link_anime_studio(anime_id, studio_id)

        for producer in related_data.get("producers", []):
            producer_id = db.insert_or_get_producer(producer.get("name"))
            if producer_id:
                db.link_anime_producer(anime_id, producer_id, "producer")

        for licensor in related_data.get("licensors", []):
            licensor_id = db.insert_or_get_producer(licensor.get("name"))
            if licensor_id:
                db.link_anime_producer(anime_id, licensor_id, "licensor")

        # Fetch episodes from Jikan
        total_episodes = jikan_data.get("episodes") or 0
        print(f"[{mal_id}] Fetching episodes...")
        episodes = jikan.get_anime_episodes(mal_id)

        if episodes:
            for ep in episodes:
                ep_num = ep.get("mal_id")
                ep_title = ep.get("title") or ep.get("title_japanese") or f"Episode {ep_num}"
                if ep_num:
                    db.insert_or_update_episode(anime_id, ep_num, ep_title)
            print(f"[{mal_id}] ✓ {len(episodes)} episodes saved")
        elif total_episodes > 0:
            print(f"[{mal_id}] No episode details, creating {total_episodes} placeholders...")
            for ep_num in range(1, total_episodes + 1):
                db.insert_or_update_episode(anime_id, ep_num, f"Episode {ep_num}")
            print(f"[{mal_id}] ✓ {total_episodes} episodes created")

        # Search in adapters
        print(f"[{mal_id}] Searching in adapters...")
        adapter_matches = search_in_adapters(
            anime_data.get("title"),
            anime_data.get("title_english"),
            anime_data.get("title_japanese")
        )

        for adapter_name, (source_anime_id, source_slug, source_title) in adapter_matches.items():
            print(f"[{mal_id}] {adapter_name}: {source_title}")
            source_id = db.get_source_id(adapter_name)
            if source_id and source_anime_id:  # source_anime_id None değilse kaydet
                db.insert_or_update_anime_source(anime_id, source_id, source_anime_id, source_slug, source_title)

        print(f"[{mal_id}] ✓ Anime info, cover and episodes saved.")
        return True

    except Exception as e:
        print(f"[{mal_id}] Update error: {e}")
        return False


def bulk_update(limit: Optional[int] = None, skip_updated: bool = True, parallel: int = 10):
    """Bulk update from anime_ids.json (PARALLEL)."""
    anime_ids = load_anime_ids()
    updated_ids = load_updated_ids() if skip_updated else set()

    to_update = []
    for anidb_id, ids in anime_ids.items():
        mal_id = ids.get("mal_id")
        if mal_id and mal_id not in updated_ids:
            to_update.append((mal_id, {
                "anidb_id": int(anidb_id),
                "anilist_id": ids.get("anilist_id"),
                "tvdb_id": ids.get("tvdb_id"),
                "imdb_id": ids.get("imdb_id")
            }))

    if limit:
        to_update = to_update[:int(limit)]

    print(f"Total to update: {len(to_update)}")

    success_count = 0
    fail_count = 0
    processed = 0
    lock = threading.Lock()

    def update_single(item):
        nonlocal success_count, fail_count, processed, updated_ids
        mal_id, extra_ids = item
        try:
            result = update_anime_by_mal_id(mal_id, extra_ids)
            with lock:
                processed += 1
                if result:
                    updated_ids.add(mal_id)
                    success_count += 1
                else:
                    fail_count += 1
                if processed % 10 == 0:
                    save_updated_ids(updated_ids)
            return result
        except Exception:
            with lock:
                processed += 1
                fail_count += 1
            return False

    with ThreadPoolExecutor(max_workers=min(parallel, 50)) as executor:
        executor.map(update_single, to_update)

    save_updated_ids(updated_ids)
    print(f"\nDone! Success: {success_count}, Failed: {fail_count}")


def show_video_links(mal_id: int):
    """Show video links for a specific anime."""
    anime_row = db.get_anime_by_mal_id(mal_id)
    if not anime_row:
        print(f"MAL ID {mal_id} not found in DB!")
        return

    anime = dict(anime_row)
    anime_id = int(anime["id"])
    print(f"\n{anime['title']} (MAL: {mal_id})")
    print("=" * 60)

    videos = db.get_video_links(anime_id=anime_id)
    if not videos:
        print("No video links found!")
        return

    current_episode = None
    for v in videos:
        if v["episode_number"] != current_episode:
            current_episode = v["episode_number"]
            print(f"\nEpisode {v['episode_number']}")
            print("-" * 40)
        print(f"  [{v.get('source_name', 'unknown')}] {v.get('fansub', 'unknown')} ({v.get('quality', 'default')})")
        print(f"    {str(v['url'])[:80]}...")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Anime Offline Database Manager")

    parser.add_argument("--init", action="store_true", help="Initialize database")
    parser.add_argument("--update", type=str, metavar="TITLE", help="Update by title")
    parser.add_argument("--mal_id", type=int, metavar="ID", help="Update by MAL ID")
    parser.add_argument("--bulk", action="store_true", help="Bulk update from anime_ids.json")
    parser.add_argument("--limit", type=int, help="Limit for bulk update")
    parser.add_argument("--parallel", type=int, default=10, help="Parallel workers")
    parser.add_argument("--videos", type=int, metavar="MAL_ID", help="Show video links")
    parser.add_argument("--reset", action="store_true", help="Reset updated list")
    parser.add_argument("--retry", action="store_true", help="Retry updated animes")

    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        return

    if args.init:
        db.init_database()
        return

    if args.reset:
        if os.path.exists(UPDATED_IDS_FILE):
            os.remove(UPDATED_IDS_FILE)
            print("Reset complete.")
        return

    if args.update:
        update_anime_by_title(args.update)
        return

    if args.mal_id:
        anime_ids = load_anime_ids()
        extra_ids = None
        for anidb_id, ids in anime_ids.items():
            if ids.get("mal_id") == args.mal_id:
                extra_ids = {
                    "anidb_id": int(anidb_id),
                    "anilist_id": ids.get("anilist_id"),
                    "tvdb_id": ids.get("tvdb_id"),
                    "imdb_id": ids.get("imdb_id")
                }
                break
        update_anime_by_mal_id(args.mal_id, extra_ids)
        return

    if args.bulk:
        bulk_update(limit=args.limit, skip_updated=not args.retry, parallel=args.parallel)
        return

    if args.videos:
        show_video_links(args.videos)
        return


if __name__ == "__main__":
    main()
