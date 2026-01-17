#!/usr/bin/env python3
"""
Anime Offline Veritabanı Yöneticisi

Kullanım:
    python main.py --init                      # Veritabanını başlat
    python main.py --guncelle "Naruto"         # İsme göre güncelle
    python main.py --mal_id 20                 # MAL ID'ye göre güncelle
    python main.py --toplu                     # anime_ids.json'dan toplu güncelle
    python main.py --toplu --limit 100         # İlk 100 anime'yi güncelle
    python main.py --videolar 20               # MAL ID için video linklerini göster
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

# Proje modülleri
from config import (
    COVER_DIR, UPDATED_IDS_FILE, ADAPTERS, HTTP_TIMEOUT
)
import db
from jikan_client import jikan

# Adaptörler
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adapters import animecix, animely, anizle, tranime, turkanime


# ─────────────────────────────────────────────────────────────────────────────
# YARDIMCI FONKSİYONLAR
# ─────────────────────────────────────────────────────────────────────────────

def load_anime_ids() -> dict:
    """anime_ids.json dosyasını yükle."""
    try:
        with open("anime_ids.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("[HATA] anime_ids.json bulunamadı!")
        return {}
    except json.JSONDecodeError:
        print("[HATA] anime_ids.json geçersiz JSON!")
        return {}


def load_updated_ids() -> set:
    """Güncellenen MAL ID'lerini yükle."""
    try:
        with open(UPDATED_IDS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def save_updated_ids(updated_ids: set):
    """Güncellenen MAL ID'lerini kaydet."""
    with open(UPDATED_IDS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(updated_ids), f)


def download_cover(url: str, mal_id: int) -> str:
    """Cover resmini indir ve yerel yolu döndür."""
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
        print(f"[HATA] Cover indirilemedi ({mal_id}): {e}")
        return ""


def similarity_score(query: str, text: str) -> float:
    """İki metin arasındaki benzerlik skorunu hesapla."""
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
    """Jikan verisini veritabanı formatına dönüştür."""
    if not jikan_data:
        return {}

    # Yayın tarihleri
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

    # Extra ID'ler (anime_ids.json'dan)
    if extra_ids:
        anime_data["anidb_id"] = extra_ids.get("anidb_id")
        anime_data["anilist_id"] = extra_ids.get("anilist_id")
        anime_data["tvdb_id"] = extra_ids.get("tvdb_id")
        anime_data["imdb_id"] = extra_ids.get("imdb_id")

    return anime_data


def get_jikan_related_data(jikan_data: dict) -> dict:
    """Jikan verisinden ilişkili verileri çıkar (türler, temalar, stüdyolar, vb.)."""
    return {
        "titles": jikan_data.get("titles", []),
        "genres": jikan_data.get("genres", []),
        "themes": jikan_data.get("themes", []),
        "studios": jikan_data.get("studios", []),
        "producers": jikan_data.get("producers", []),
        "licensors": jikan_data.get("licensors", []),
    }


# ─────────────────────────────────────────────────────────────────────────────
# ADAPTÖR İŞLEMLERİ
# ─────────────────────────────────────────────────────────────────────────────

def search_in_single_adapter(adapter_func, adapter_name, search_terms, threshold=0.5):
    """Tek bir adaptörde arama yap ve en iyi sonucu döndür."""
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
        print(f"[{adapter_name}] Arama hatası: {e}")
    
    return None


def search_in_adapters(title: Optional[str], title_english: Optional[str] = None, title_japanese: Optional[str] = None) -> dict:
    """
    Tüm adaptörlerde anime ara.
    Returns: {adapter_name: (source_id, source_slug, source_title)}
    """
    results = {}
    search_terms = [t for t in [title, title_english, title_japanese] if t]

    if not search_terms:
        return results

    # AnimeCiX
    match = search_in_single_adapter(animecix.search_animecix, "animecix", search_terms)
    if match:
        results["animecix"] = (match[0], match[0], match[1])

    # Animely - DEVRE DIŞI
    # if ADAPTERS.get("animely"):
    #     try:
    #         for term in search_terms:
    #             try:
    #                 aly_results = animely.search_animely(term, limit=10)
    #                 if aly_results:
    #                     best_match = max(aly_results, key=lambda x: similarity_score(term, x[1]))
    #                     if similarity_score(term, best_match[1]) > 0.5:
    #                         results["animely"] = (None, best_match[0], best_match[1])
    #                         break
    #             except Exception:
    #                 break
    #     except Exception as e:
    #         print(f"[Animely] Arama hatası: {e}")

    # Anizle - hata toleranslı
    match = search_in_single_adapter(lambda term: anizle.search_anizle(term, limit=10, timeout=10), "anizle", search_terms)
    if match:
        results["anizle"] = (None, match[0], match[1])

    # TRAnime - hata toleranslı
    match = search_in_single_adapter(lambda term: tranime.search_tranime(term, limit=10), "tranime", search_terms)
    if match:
        results["tranime"] = (None, match[0], match[1])

    # TurkAnime - hata toleranslı
    if ADAPTERS.get("turkanime"):
        try:
            for term in search_terms:
                try:
                    ta_results = turkanime.search_anime(term)
                    if ta_results:
                        # Find best match for current term
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
            print(f"[TurkAnime] Arama hatası: {e}")

    return results


def fetch_episodes_from_animecix(source_id: str) -> list:
    """AnimeCiX'den bölümleri ve video linklerini çek."""
    try:
        anime = animecix.CixAnime(id=source_id, title="")
        episodes = anime.episodes

        result = []
        for i, ep in enumerate(episodes):
            ep_num = i + 1
            # Bölüm numarasını isminden çıkarmaya çalış
            match = re.search(r'(\d+)\.?\s*[Bb]ölüm', ep.title)
            if match:
                ep_num = int(match.group(1))

            # Video linklerini çek
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
                    print(f"[AnimeCiX] Video çekme hatası ({ep_num}): {ve}")

            result.append({
                "number": ep_num,
                "title": ep.title,
                "url": ep.url,
                "videos": videos
            })
        return result
    except Exception as e:
        print(f"[AnimeCiX] Bölüm çekme hatası: {e}")
        return []


def fetch_episodes_from_animely(slug: str) -> list:
    """Animely'den bölümleri ve video linklerini çek."""
    try:
        episodes = animely.get_anime_episodes(slug)

        result = []
        for ep in episodes:
            videos = []
            streams = ep.get_streams()
            for stream in streams:
                videos.append({
                    "url": stream.url,
                    "quality": stream.quality,
                    "fansub": stream.fansub
                })

            result.append({
                "number": ep.episode_number,
                "title": ep.name,
                "videos": videos
            })
        return result
    except Exception as e:
        print(f"[Animely] Bölüm çekme hatası: {e}")
        return []


def fetch_episodes_from_anizle(slug: str) -> list:
    """Anizle'den bölümleri ve video linklerini çek."""
    try:
        episodes = anizle.get_anime_episodes(slug)

        result = []
        for ep_slug, ep_title in episodes:
            # Bölüm numarasını slug'dan çıkar
            match = re.search(r'-(\d+)-bolum', ep_slug)
            ep_num = int(match.group(1)) if match else 0

            # Video linklerini çek
            videos = []
            try:
                streams = anizle.get_episode_streams(ep_slug)
                for stream in streams:
                    # stream formatı: {"url": "...", "label": "...", "type": "..."}
                    url = stream.get("url") or stream.get("videoUrl", "")
                    if url:
                        # Fansub bilgisini label'dan çıkar
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
                print(f"[Anizle] Video çekme hatası ({ep_num}): {ve}")

            result.append({
                "number": ep_num,
                "title": ep_title,
                "slug": ep_slug,
                "videos": videos
            })
        return result
    except Exception as e:
        print(f"[Anizle] Bölüm çekme hatası: {e}")
        return []


def fetch_episodes_from_tranime(slug: str) -> list:
    """TRAnime'den bölümleri ve video linklerini çek."""
    try:
        episodes = tranime.get_anime_episodes(slug)

        result = []
        for ep in episodes:
            videos = []

            # Bölüm detaylarını al (fansub listesi için)
            try:
                ep_details = tranime.get_episode_details(ep.slug)
                if ep_details:
                    for fansub_id, fansub_name in ep_details.fansubs:
                        sources = ep_details.get_sources(fansub_id)
                        for source in sources:
                            iframe = source.get_iframe()
                            if iframe:
                                videos.append({
                                    "url": iframe,
                                    "quality": source.name,
                                    "fansub": fansub_name
                                })
            except:
                pass

            result.append({
                "number": ep.episode_number,
                "title": ep.title,
                "slug": ep.slug,
                "videos": videos
            })
        return result
    except Exception as e:
        print(f"[TRAnime] Bölüm çekme hatası: {e}")
        return []


# ─────────────────────────────────────────────────────────────────────────────
# ANA GÜNCELLEME FONKSİYONLARI
# ─────────────────────────────────────────────────────────────────────────────

def update_anime_by_mal_id(mal_id: int, extra_ids: Optional[Dict[str, Any]] = None, skip_videos: bool = True) -> bool:
    """
    MAL ID'ye göre anime'yi güncelle.

    1. Jikan API'den anime bilgilerini çek
    2. Cover resmini indir
    3. Veritabanına kaydet
    4. İlişkili verileri (tür, tema, stüdyo) kaydet
    5. Jikan API'den bölüm listesini çek ve kaydet
    6. Adaptörlerde ara ve eşleştir (video çekmeden)

    NOT: Video linkleri çekilmez. Video linkleri için api.py'deki
    /api/sync/videos endpointini kullanın.
    """
    print(f"\n[{mal_id}] Güncelleniyor...")

    # 1. Jikan API'den bilgileri çek
    jikan_data = jikan.get_anime(mal_id)

    if not jikan_data:
        print(f"[{mal_id}] Anime bulunamadı!")
        return False

    # 2. Veriyi parse et
    anime_data = parse_jikan_data(jikan_data, extra_ids or {})
    related_data = get_jikan_related_data(jikan_data)

    # 3. Cover indir
    cover_url = anime_data.get("cover_url")
    if cover_url:
        local_cover = download_cover(cover_url, mal_id)
        anime_data["cover_local"] = local_cover
        print(f"[{mal_id}] Cover indirildi: {local_cover}")

    # 4. Veritabanına kaydet
    anime_id = db.insert_or_update_anime(anime_data)
    if not anime_id:
        print(f"[{mal_id}] Veritabanı kayıt hatası!")
        return False

    print(f"[{mal_id}] {anime_data.get('title')} - DB ID: {anime_id}")

    # 5. İlişkili verileri kaydet
    # Başlıklar
    if related_data.get("titles"):
        db.insert_anime_titles(anime_id, related_data["titles"])

    # Türler
    for genre in related_data.get("genres", []):
        genre_id = db.insert_or_get_genre(genre.get("mal_id"), genre.get("name"))
        if genre_id:
            db.link_anime_genre(anime_id, genre_id)

    # Temalar
    for theme in related_data.get("themes", []):
        theme_id = db.insert_or_get_theme(theme.get("mal_id"), theme.get("name"))
        if theme_id:
            db.link_anime_theme(anime_id, theme_id)

    # Stüdyolar
    for studio in related_data.get("studios", []):
        studio_id = db.insert_or_get_studio(studio.get("mal_id"), studio.get("name"))
        if studio_id:
            db.link_anime_studio(anime_id, studio_id)

    # Yapımcılar
    for producer in related_data.get("producers", []):
        producer_id = db.insert_or_get_producer(producer.get("mal_id"), producer.get("name"))
        if producer_id:
            db.link_anime_producer(anime_id, producer_id, "producer")

    # Lisansörler
    for licensor in related_data.get("licensors", []):
        licensor_id = db.insert_or_get_producer(licensor.get("mal_id"), licensor.get("name"))
        if licensor_id:
            db.link_anime_producer(anime_id, licensor_id, "licensor")

    # 6. Jikan API'den bölüm listesini çek ve kaydet
    # NOT: Devam eden seriler için episodes=null olabilir, yine de bölümleri çekmeye çalış
    total_episodes = jikan_data.get("episodes") or 0
    print(f"[{mal_id}] Bölümler çekiliyor...")
    episodes = jikan.get_anime_episodes(mal_id)

    if episodes:
        for ep in episodes:
            ep_num = ep.get("mal_id")  # Jikan'da episode number "mal_id" olarak geliyor
            ep_title = ep.get("title") or ep.get("title_japanese") or f"{ep_num}. Bölüm"
            if ep_num:
                db.insert_or_update_episode(anime_id, ep_num, ep_title)
        print(f"[{mal_id}] ✓ {len(episodes)} bölüm kaydedildi")
    elif total_episodes > 0:
        # Episode API'den veri gelmezse ve bölüm sayısı biliniyorsa oluştur
        print(f"[{mal_id}] Bölüm detayı yok, {total_episodes} bölüm numarayla oluşturuluyor...")
        for ep_num in range(1, total_episodes + 1):
            db.insert_or_update_episode(anime_id, ep_num, f"{ep_num}. Bölüm")
        print(f"[{mal_id}] ✓ {total_episodes} bölüm oluşturuldu")
    else:
        print(f"[{mal_id}] Henüz bölüm bilgisi yok (devam eden/yeni seri)")

    # 7. Adaptörlerde ara ve sadece eşleşmeyi kaydet (video çekme)
    print(f"[{mal_id}] Adaptörlerde aranıyor...")
    adapter_matches = search_in_adapters(
        anime_data.get("title"),
        anime_data.get("title_english"),
        anime_data.get("title_japanese")
    )

    # 8. Her adaptör için sadece eşleşmeyi kaydet
    for adapter_name, (source_anime_id, source_slug, source_title) in adapter_matches.items():
        print(f"[{mal_id}] {adapter_name}: {source_title}")

        source_id = db.get_source_id(adapter_name)
        if not source_id:
            continue

        # Anime-kaynak eşleşmesini kaydet
        db.insert_or_update_anime_source(anime_id, source_id, source_anime_id, source_slug, source_title)

    print(f"[{mal_id}] ✓ Anime bilgileri, cover ve bölümler kaydedildi (video linkleri çekilmedi)")
    return True


def update_anime_by_title(title: str) -> bool:
    """İsme göre anime güncelle."""
    print(f"\nAranıyor: {title}")

    # Önce anime_ids.json'da MAL ID bul
    anime_ids = load_anime_ids()

    # Jikan'da ara
    try:
        results = jikan.search_anime(title)

        if not results:
            print(f"'{title}' bulunamadı!")
            return False

        # İlk sonucu al veya kullanıcıya sor
        if len(results) == 1:
            selected = results[0]
        else:
            print("\nBulunan sonuçlar:")
            for i, anime in enumerate(results):
                print(f"  {i+1}. [{anime.get('mal_id')}] {anime.get('title')}")

            choice = input("\nSeçiminiz (1-5, varsayılan 1): ").strip()
            idx = int(choice) - 1 if choice.isdigit() else 0
            selected = results[max(0, min(idx, len(results)-1))]

        mal_id = selected.get("mal_id")
        print(f"\nSeçilen: [{mal_id}] {selected.get('title')}")

        # anime_ids.json'dan extra ID'leri bul
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
        print(f"Arama hatası: {e}")
        return False


def bulk_update(limit: Optional[int] = None, skip_updated: bool = True, parallel: int = 10):
    """
    anime_ids.json'dan toplu güncelleme (PARALEL).

    Args:
        limit: Maksimum güncellenecek anime sayısı
        skip_updated: Daha önce güncellenenler atlanır
        parallel: Paralel işlem sayısı (varsayılan: 10, max: 50)
    """
    anime_ids = load_anime_ids()
    updated_ids = load_updated_ids() if skip_updated else set()

    print(f"Toplam anime: {len(anime_ids)}")
    print(f"Daha önce güncellenen: {len(updated_ids)}")

    # MAL ID'leri topla (henüz güncellenmemişler)
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

    print(f"Güncellenecek: {len(to_update)}")
    print(f"Paralel işlem: {min(parallel, 50)}")

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

                # Her 10 anime'de bir kaydet
                if processed % 10 == 0:
                    save_updated_ids(updated_ids)
                    print(f"\n[İlerleme] {processed}/{len(to_update)} - Başarılı: {success_count}, Hatalı: {fail_count}")

            return result
        except Exception as e:
            with lock:
                processed += 1
                fail_count += 1
            print(f"\n[HATA] {mal_id}: {e}")
            return False

    # Paralel güncelleme
    try:
        with ThreadPoolExecutor(max_workers=min(parallel, 50)) as executor:
            futures = [executor.submit(update_single, item) for item in to_update]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"[HATA] Future: {e}")
    except KeyboardInterrupt:
        print("\n\nİptal edildi!")

    # Son kayıt
    save_updated_ids(updated_ids)

    print(f"\n\n{'='*60}")
    print(f"Tamamlandı!")
    print(f"Başarılı: {success_count}")
    print(f"Başarısız: {fail_count}")
    print(f"{'='*60}")


