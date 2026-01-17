"""
SQLite Database Operations for Anime Platform
"""

import sqlite3
from sqlite3 import Error
from config import DB_PATH
import os

def get_connection():
    """Create a database connection."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Error as e:
        print(f"[DB] Connection error: {e}")
        return None

def init_database():
    """Initialize database tables."""
    conn = get_connection()
    if not conn: return False
    cursor = conn.cursor()

    # Animes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS animes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mal_id INTEGER UNIQUE NOT NULL,
        title TEXT NOT NULL,
        title_english TEXT,
        type TEXT,
        episodes INTEGER DEFAULT 0,
        status TEXT,
        score REAL,
        synopsis TEXT,
        year INTEGER,
        season TEXT,
        cover_url TEXT,
        cover_local TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # Users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # Episodes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS episodes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        anime_id INTEGER NOT NULL,
        episode_number INTEGER NOT NULL,
        title TEXT,
        aired DATE,
        FOREIGN KEY (anime_id) REFERENCES animes(id)
    )""")

    # Video Links
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS video_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        episode_id INTEGER NOT NULL,
        source_id INTEGER,
        url TEXT NOT NULL,
        quality TEXT,
        fansub TEXT,
        is_active BOOLEAN DEFAULT 1,
        FOREIGN KEY (episode_id) REFERENCES episodes(id)
    )""")

    # Watch History
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS watch_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        anime_id INTEGER NOT NULL,
        episode_number INTEGER DEFAULT 0,
        progress INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (anime_id) REFERENCES animes(id),
        UNIQUE(user_id, anime_id)
    )""")

    # Watchlists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS watchlists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        anime_id INTEGER NOT NULL,
        status TEXT NOT NULL,
        score INTEGER,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (anime_id) REFERENCES animes(id),
        UNIQUE(user_id, anime_id)
    )""")

    # Comments
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        anime_id INTEGER NOT NULL,
        episode_number INTEGER NOT NULL,
        content TEXT NOT NULL,
        is_spoiler BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (anime_id) REFERENCES animes(id)
    )""")

    # Auxiliary tables
    for table in ['genres', 'themes', 'studios', 'producers']:
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {table} (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL)")

    cursor.execute("CREATE TABLE IF NOT EXISTS anime_genres (anime_id INTEGER, genre_id INTEGER, PRIMARY KEY(anime_id, genre_id))")
    cursor.execute("CREATE TABLE IF NOT EXISTS anime_themes (anime_id INTEGER, theme_id INTEGER, PRIMARY KEY(anime_id, theme_id))")
    cursor.execute("CREATE TABLE IF NOT EXISTS anime_studios (anime_id INTEGER, studio_id INTEGER, PRIMARY KEY(anime_id, studio_id))")
    cursor.execute("CREATE TABLE IF NOT EXISTS anime_producers (anime_id INTEGER, producer_id INTEGER, role TEXT, PRIMARY KEY(anime_id, producer_id, role))")
    cursor.execute("CREATE TABLE IF NOT EXISTS anime_titles (id INTEGER PRIMARY KEY AUTOINCREMENT, anime_id INTEGER, title TEXT, type TEXT)")

    # Sources
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        base_url TEXT,
        is_active BOOLEAN DEFAULT 1
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS anime_sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        anime_id INTEGER NOT NULL,
        source_id INTEGER NOT NULL,
        source_anime_id TEXT NOT NULL,
        source_slug TEXT,
        source_title TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (anime_id) REFERENCES animes(id),
        FOREIGN KEY (source_id) REFERENCES sources(id),
        UNIQUE(anime_id, source_id)
    )""")

    conn.commit()
    cursor.close()
    conn.close()
    return True

# --- User ---
def get_user_by_username(username):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    res = cursor.fetchone(); cursor.close(); conn.close()
    return dict(res) if res else None

def get_user_by_id(user_id):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    res = cursor.fetchone(); cursor.close(); conn.close()
    return dict(res) if res else None

def create_user(username, email, password_hash):
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)", (username, email, password_hash))
        conn.commit(); uid = cursor.lastrowid
    except: uid = None
    cursor.close(); conn.close()
    return uid

# --- Anime ---
def get_anime_by_mal_id(mal_id):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("SELECT * FROM animes WHERE mal_id = ?", (mal_id,))
    res = cursor.fetchone(); cursor.close(); conn.close()
    return dict(res) if res else None

def get_anime_full_details(mal_id):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("SELECT * FROM animes WHERE mal_id = ?", (mal_id,))
    a = cursor.fetchone()
    if not a: cursor.close(); conn.close(); return None
    a = dict(a)
    cursor.execute("""
        SELECT e.*,
               (SELECT COUNT(*) FROM video_links WHERE episode_id = e.id) as video_count
        FROM episodes e
        WHERE anime_id = ?
        ORDER BY episode_number
    """, (a["id"],))
    a["episodes_list"] = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT g.name, g.id FROM genres g JOIN anime_genres ag ON g.id = ag.genre_id WHERE ag.anime_id = ? ORDER BY g.name", (a["id"],))
    gs = cursor.fetchall()
    a["genres"] = [r["name"] for r in gs]; a["genre_ids"] = [r["id"] for r in gs]
    cursor.close(); conn.close()
    return a

def insert_or_update_anime(anime_data):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("SELECT id FROM animes WHERE mal_id = ?", (anime_data["mal_id"],))
    ex = cursor.fetchone()
    if ex:
        cursor.execute("UPDATE animes SET title=?, title_english=?, type=?, episodes=?, status=?, score=?, synopsis=?, year=?, season=?, cover_url=?, cover_local=?, updated_at=CURRENT_TIMESTAMP WHERE mal_id=?",
            (anime_data.get("title"), anime_data.get("title_english"), anime_data.get("type"), anime_data.get("episodes",0), anime_data.get("status"), anime_data.get("score"), anime_data.get("synopsis"), anime_data.get("year"), anime_data.get("season"), anime_data.get("cover_url"), anime_data.get("cover_local"), anime_data["mal_id"]))
        aid = ex["id"]
    else:
        cursor.execute("INSERT INTO animes (mal_id, title, title_english, type, episodes, status, score, synopsis, year, season, cover_url, cover_local) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (anime_data["mal_id"], anime_data.get("title"), anime_data.get("title_english"), anime_data.get("type"), anime_data.get("episodes",0), anime_data.get("status"), anime_data.get("score"), anime_data.get("synopsis"), anime_data.get("year"), anime_data.get("season"), anime_data.get("cover_url"), anime_data.get("cover_local")))
        aid = cursor.lastrowid
    conn.commit(); cursor.close(); conn.close()
    return aid

# --- Sources & Links ---
def get_anime_sources(mal_id):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("""
        SELECT s.name as source_name, s.id as source_id, aso.source_slug, aso.source_anime_id
        FROM anime_sources aso
        JOIN sources s ON aso.source_id = s.id
        JOIN animes a ON aso.anime_id = a.id
        WHERE a.mal_id = ?
    """, (mal_id,))
    res = [dict(r) for r in cursor.fetchall()]; cursor.close(); conn.close()
    return res

def get_source_id(name):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("SELECT id FROM sources WHERE name = ?", (name,))
    ex = cursor.fetchone()
    if ex: sid = ex["id"]
    else: cursor.execute("INSERT INTO sources (name) VALUES (?)", (name,)); conn.commit(); sid = cursor.lastrowid
    cursor.close(); conn.close()
    return sid

def insert_or_update_anime_source(anime_id, source_id, source_anime_id, source_slug, source_title):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("SELECT id FROM anime_sources WHERE anime_id=? AND source_id=?", (anime_id, source_id))
    ex = cursor.fetchone()
    if ex: cursor.execute("UPDATE anime_sources SET source_anime_id=?, source_slug=?, source_title=? WHERE id=?", (source_anime_id, source_slug, source_title, ex["id"]))
    else: cursor.execute("INSERT INTO anime_sources (anime_id, source_id, source_anime_id, source_slug, source_title) VALUES (?,?,?,?,?)", (anime_id, source_id, source_anime_id, source_slug, source_title))
    conn.commit(); cursor.close(); conn.close()

def insert_video_link(episode_id, source_id, url, quality, fansub=None):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("INSERT INTO video_links (episode_id, source_id, url, quality, fansub) VALUES (?,?,?,?,?)", (episode_id, source_id, url, quality, fansub))
    conn.commit(); cursor.close(); conn.close()

def remove_dead_video_link(link_id):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("DELETE FROM video_links WHERE id = ?", (link_id,))
    conn.commit(); cursor.close(); conn.close()

# --- Episodes ---
def get_episode_by_number(anime_id, episode_number):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("SELECT * FROM episodes WHERE anime_id=? AND episode_number=?", (anime_id, episode_number))
    res = cursor.fetchone(); cursor.close(); conn.close()
    return dict(res) if res else None

def insert_or_update_episode(anime_id, episode_number, title):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("SELECT id FROM episodes WHERE anime_id=? AND episode_number=?", (anime_id, episode_number))
    ex = cursor.fetchone()
    if ex: cursor.execute("UPDATE episodes SET title=? WHERE id=?", (title, ex["id"])); eid = ex["id"]
    else: cursor.execute("INSERT INTO episodes (anime_id, episode_number, title) VALUES (?,?,?)", (anime_id, episode_number, title)); eid = cursor.lastrowid
    conn.commit(); cursor.close(); conn.close()
    return eid

def get_video_links(anime_id, episode_number=None):
    conn = get_connection(); cursor = conn.cursor()
    if episode_number:
        cursor.execute("""
            SELECT vl.*, e.episode_number, s.name as source_name
            FROM video_links vl
            JOIN episodes e ON vl.episode_id=e.id
            LEFT JOIN sources s ON vl.source_id = s.id
            WHERE e.anime_id=? AND e.episode_number=? AND vl.is_active=1
            ORDER BY vl.quality
        """, (anime_id, episode_number))
    else:
        cursor.execute("""
            SELECT vl.*, e.episode_number, s.name as source_name
            FROM video_links vl
            JOIN episodes e ON vl.episode_id=e.id
            LEFT JOIN sources s ON vl.source_id = s.id
            WHERE e.anime_id=? AND vl.is_active=1
            ORDER BY e.episode_number, vl.quality
        """, (anime_id,))
    res = [dict(r) for r in cursor.fetchall()]; cursor.close(); conn.close()
    return res

# --- Discovery & Search ---
def discover_animes(filters, limit=24, offset=0):
    conn = get_connection(); cursor = conn.cursor()
    q = "SELECT a.* FROM animes a"; p = []; w = []
    if filters.get("genre"): q += " JOIN anime_genres ag ON a.id=ag.anime_id"; w.append("ag.genre_id=?"); p.append(filters["genre"])
    if filters.get("year"): w.append("a.year=?"); p.append(filters["year"])
    if filters.get("type"): w.append("a.type=?"); p.append(filters["type"])
    if w: q += " WHERE " + " AND ".join(w)
    s = filters.get("sort", "score")
    if s == "newest": q += " ORDER BY a.year DESC, a.id DESC"
    elif s == "oldest": q += " ORDER BY a.year ASC, a.id ASC"
    else: q += " ORDER BY a.score DESC"
    q += " LIMIT ? OFFSET ?"; p.extend([limit, offset])
    cursor.execute(q, p); res = [dict(r) for r in cursor.fetchall()]; cursor.close(); conn.close()
    return res

def get_trending_anime(limit=10, days=7):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute(f"SELECT a.*, COUNT(wh.id) as trend_score FROM animes a LEFT JOIN watch_history wh ON a.id=wh.anime_id WHERE wh.updated_at >= date('now', '-{days} days') OR wh.id IS NULL GROUP BY a.id ORDER BY trend_score DESC, a.score DESC LIMIT ?", (limit,))
    res = [dict(r) for r in cursor.fetchall()]; cursor.close(); conn.close()
    return res

def get_anime_by_title(query, limit=20):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("SELECT * FROM animes WHERE title LIKE ? OR title_english LIKE ? ORDER BY score DESC LIMIT ?", (f"%{query}%", f"%{query}%", limit))
    res = [dict(r) for r in cursor.fetchall()]; cursor.close(); conn.close()
    return res

def get_genres():
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("SELECT * FROM genres ORDER BY name")
    res = [dict(r) for r in cursor.fetchall()]; cursor.close(); conn.close()
    return res

def get_all_mal_ids():
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("SELECT mal_id FROM animes"); res = [r[0] for r in cursor.fetchall()]; cursor.close(); conn.close()
    return res

# --- Watch & Social ---
def update_watch_history(user_id, anime_id, episode_number, progress=0):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("INSERT INTO watch_history (user_id, anime_id, episode_number, progress, updated_at) VALUES (?,?,?,?,CURRENT_TIMESTAMP) ON CONFLICT(user_id, anime_id) DO UPDATE SET episode_number=excluded.episode_number, progress=excluded.progress, updated_at=CURRENT_TIMESTAMP", (user_id, anime_id, episode_number, progress))
    conn.commit(); cursor.close(); conn.close()

def update_watchlist(user_id, anime_id, status, score=None):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("INSERT INTO watchlists (user_id, anime_id, status, score, added_at) VALUES (?,?,?,?,CURRENT_TIMESTAMP) ON CONFLICT(user_id, anime_id) DO UPDATE SET status=excluded.status, score=COALESCE(excluded.score, watchlists.score)", (user_id, anime_id, status, score))
    conn.commit(); cursor.close(); conn.close()

def get_user_watch_history(user_id, limit=50):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("SELECT wh.*, a.title, a.cover_url, a.mal_id FROM watch_history wh JOIN animes a ON wh.anime_id=a.id WHERE wh.user_id=? ORDER BY wh.updated_at DESC LIMIT ?", (user_id, limit))
    res = [dict(r) for r in cursor.fetchall()]; cursor.close(); conn.close()
    return res

def get_user_watchlist(user_id):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("SELECT wl.*, a.title, a.cover_url, a.mal_id, a.type, a.status as anime_status FROM watchlists wl JOIN animes a ON wl.anime_id=a.id WHERE wl.user_id=? ORDER BY wl.added_at DESC", (user_id,))
    res = [dict(r) for r in cursor.fetchall()]; cursor.close(); conn.close()
    return res

def get_comments(anime_id, episode_number=None):
    conn = get_connection(); cursor = conn.cursor()
    if episode_number: cursor.execute("SELECT c.*, u.username FROM comments c JOIN users u ON c.user_id=u.id WHERE c.anime_id=? AND c.episode_number=? ORDER BY c.created_at DESC", (anime_id, episode_number))
    else: cursor.execute("SELECT c.*, u.username FROM comments c JOIN users u ON c.user_id=u.id WHERE c.anime_id=? ORDER BY c.created_at DESC", (anime_id,))
    res = [dict(r) for r in cursor.fetchall()]; cursor.close(); conn.close()
    return res

def get_episode_comments(anime_id, episode_number): return get_comments(anime_id, episode_number)

def add_comment(user_id, anime_id, episode_number, content, is_spoiler=0):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("INSERT INTO comments (user_id, anime_id, episode_number, content, is_spoiler) VALUES (?,?,?,?,?)", (user_id, anime_id, episode_number, content, is_spoiler))
    conn.commit(); cid = cursor.lastrowid; cursor.close(); conn.close()
    return cid

def delete_comment(comment_id, user_id):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("DELETE FROM comments WHERE id=? AND user_id=?", (comment_id, user_id))
    aff = cursor.rowcount; conn.commit(); cursor.close(); conn.close()
    return aff > 0

# --- Tags & Recommendation ---
def insert_or_get_genre(name):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("SELECT id FROM genres WHERE name=?", (name,)); ex = cursor.fetchone()
    if ex: gid = ex["id"]
    else: cursor.execute("INSERT INTO genres (name) VALUES (?)", (name,)); conn.commit(); gid = cursor.lastrowid
    cursor.close(); conn.close(); return gid

def link_anime_genre(anime_id, genre_id):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO anime_genres (anime_id, genre_id) VALUES (?,?)", (anime_id, genre_id))
    conn.commit(); cursor.close(); conn.close()

def insert_or_get_theme(name):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("SELECT id FROM themes WHERE name=?", (name,)); ex = cursor.fetchone()
    if ex: tid = ex["id"]
    else: cursor.execute("INSERT INTO themes (name) VALUES (?)", (name,)); conn.commit(); tid = cursor.lastrowid
    cursor.close(); conn.close(); return tid

def link_anime_theme(anime_id, theme_id):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO anime_themes (anime_id, theme_id) VALUES (?,?)", (anime_id, theme_id))
    conn.commit(); cursor.close(); conn.close()

def insert_or_get_studio(name):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("SELECT id FROM studios WHERE name=?", (name,)); ex = cursor.fetchone()
    if ex: sid = ex["id"]
    else: cursor.execute("INSERT INTO studios (name) VALUES (?)", (name,)); conn.commit(); sid = cursor.lastrowid
    cursor.close(); conn.close(); return sid

def link_anime_studio(anime_id, studio_id):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO anime_studios (anime_id, studio_id) VALUES (?,?)", (anime_id, studio_id))
    conn.commit(); cursor.close(); conn.close()

def insert_or_get_producer(name):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("SELECT id FROM producers WHERE name=?", (name,)); ex = cursor.fetchone()
    if ex: pid = ex["id"]
    else: cursor.execute("INSERT INTO producers (name) VALUES (?)", (name,)); conn.commit(); pid = cursor.lastrowid
    cursor.close(); conn.close(); return pid

def link_anime_producer(anime_id, producer_id, role):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO anime_producers (anime_id, producer_id, role) VALUES (?,?,?)", (anime_id, producer_id, role))
    conn.commit(); cursor.close(); conn.close()

def insert_anime_titles(anime_id, titles):
    conn = get_connection(); cursor = conn.cursor()
    for t in titles:
        cursor.execute("INSERT INTO anime_titles (anime_id, title, type) VALUES (?,?,?)", (anime_id, t.get("title"), t.get("type")))
    conn.commit(); cursor.close(); conn.close()

def get_user_stats(user_id):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM watch_history WHERE user_id=?", (user_id,)); tw = cursor.fetchone()[0]
    cursor.execute("SELECT status, COUNT(*) FROM watchlists WHERE user_id=? GROUP BY status", (user_id,))
    wc = {r[0]: r[1] for r in cursor.fetchall()}
    cursor.execute("""
        SELECT g.name, COUNT(*) as c
        FROM watch_history wh
        JOIN anime_genres ag ON wh.anime_id=ag.anime_id
        JOIN genres g ON ag.genre_id=g.id
        WHERE wh.user_id=?
        GROUP BY g.id
        ORDER BY c DESC LIMIT 5
    """, (user_id,))
    fg = [dict(r) for r in cursor.fetchall()]
    cursor.close(); conn.close()
    return {"total_watched": tw, "watchlist_counts": wc, "favorite_genres": fg}

def get_personalized_recommendations(user_id, limit=6):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("SELECT ag.genre_id, COUNT(*) as c FROM watch_history wh JOIN anime_genres ag ON wh.anime_id=ag.anime_id WHERE wh.user_id=? GROUP BY ag.genre_id ORDER BY c DESC LIMIT 3", (user_id,))
    tgs = [r[0] for r in cursor.fetchall()]
    if not tgs:
        cursor.execute("SELECT * FROM animes ORDER BY score DESC LIMIT ?", (limit,))
    else:
        ph = ",".join(["?"]*len(tgs))
        cursor.execute(f"""
            SELECT DISTINCT a.*
            FROM animes a
            JOIN anime_genres ag ON a.id=ag.anime_id
            WHERE ag.genre_id IN ({ph})
            AND a.id NOT IN (SELECT anime_id FROM watch_history WHERE user_id=?)
            ORDER BY a.score DESC LIMIT ?
        """, (*tgs, user_id, limit))
    res = [dict(r) for r in cursor.fetchall()]; cursor.close(); conn.close()
    return res

def serialize_for_json(obj):
    if isinstance(obj, sqlite3.Row): return dict(obj)
    if isinstance(obj, list): return [serialize_for_json(i) for i in obj]
    return obj

if __name__ == "__main__": init_database(); print("Database initialized.")
