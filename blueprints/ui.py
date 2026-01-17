from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from typing import Dict, Any, cast
import requests
import time
import threading

import db
from config import JIKAN_API_BASE, JIKAN_RATE_LIMIT

ui_bp = Blueprint('ui', __name__)

# ─────────────────────────────────────────────────────────────────────────────
# JIKAN API - SEASON ANIME LIST (RATE LIMIT: 3/sec, 60/min)
# ─────────────────────────────────────────────────────────────────────────────

# Global variables for rate limiter
_jikan_last_request_time = 0.0
_jikan_rate_lock = threading.Lock()

def _apply_jikan_rate_limit():
    """Jikan API rate limit - max 3 requests per second."""
    global _jikan_last_request_time
    with _jikan_rate_lock:
        now = time.time()
        elapsed = now - _jikan_last_request_time
        if elapsed < 0.35:  # Safe interval for ~3 requests/sec
            time.sleep(0.35 - elapsed)
        _jikan_last_request_time = time.time()


def fetch_season_anime(year: int, season: str, page: int = 1, max_retries: int = 5) -> Dict[str, Any] | None:
    """
    Fetch season anime list from Jikan API.
    Retries on 429 (Too Many Requests).

    season: winter, spring, summer, fall
    """
    for attempt in range(max_retries):
        try:
            _apply_jikan_rate_limit()

            url = f"{JIKAN_API_BASE}/seasons/{year}/{season}"
            params = {"page": page, "limit": 25}
            response = requests.get(url, params=params, timeout=30)

            # 429 Too Many Requests - wait and retry
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 5))
                wait_time = max(retry_after, 2 ** attempt + 1)
                print(f"[Jikan] Rate limit! Waiting {wait_time}s... (attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
                continue

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 429:
                wait_time = 2 ** attempt + 2
                print(f"[Jikan] Rate limit! Waiting {wait_time}s... (attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
                continue
            print(f"[Jikan] Season fetch error ({year}/{season}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return None
        except requests.exceptions.Timeout:
            print(f"[Jikan] Timeout ({year}/{season} p.{page}), retrying...")
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
    Fetch all anime of a season (all pages).

    Args:
        year: Year (e.g., 2026)
        season: Season (winter, spring, summer, fall)
        save_to_db: If True, saves missing anime to DB

    Returns:
        Anime list
    """
    all_anime = []
    page = 1

    # Existing MAL IDs in DB
    existing_ids = set(db.get_all_mal_ids()) if save_to_db else set()
    saved_count = 0

    while True:
        print(f"[Jikan] Fetching {year}/{season} page {page}...")
        result = fetch_season_anime(year, season, page)

        if not result:
            break

        data = result.get("data", [])
        if not data:
            break

        all_anime.extend(data)

        pagination = result.get("pagination", {})
        if not pagination.get("has_next_page", False):
            break

        page += 1
        time.sleep(JIKAN_RATE_LIMIT)  # Rate limit

    return all_anime

@ui_bp.route("/anime/<int:mal_id>")
def anime_details(mal_id):
    """Anime details page."""
    from flask import session
    anime = db.get_anime_full_details(mal_id)

    if not anime:
        from main import update_anime_by_mal_id
        update_anime_by_mal_id(mal_id)
        anime = db.get_anime_full_details(mal_id)

    if not anime:
        return "Anime not found", 404

    # User status (In watchlist?)
    user_status = None
    if "user_id" in session:
        watchlist = db.get_user_watchlist(session["user_id"])
        for item in watchlist:
            if item["mal_id"] == mal_id:
                user_status = item["status"]
                break

    return render_template("anime_details.html", anime=anime, user_status=user_status)

@ui_bp.route("/profile")
@ui_bp.route("/dashboard")
def profile_page():
    """User profile and dashboard page."""
    from flask import session
    if "user_id" not in session:
        return redirect(url_for("ui.login_page"))

    user = db.get_user_by_id(session["user_id"])
    if not user:
        return redirect(url_for("ui.login_page"))

    stats = db.get_user_stats(session["user_id"])
    watch_history = db.get_user_watch_history(session["user_id"], limit=50)
    watchlist = db.get_user_watchlist(session["user_id"])

    # Categorize watchlist
    categorized_watchlist = {
        "watching": [],
        "plan-to-watch": [],
        "completed": [],
        "on-hold": [],
        "dropped": []
    }
    for item in watchlist:
        status = item["status"]
        if status in categorized_watchlist:
            categorized_watchlist[status].append(item)

    return render_template("profile.html",
                         user=user,
                         stats=stats,
                         watch_history=watch_history,
                         watchlist=categorized_watchlist)

@ui_bp.route("/")
def home():
    """Home page."""
    from flask import session
    # Fetch statistics
    conn = db.get_connection()
    stats = {"anime_count": 0, "episode_count": 0, "video_count": 0}

    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM animes")
        res = cursor.fetchone()
        if res: stats["anime_count"] = int(cast(Dict[str, Any], res)["count"])

        cursor.execute("SELECT COUNT(*) as count FROM episodes")
        res = cursor.fetchone()
        if res: stats["episode_count"] = int(cast(Dict[str, Any], res)["count"])

        cursor.execute("SELECT COUNT(*) as count FROM video_links")
        res = cursor.fetchone()
        if res: stats["video_count"] = int(cast(Dict[str, Any], res)["count"])
        cursor.close()
        conn.close()

    seasons = get_available_seasons()

    # User history and watchlist
    user_history = []
    user_watchlist = []
    user_recommendations = []
    if "user_id" in session:
        user_history = db.get_user_watch_history(session["user_id"], limit=5)
        user_watchlist = db.get_user_watchlist(session["user_id"])
        user_recommendations = db.get_personalized_recommendations(session["user_id"], limit=5)

    # Local Trending
    local_trending = db.get_trending_anime(limit=10)

    # Fetch dynamic content from Jikan API
    top_anime = []
    recommendations = []
    try:
        top_anime_res = requests.get(f"{JIKAN_API_BASE}/top/anime", params={"limit": 10}, timeout=5)
        if top_anime_res.status_code == 200:
            top_anime = top_anime_res.json().get("data", [])

        recommendations_res = requests.get(f"{JIKAN_API_BASE}/recommendations/anime", params={"limit": 10}, timeout=5)
        if recommendations_res.status_code == 200:
            recommendations = recommendations_res.json().get("data", [])
    except Exception as e:
        print(f"Jikan API error: {e}")

    return render_template("home.html",
                         stats=stats,
                         seasons=seasons,
                         top_anime=top_anime,
                         recommendations=recommendations,
                         local_trending=local_trending,
                         user_history=user_history,
                         user_watchlist=user_watchlist,
                         user_recommendations=user_recommendations)

@ui_bp.route("/login")
def login_page():
    return render_template("login.html")

@ui_bp.route("/register")
def register_page():
    return render_template("register.html")


@ui_bp.route("/player")
def player():
    """Anime player page."""
    mal_id = request.args.get("mal_id", type=int)
    ep = request.args.get("ep", 1, type=int)

    if not mal_id:
        return redirect("/")

    # Fetch anime info (Using helper)
    anime_raw = ensure_anime_data(mal_id)

    if not anime_raw:
        return "Anime not found", 404

    anime = dict(anime_raw)

    # Fetch episodes
    conn = db.get_connection()
    episodes = []

    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.*,
                   (SELECT COUNT(*) FROM video_links WHERE episode_id = e.id) as video_count
            FROM episodes e
            WHERE e.anime_id = ?
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

    # If no episodes, create placeholders up to total episodes
    total_eps = dict(anime).get("episodes")
    if not episodes and total_eps:
        episodes = [{"episode_number": i, "title": f"Episode {i}", "has_video": False}
                    for i in range(1, int(total_eps) + 1)]

    return render_template("player.html",
                                  anime=anime,
                                  episodes=episodes,
                                  current_ep=ep)


@ui_bp.route("/season/<int:year>/<season>")
def season_page(year, season):
    """Season anime list page."""
    # Fetch season list from Jikan
    anime_list_raw = fetch_all_season_anime(year, season)

    # MAL IDs in database
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

    return render_template("season.html",
                                  year=year,
                                  season=season,
                                  anime_list=anime_list,
                                  in_db_count=in_db_count)


@ui_bp.route("/watchlist")
def watchlist_page():
    """Watchlist page."""
    from flask import session
    if "user_id" not in session:
        return redirect(url_for("ui.login_page"))

    watchlist = db.get_user_watchlist(session["user_id"])

    return render_template("watchlist.html", watchlist=watchlist)

@ui_bp.route("/search")
def search_page():
    """Search page."""
    query = request.args.get("q", "")

    if not query:
        return redirect("/")

    results = db.get_anime_by_title(query) or []

    return render_template("search.html", query=query, results=results)

@ui_bp.route("/discover")
def discover_page():
    """Discover (Advanced Filtering) page."""
    genres = db.get_genres()
    current_filters = {
        "sort": request.args.get("sort", "score"),
        "genres": request.args.getlist("genres"),
        "type": request.args.get("type", ""),
        "status": request.args.get("status", ""),
        "min_score": request.args.get("min_score", ""),
        "year": request.args.get("year", "")
    }
    return render_template("discover.html", genres=genres, current_filters=current_filters)


@ui_bp.route("/anime/covers/<filename>")
def serve_cover(filename):
    """Serve cover images."""
    from flask import send_from_directory
    return send_from_directory("covers", filename)

def get_available_seasons() -> list:
    """List available seasons (from 2000 to today)."""
    import datetime
    current_year = datetime.datetime.now().year
    seasons = ["winter", "spring", "summer", "fall"]

    result = []
    for year in range(current_year, 1999, -1):
        for season in seasons:
            result.append({"year": year, "season": season})

    return result

def ensure_anime_data(mal_id):
    """Complete anime data if missing or incomplete."""
    anime = db.get_anime_by_mal_id(mal_id)
    if not anime:
        print(f"[Info] Anime {mal_id} not in DB, downloading...")
        from main import update_anime_by_mal_id
        update_anime_by_mal_id(mal_id)
        return db.get_anime_by_mal_id(mal_id)
    return anime