def show_video_links(mal_id: int):
    """Belirli anime için video linklerini göster."""
    anime_row = db.get_anime_by_mal_id(mal_id)
    if not anime_row:
        print(f"MAL ID {mal_id} veritabanında bulunamadı!")
        return

    anime = cast(Dict[str, Any], anime_row)
    anime_id = int(anime["id"])
    print(f"\n{anime['title']} (MAL: {mal_id})")
    print("=" * 60)

    videos = db.get_video_links(anime_id=anime_id)

    if not videos:
        print("Video linki bulunamadı!")
        return

    current_episode = None
    for video_row in videos:
        video = cast(Dict[str, Any], video_row)
        if video["episode_number"] != current_episode:
            current_episode = video["episode_number"]
            print(f"\n{video['episode_number']}. Bölüm")
            print("-" * 40)

        print(f"  [{video['source_name']}] {video['fansub']} ({video['quality']})")
        print(f"    {str(video['video_url'])[:80]}...")


# ─────────────────────────────────────────────────────────────────────────────
# ANA FONKSİYON
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Anime Offline Veritabanı Yöneticisi",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
    python main.py --init                      # Veritabanını başlat
    python main.py --guncelle "Naruto"         # İsme göre güncelle
    python main.py --mal_id 20                 # MAL ID'ye göre güncelle
    python main.py --toplu                     # Toplu güncelle
    python main.py --toplu --limit 100         # İlk 100'ü güncelle
    python main.py --videolar 20               # Video linklerini göster
    python main.py --sifirla                   # Güncelleme listesini sıfırla
        """
    )

    parser.add_argument("--init", action="store_true", help="Veritabanını başlat")
    parser.add_argument("--guncelle", type=str, metavar="ISIM", help="İsme göre güncelle")
    parser.add_argument("--mal_id", type=int, metavar="ID", help="MAL ID'ye göre güncelle")
    parser.add_argument("--toplu", action="store_true", help="anime_ids.json'dan toplu güncelle")
    parser.add_argument("--limit", type=int, help="Toplu güncellemede limit")
    parser.add_argument("--parallel", type=int, default=10, help="Paralel işlem sayısı (varsayılan: 10, max: 50)")
    parser.add_argument("--videolar", type=int, metavar="MAL_ID", help="Video linklerini göster")
    parser.add_argument("--sifirla", action="store_true", help="Güncelleme listesini sıfırla")
    parser.add_argument("--tekrar", action="store_true", help="Güncellenenleri de tekrar güncelle")

    args = parser.parse_args()

    # Hiçbir argüman verilmediyse yardım göster
    if len(sys.argv) == 1:
        parser.print_help()
        return

    # Veritabanını başlat
    if args.init:
        print("Veritabanı başlatılıyor...")
        db.init_database()
        return

    # Güncelleme listesini sıfırla
    if args.sifirla:
        if os.path.exists(UPDATED_IDS_FILE):
            os.remove(UPDATED_IDS_FILE)
            print("Güncelleme listesi sıfırlandı.")
        else:
            print("Güncelleme listesi zaten boş.")
        return

    # İsme göre güncelle
    if args.guncelle:
        update_anime_by_title(args.guncelle)
        return

    # MAL ID'ye göre güncelle
    if args.mal_id:
        # anime_ids.json'dan extra ID'leri bul
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

    # Toplu güncelle
    if args.toplu:
        bulk_update(limit=args.limit, skip_updated=not args.tekrar, parallel=args.parallel)
        return

    # Video linklerini göster
    if args.videolar:
        show_video_links(args.videolar)
        return


if __name__ == "__main__":
    main()
