from flask import Blueprint, request, jsonify, render_template, redirect, url_for, Response
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, cast, Optional, List, Tuple
from functools import partial
from threading import Thread
import threading
import json
import os
import re
import subprocess
import time
import requests

from urllib.parse import urlparse

# Local Modules
import main
from config import (
    JIKAN_API_BASE, JIKAN_RATE_LIMIT, API_HOST, API_PORT, MAX_WORKERS, ADAPTERS,
    ALLOWED_PROXY_DOMAINS
)
import db
from jikan_client import jikan
from .ui import ensure_anime_data, get_available_seasons
from adapters import anizle, animecix, tranime, turkanime

api_bp = Blueprint('api', __name__)

@api_bp.route("/info")
def info_page():
    """Anime bilgi ve JSON çıktısı."""
    mal_id = request.args.get("mal_id", type=int)
    if not mal_id:
        return jsonify({"error": "mal_id required"}), 400

    anime = ensure_anime_data(mal_id)
    if not anime:
        return jsonify({"error": "Anime not found"}), 404

    return jsonify(anime)

@api_bp.route("/")
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

    # Jikan API'den dinamik içerik çek
    top_anime = jikan.get_top_anime()
    recommendations = jikan.get_recommendations()

    return render_template("home.html", stats=stats, seasons=seasons, top_anime=top_anime, recommendations=recommendations)


@api_bp.route("/player")
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


@api_bp.route("/season/<int:year>/<season>")
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


@api_bp.route("/search")
def search_page():
    """Arama sayfası."""
    query = request.args.get("q", "")

    if not query:
        return redirect("/")

    results = db.get_anime_by_title(query) or []

    return render_template_string(SEARCH_TEMPLATE, query=query, results=results)


@api_bp.route("/covers/<filename>")
def serve_cover(filename):
    """Cover resimlerini sun."""
    from flask import send_from_directory
    return send_from_directory("covers", filename)


@api_bp.route("/api/proxy")
def proxy():
    """HLS stream proxy to fix CORS issues."""
    url = request.args.get("url")
    if not url:
        return "URL parameter is required", 400

    # SSRF Koruması
    try:
        parsed_url = urlparse(url)
        if not parsed_url.hostname or not any(parsed_url.hostname.endswith(domain) for domain in ALLOWED_PROXY_DOMAINS):
            return "URL is not allowed", 403
    except Exception:
        return "Invalid URL", 400

    headers = {"Referer": "https://anizmplayer.com/"}
    req = requests.get(url, headers=headers, stream=True)
    return Response(req.iter_content(chunk_size=1024), content_type=req.headers['content-type'])


# ─────────────────────────────────────────────────────────────────────────────
# API ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@api_bp.route("/api/dbanimelist")
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


@api_bp.route("/api/json")
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


@api_bp.route("/api/anime/<int:mal_id>")
def api_anime(mal_id):
    """Anime bilgilerini döndür."""
    anime = db.get_anime_by_mal_id(mal_id)
    if not anime:
        return jsonify({"error": "Anime bulunamadı"}), 404
    return jsonify(anime)


@api_bp.route("/api/episodes/<int:mal_id>")
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


@api_bp.route("/api/stream/<int:mal_id>/<int:episode>")
def api_stream(mal_id, episode):
    """
    Bölüm video stream URL'lerini döndür.
    yt-dlp ile en iyi kaliteyi bul.
    """
    refresh = request.args.get('refresh', 'false').lower() == 'true'
    anime_raw = ensure_anime_data(mal_id)
    if not anime_raw:
        return jsonify({"error": "Anime bulunamadı"}), 404

    anime = cast(Dict[str, Any], anime_raw)
    anime_id = int(anime["id"])

    if refresh:
        db.delete_video_links_for_episode(anime_id, episode)

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


@api_bp.route("/api/trending")
def api_trending():
    """Platformda trend olan anime'leri döndür."""
    limit = request.args.get("limit", 10, type=int)
    trending = db.get_trending_anime(limit)
    return jsonify(trending)


@api_bp.route("/api/seasons")
def api_seasons():
    """Mevcut sezonları listele."""
    return jsonify(get_available_seasons()[:100])


@api_bp.route("/api/seasons/<int:year>/<season>")
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


@api_bp.route("/api/sync/season", methods=["POST"])
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

@api_bp.route("/api/sync/anime-info", methods=["POST"])
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
            jikan_data = jikan.get_anime(mal_id)
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


@api_bp.route("/api/sync/covers", methods=["POST"])
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


@api_bp.route("/api/sync/videos", methods=["POST"])
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


@api_bp.route("/api/sync/adapter/<adapter_name>", methods=["POST"])
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


@api_bp.route("/api/sync/batch", methods=["POST"])
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
                jikan_data = jikan.get_anime(mal_id)
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


@api_bp.route("/api/adapters/status")
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

@api_bp.route("/api/validate/link", methods=["POST"])
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


@api_bp.route("/api/validate/anime/<int:mal_id>", methods=["POST"])
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


@api_bp.route("/api/validate/batch", methods=["POST"])
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


@api_bp.route("/api/cleanup/dead-links", methods=["POST"])
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
