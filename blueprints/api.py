from flask import Blueprint, request, jsonify, Response
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, cast, Optional, List, Tuple
from threading import Thread
import threading
import re
import requests
from urllib.parse import urlparse

# Local Modules
import db
from jikan_client import jikan
from .ui import ensure_anime_data, fetch_all_season_anime, get_available_seasons
from services.video_service import ensure_episode_videos, check_video_link_alive, remove_dead_video_link
from config import (
    JIKAN_API_BASE, JIKAN_RATE_LIMIT, API_HOST, API_PORT, MAX_WORKERS, ADAPTERS,
    ALLOWED_PROXY_DOMAINS, VIDEO_WORKERS
)

api_bp = Blueprint('api', __name__)

@api_bp.route("/api/info")
def info_page():
    """Anime information and JSON output."""
    mal_id = request.args.get("mal_id", type=int)
    if not mal_id:
        return jsonify({"error": "mal_id required"}), 400

    anime = ensure_anime_data(mal_id)
    if not anime:
        return jsonify({"error": "Anime not found"}), 404

    return jsonify(anime)

@api_bp.route("/api/proxy")
def proxy():
    """HLS stream proxy to fix CORS issues."""
    url = request.args.get("url")
    if not url:
        return "URL parameter is required", 400

    # SSRF Protection
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
    """Short list of all animes in the database."""
    conn = db.get_connection()
    if not conn:
        return jsonify({"error": "DB connection error"}), 500

    cursor = conn.cursor()
    cursor.execute("""
        SELECT mal_id, title, title_english, type, episodes, status, score, year, season, cover_local
        FROM animes ORDER BY mal_id
    """)

    rows = cursor.fetchall()
    cursor.close(); conn.close()

    host = request.host_url.rstrip('/')
    animes = []
    for r in rows:
        animes.append({
            "mal_id": r["mal_id"],
            "title": r["title"],
            "title_english": r["title_english"],
            "cover": f"{host}/anime/covers/{r['mal_id']}.jpg" if r["cover_local"] else None,
            "type": r["type"],
            "episodes": r["episodes"],
            "status": r["status"],
            "score": float(r["score"]) if r["score"] else None,
            "year": r["year"],
            "season": r["season"]
        })

    return jsonify({"count": len(animes), "animes": animes})

@api_bp.route("/api/json")
def api_json_endpoint():
    """Single endpoint for anime info and video links."""
    mal_id = request.args.get("malid", type=int)
    episode = request.args.get("episode", type=int)

    if not mal_id: return jsonify({"error": "malid parameter required"}), 400

    anime_raw = ensure_anime_data(mal_id)
    if not anime_raw: return jsonify({"error": "Anime not found"}), 404

    anime = dict(anime_raw)
    anime_db_id = int(anime["id"])

    if episode is None:
        episodes_list = db.get_anime_full_details(mal_id).get("episodes_list", [])
        return jsonify({"success": True, "anime": anime, "episodes": episodes_list})
    else:
        videos = db.get_video_links(anime_id=anime_db_id, episode_number=episode)
        if not videos:
            ensure_episode_videos(mal_id, episode, anime_db_id)
            videos = db.get_video_links(anime_id=anime_db_id, episode_number=episode)
        return jsonify({"success": True, "anime": anime, "episode": episode, "videos": videos})

@api_bp.route("/api/anime/<int:mal_id>")
def api_anime(mal_id):
    """Return anime details."""
    anime = db.get_anime_by_mal_id(mal_id)
    if not anime: return jsonify({"error": "Anime not found"}), 404
    return jsonify(dict(anime))

@api_bp.route("/api/stream/<int:mal_id>/<int:episode>")
def api_stream(mal_id, episode):
    """Return episode video stream URLs."""
    anime_raw = ensure_anime_data(mal_id)
    if not anime_raw: return jsonify({"error": "Anime not found"}), 404

    anime = dict(anime_raw)
    anime_db_id = int(anime["id"])

    ensure_episode_videos(mal_id, episode, anime_db_id)
    videos = db.get_video_links(anime_id=anime_db_id, episode_number=episode)

    return jsonify({"mal_id": mal_id, "episode": episode, "videos": videos})

# ─────────────────────────────────────────────────────────────────────────────
# SYNC ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@api_bp.route("/api/sync/anime/<int:mal_id>")
def api_sync_anime(mal_id):
    """Force sync anime metadata from Jikan."""
    from main import update_anime_by_mal_id
    success = update_anime_by_mal_id(mal_id)
    return jsonify({"success": success, "mal_id": mal_id})

@api_bp.route("/api/sync/videos/<int:mal_id>")
def api_sync_videos(mal_id):
    """Sync video links for all episodes of an anime."""
    anime = db.get_anime_by_mal_id(mal_id)
    if not anime: return jsonify({"error": "Anime not in DB"}), 404

    details = db.get_anime_full_details(mal_id)
    episodes = details.get("episodes_list", [])

    def sync_ep(ep_num):
        ensure_episode_videos(mal_id, ep_num, anime["id"], force_refresh=True)

    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(lambda e: sync_ep(e["episode_number"]), episodes)

    return jsonify({"success": True, "mal_id": mal_id, "episodes_synced": len(episodes)})

@api_bp.route("/api/sync/season/<int:year>/<season>")
def api_sync_season(year, season):
    """Sync all anime from a specific season."""
    anime_list = fetch_all_season_anime(year, season, save_to_db=True)
    return jsonify({"success": True, "count": len(anime_list)})

# ─────────────────────────────────────────────────────────────────────────────
# DISCOVERY & SOCIAL
# ─────────────────────────────────────────────────────────────────────────────

@api_bp.route("/api/discover", methods=["GET", "POST"])
def api_discover():
    """Discover animes with filters."""
    if request.method == "POST":
        filters = request.get_json() or {}
    else:
        filters = {
            "genres": request.args.getlist("genres", type=int),
            "year": request.args.get("year", type=int),
            "type": request.args.get("type"),
            "sort": request.args.get("sort", "popularity")
        }

    results = db.discover_animes(filters)
    return jsonify(db.serialize_for_json(results))

@api_bp.route("/api/trending")
def api_trending():
    """Get trending animes."""
    trending = db.get_trending_anime(limit=10)
    return jsonify(db.serialize_for_json(trending))

@api_bp.route("/api/seasons")
def api_seasons():
    """List available seasons."""
    return jsonify(get_available_seasons()[:100])

@api_bp.route("/api/validate/batch", methods=["POST"])
def api_validate_batch_links():
    """Batch validate video links."""
    data = request.get_json() or {}
    limit = min(data.get("limit", 100), 1000)
    parallel = min(data.get("parallel", 10), 50)

    conn = db.get_connection(); cursor = conn.cursor()
    cursor.execute("SELECT id, url FROM video_links WHERE is_active = 1 LIMIT ?", (limit,))
    links = cursor.fetchall(); cursor.close(); conn.close()

    results = {"total": len(links), "alive": 0, "dead": 0}

    def check_link(link):
        is_alive, _ = check_video_link_alive(link["url"])
        if not is_alive: remove_dead_video_link(link["id"])
        return is_alive

    with ThreadPoolExecutor(max_workers=parallel) as executor:
        futures = [executor.submit(check_link, l) for l in links]
        for f in as_completed(futures):
            if f.result(): results["alive"] += 1
            else: results["dead"] += 1

    return jsonify(results)
