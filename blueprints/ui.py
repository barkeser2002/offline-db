from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from typing import Dict, Any, cast
import requests
import time
import threading

import db
from config import JIKAN_API_BASE, JIKAN_RATE_LIMIT

ui_bp = Blueprint('ui', __name__)

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


def fetch_season_anime(year: int, season: str, page: int = 1, max_retries: int = 5) -> Dict[str, Any] | None:
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

        all_anime.extend(data)

        pagination = result.get("pagination", {})
        if not pagination.get("has_next_page", False):
            break

        page += 1
        time.sleep(JIKAN_RATE_LIMIT)  # Rate limit

    return all_anime

@ui_bp.route("/")
def home():
    """Ana sayfa."""
    from flask import session
    # İstatistikleri çek
    conn = db.get_connection()
    stats = {"anime_count": 0, "episode_count": 0, "video_count": 0}

    if conn:
        cursor = conn.cursor(dictionary=True)
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

    # Kullanıcı geçmişi ve izleme listesi
    user_history = []
    user_watchlist = []
    if "user_id" in session:
        user_history = db.get_user_watch_history(session["user_id"], limit=5)
        user_watchlist = db.get_user_watchlist(session["user_id"])

    # Yerel Trending
    local_trending = db.get_trending_anime(limit=10)

    # Jikan API'den dinamik içerik çek
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
                         user_watchlist=user_watchlist)

@ui_bp.route("/login")
def login_page():
    return render_template("login.html")

@ui_bp.route("/register")
def register_page():
    return render_template("register.html")


@ui_bp.route("/player")
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

    return render_template("player.html",
                                  anime=anime,
                                  episodes=episodes,
                                  current_ep=ep)


@ui_bp.route("/season/<int:year>/<season>")
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

    return render_template("season.html",
                                  year=year,
                                  season=season,
                                  anime_list=anime_list,
                                  in_db_count=in_db_count)


@ui_bp.route("/search")
def search_page():
    """Arama sayfası."""
    query = request.args.get("q", "")

    if not query:
        return redirect("/")

    results = db.get_anime_by_title(query) or []

    return render_template("search.html", query=query, results=results)


@ui_bp.route("/covers/<filename>")
def serve_cover(filename):
    """Cover resimlerini sun."""
    from flask import send_from_directory
    return send_from_directory("covers", filename)

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

def ensure_anime_data(mal_id):
    """Anime verisi eksikse veya yoksa tamamla."""
    anime = db.get_anime_by_mal_id(mal_id)
    if not anime:
        print(f"[Info] Anime {mal_id} DB'de yok, indiriliyor...")
        from main import update_anime_by_mal_id
        update_anime_by_mal_id(mal_id)
        return db.get_anime_by_mal_id(mal_id)
    return anime
