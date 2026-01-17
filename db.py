"""
SQLite Veritabanı İşlemleri
"""

import sqlite3
from sqlite3 import Error
from config import DB_PATH

def get_connection():
    """Veritabanı bağlantısı oluştur."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Dict-like access için
        return conn
    except Error as e:
        print(f"[DB] Bağlantı hatası: {e}")
        return None

def init_database():
    """
    Veritabanı tablolarını oluştur.
    """
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    # Ana anime tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS animes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mal_id INTEGER UNIQUE NOT NULL,
        title TEXT NOT NULL,
        title_english TEXT,
        title_japanese TEXT,
        type TEXT,
        episodes INTEGER DEFAULT 0,
        status TEXT,
        score REAL,
        rating TEXT,
        popularity INTEGER,
        members INTEGER,
        favorites INTEGER,
        synopsis TEXT,
        background TEXT,
        year INTEGER,
        season TEXT,
        aired_from DATE,
        aired_to DATE,
        duration TEXT,
        broadcast TEXT,
        cover_url TEXT,
        cover_local TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Kullanıcılar tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Bölümler tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS episodes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        anime_id INTEGER NOT NULL,
        episode_number INTEGER NOT NULL,
        title TEXT,
        aired DATE,
        FOREIGN KEY (anime_id) REFERENCES animes(id)
    )
    """)

    # Video linkleri tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS video_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        episode_id INTEGER NOT NULL,
        source_id INTEGER,
        video_url TEXT NOT NULL,
        quality TEXT,
        fansub TEXT,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (episode_id) REFERENCES episodes(id),
        FOREIGN KEY (source_id) REFERENCES sources(id)
    )
    """)

    # Migration for video_links table
    try:
        # Check if video_url column exists, if not rename url to video_url
        cursor.execute("PRAGMA table_info(video_links)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'url' in columns and 'video_url' not in columns:
            cursor.execute("ALTER TABLE video_links RENAME COLUMN url TO video_url")

        # Add source_id if missing
        if 'source_id' not in columns:
            cursor.execute("ALTER TABLE video_links ADD COLUMN source_id INTEGER")

        # Add fansub if missing
        if 'fansub' not in columns:
            cursor.execute("ALTER TABLE video_links ADD COLUMN fansub TEXT")

        # Add timestamps if missing
        if 'created_at' not in columns:
            cursor.execute("ALTER TABLE video_links ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        if 'updated_at' not in columns:
            cursor.execute("ALTER TABLE video_links ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    except sqlite3.OperationalError:
        pass

    # İzleme geçmişi
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS watch_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        anime_id INTEGER NOT NULL,
        episode_number INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (anime_id) REFERENCES animes(id),
        UNIQUE(user_id, anime_id)
    )
    """)

    # İzleme listesi
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
    )
    """)

    # Yorumlar tablosu (Threaded support)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        anime_id INTEGER NOT NULL,
        episode_number INTEGER NOT NULL,
        content TEXT NOT NULL,
        is_spoiler BOOLEAN DEFAULT 0,
        parent_id INTEGER DEFAULT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (anime_id) REFERENCES animes(id),
        FOREIGN KEY (parent_id) REFERENCES comments(id)
    )
    """)

    # Bildirimler tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        type TEXT NOT NULL, -- 'reply', 'system', 'update'
        message TEXT NOT NULL,
        link TEXT,
        is_read BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    # Favoriler tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS favorites (
        user_id INTEGER NOT NULL,
        anime_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, anime_id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (anime_id) REFERENCES animes(id)
    )
    """)

    # Kullanıcı Aktivite Akışı
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_activity (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        type TEXT NOT NULL, -- 'watch', 'favorite', 'comment', 'follow'
        anime_id INTEGER,
        target_user_id INTEGER, -- For follows
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (anime_id) REFERENCES animes(id),
        FOREIGN KEY (target_user_id) REFERENCES users(id)
    )
    """)

    # Takip Sistemi
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS follows (
        follower_id INTEGER NOT NULL,
        followed_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (follower_id, followed_id),
        FOREIGN KEY (follower_id) REFERENCES users(id),
        FOREIGN KEY (followed_id) REFERENCES users(id)
    )
    """)

    # Migration: Add parent_id to comments if it doesn't exist
    try:
        cursor.execute("ALTER TABLE comments ADD COLUMN parent_id INTEGER DEFAULT NULL")
    except sqlite3.OperationalError:
        # Column already exists
        pass

    # Türler tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS genres (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    """)

    # Anime-Tür ilişki tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS anime_genres (
        anime_id INTEGER NOT NULL,
        genre_id INTEGER NOT NULL,
        FOREIGN KEY (anime_id) REFERENCES animes(id),
        FOREIGN KEY (genre_id) REFERENCES genres(id),
        PRIMARY KEY (anime_id, genre_id)
    )
    """)

    # Temalar tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS themes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    """)

    # Anime-Tema ilişki tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS anime_themes (
        anime_id INTEGER NOT NULL,
        theme_id INTEGER NOT NULL,
        FOREIGN KEY (anime_id) REFERENCES animes(id),
        FOREIGN KEY (theme_id) REFERENCES themes(id),
        PRIMARY KEY (anime_id, theme_id)
    )
    """)

    # Stüdyolar tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS studios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    """)

    # Anime-Stüdyo ilişki tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS anime_studios (
        anime_id INTEGER NOT NULL,
        studio_id INTEGER NOT NULL,
        FOREIGN KEY (anime_id) REFERENCES animes(id),
        FOREIGN KEY (studio_id) REFERENCES studios(id),
        PRIMARY KEY (anime_id, studio_id)
    )
    """)

    # Yapımcılar/Lisansörler tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS producers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    """)

    # Anime-Yapımcı ilişki tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS anime_producers (
        anime_id INTEGER NOT NULL,
        producer_id INTEGER NOT NULL,
        role TEXT NOT NULL,  -- 'producer' veya 'licensor'
        FOREIGN KEY (anime_id) REFERENCES animes(id),
        FOREIGN KEY (producer_id) REFERENCES producers(id),
        PRIMARY KEY (anime_id, producer_id, role)
    )
    """)

    # Kaynaklar tablosu (animecix, turkanime, vb.)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        base_url TEXT,
        is_active BOOLEAN DEFAULT 1
    )
    """)

    # Anime-Kaynak eşleşmeleri
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
    )
    """)

    # İncelemeler (Reviews) tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        anime_id INTEGER NOT NULL,
        score INTEGER NOT NULL,
        title TEXT,
        content TEXT NOT NULL,
        is_spoiler BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (anime_id) REFERENCES animes(id),
        UNIQUE(user_id, anime_id)
    )
    """)

    # İnceleme Oyları (Review Votes)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS review_votes (
        review_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        vote INTEGER NOT NULL, -- 1: Faydalı, -1: Faydalı Değil
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (review_id, user_id),
        FOREIGN KEY (review_id) REFERENCES reviews(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    return True

def get_anime_by_mal_id(mal_id: int):
    """MAL ID ile anime'yi getir."""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM animes WHERE mal_id = ?", (mal_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return dict(result) if result else None

def get_user_by_username(username):
    conn = get_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return dict(result) if result else None

def create_user(username, email, password_hash):
    conn = get_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
        """, (username, email, password_hash))
        conn.commit()
        user_id = cursor.lastrowid
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        cursor.close()
        conn.close()

# Basit placeholder fonksiyonları
def serialize_for_json(data):
    """JSON serileştirme için basit versiyon."""
    if isinstance(data, list):
        return [serialize_for_json(i) for i in data]
    if isinstance(data, sqlite3.Row):
        return dict(data)
    if isinstance(data, dict):
        return {k: serialize_for_json(v) for k, v in data.items()}
    return data

def add_comment(user_id, anime_id, episode_number, content, is_spoiler=False, parent_id=None):
    """Yorum ekle."""
    conn = get_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO comments (user_id, anime_id, episode_number, content, is_spoiler, parent_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, anime_id, episode_number, content, is_spoiler, parent_id))
    conn.commit()
    comment_id = cursor.lastrowid

    # If it's a reply, notify the parent comment owner
    if parent_id:
        cursor.execute("SELECT user_id, content FROM comments WHERE id = ?", (parent_id,))
        parent = cursor.fetchone()
        if parent and parent["user_id"] != user_id:
            cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
            replier = cursor.fetchone()

            cursor.execute("SELECT mal_id FROM animes WHERE id = ?", (anime_id,))
            anime = cursor.fetchone()

            msg = f"{replier['username']} replied to your comment: \"{content[:30]}...\""
            link = f"/player?mal_id={anime['mal_id']}&ep={episode_number}#comment-{comment_id}"

            add_notification(parent["user_id"], 'reply', msg, link)

    cursor.close()
    conn.close()
    return comment_id

def get_comments(anime_id, episode_number):
    """Bölüm yorumlarını getir (Threaded)."""
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, u.username
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.anime_id = ? AND c.episode_number = ?
        ORDER BY c.created_at ASC
    """, (anime_id, episode_number))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # Build thread structure
    comments = [dict(row) for row in rows]
    comment_map = {c['id']: c for c in comments}
    root_comments = []

    for c in comments:
        c['replies'] = []
        if c['parent_id'] and c['parent_id'] in comment_map:
            comment_map[c['parent_id']]['replies'].append(c)
        else:
            root_comments.append(c)

    # Reverse root comments to show newest first
    root_comments.reverse()
    return root_comments

def get_episode_comments(anime_id, episode_number):
    """Alias for get_comments."""
    return get_comments(anime_id, episode_number)

def add_notification(user_id, type, message, link=None):
    """Bildirim ekle."""
    conn = get_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO notifications (user_id, type, message, link)
        VALUES (?, ?, ?, ?)
    """, (user_id, type, message, link))
    conn.commit()
    notif_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return notif_id

def get_unread_notifications(user_id, limit=20):
    """Okunmamış bildirimleri getir."""
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM notifications
        WHERE user_id = ? AND is_read = 0
        ORDER BY created_at DESC
        LIMIT ?
    """, (user_id, limit))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(row) for row in rows]

def mark_notifications_read(user_id, notification_ids=None):
    """Bildirimleri okundu olarak işaretle."""
    conn = get_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    if notification_ids:
        placeholders = ",".join(["?"] * len(notification_ids))
        cursor.execute(f"UPDATE notifications SET is_read = 1 WHERE user_id = ? AND id IN ({placeholders})", [user_id] + notification_ids)
    else:
        cursor.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return True

def delete_comment(comment_id, user_id):
    """Yorum sil."""
    conn = get_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    cursor.execute("DELETE FROM comments WHERE id = ? AND user_id = ?", (comment_id, user_id))
    affected = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    return affected > 0

def get_trending_anime(limit=10, days=7):
    """Trend anime'leri getir."""
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.*, COUNT(wh.id) as watch_count
        FROM animes a
        LEFT JOIN watch_history wh ON a.id = wh.anime_id
        GROUP BY a.id
        ORDER BY watch_count DESC
        LIMIT ?
    """, (limit,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def get_personalized_recommendations(user_id, limit=5):
    """Kişiselleştirilmiş öneriler."""
    # Basit versiyon - rastgele anime döndür
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM animes ORDER BY RANDOM() LIMIT ?", (limit,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def discover_animes(filters, limit=24, offset=0):
    """Anime keşfet (Gelişmiş Filtreleme)."""
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor()

    query = "SELECT DISTINCT a.* FROM animes a"
    params = []
    where_clauses = []

    # Filter: Genres (AND Logic)
    if filters.get("genres"):
        # Convert to list of ints
        try:
            genre_ids = [int(g) for g in filters["genres"] if g]
            if genre_ids:
                placeholders = ",".join(["?"] * len(genre_ids))
                # Subquery to ensure anime has ALL selected genres
                where_clauses.append(f"""
                    (SELECT COUNT(*) FROM anime_genres ag
                     WHERE ag.anime_id = a.id AND ag.genre_id IN ({placeholders})) = ?
                """)
                params.extend(genre_ids)
                params.append(len(genre_ids))
        except ValueError:
            pass

    # Filter: Type
    if filters.get("type"):
        where_clauses.append("a.type = ?")
        params.append(filters["type"])

    # Filter: Status
    if filters.get("status"):
        where_clauses.append("a.status = ?")
        params.append(filters["status"])

    # Filter: Year
    if filters.get("year"):
        # Exact year
        try:
            where_clauses.append("a.year = ?")
            params.append(int(filters["year"]))
        except ValueError:
            pass
    elif filters.get("year_min") or filters.get("year_max"):
        # Range
        if filters.get("year_min"):
            where_clauses.append("a.year >= ?")
            params.append(int(filters["year_min"]))
        if filters.get("year_max"):
            where_clauses.append("a.year <= ?")
            params.append(int(filters["year_max"]))

    # Filter: Score
    if filters.get("min_score"):
        where_clauses.append("a.score >= ?")
        params.append(float(filters["min_score"]))

    # Construct WHERE
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    # Sort
    sort = filters.get("sort", "popularity")
    if sort == "popularity":
        # Popularity (Rank) should be ASC, but Members should be DESC.
        # Let's use members count as it's more direct for "Most Popular".
        query += " ORDER BY a.members DESC NULLS LAST, a.popularity ASC NULLS LAST"
    elif sort == "score":
        query += " ORDER BY a.score DESC NULLS LAST"
    elif sort == "newest":
        query += " ORDER BY a.id DESC"
    elif sort == "title":
        query += " ORDER BY a.title ASC"
    else:
        query += " ORDER BY a.score DESC NULLS LAST"

    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    try:
        cursor.execute(query, params)
        results = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"[DB] Discover Error: {e}")
        results = []

    cursor.close()
    conn.close()
    return results

# Diğer basit placeholder fonksiyonları
def get_user_by_id(user_id):
    conn = get_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

def log_activity(user_id, type, anime_id=None, target_user_id=None, message=None, cursor=None):
    """Kullanıcı aktivitesini kaydet."""
    query = """
        INSERT INTO user_activity (user_id, type, anime_id, target_user_id, message)
        VALUES (?, ?, ?, ?, ?)
    """
    params = (user_id, type, anime_id, target_user_id, message)

    if cursor:
        cursor.execute(query, params)
        return True

    conn = get_connection()
    if not conn: return False
    try:
        conn.execute(query, params)
        conn.commit()
        return True
    except: return False
    finally: conn.close()

def get_user_stats(user_id):
    """Kullanıcı istatistiklerini hesapla."""
    conn = get_connection()
    if not conn: return {}
    cursor = conn.cursor()

    # İzlenen anime sayısı
    cursor.execute("SELECT COUNT(*) FROM watch_history WHERE user_id = ?", (user_id,))
    total_watched = cursor.fetchone()[0]

    # Toplam izlenen bölüm (tahmini)
    cursor.execute("SELECT SUM(episode_number) FROM watch_history WHERE user_id = ?", (user_id,))
    total_episodes = cursor.fetchone()[0] or 0

    # Favori sayısı
    cursor.execute("SELECT COUNT(*) FROM favorites WHERE user_id = ?", (user_id,))
    total_favorites = cursor.fetchone()[0]

    # Takipçi ve Takip edilen
    cursor.execute("SELECT COUNT(*) FROM follows WHERE followed_id = ?", (user_id,))
    followers = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM follows WHERE follower_id = ?", (user_id,))
    following = cursor.fetchone()[0]

    # İzleme listesi dağılımı
    cursor.execute("SELECT status, COUNT(*) as count FROM watchlists WHERE user_id = ? GROUP BY status", (user_id,))
    watchlist_counts = {row["status"]: row["count"] for row in cursor.fetchall()}

    cursor.close()
    conn.close()

    return {
        "total_watched": total_watched,
        "total_episodes": total_episodes,
        "total_favorites": total_favorites,
        "followers": followers,
        "following": following,
        "watchlist_counts": watchlist_counts
    }

def toggle_favorite(user_id, mal_id):
    """Favoriye ekle/çıkar."""
    anime = get_anime_by_mal_id(mal_id)
    if not anime: return None

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM favorites WHERE user_id = ? AND anime_id = ?", (user_id, anime["id"]))
    is_fav = cursor.fetchone()

    if is_fav:
        cursor.execute("DELETE FROM favorites WHERE user_id = ? AND anime_id = ?", (user_id, anime["id"]))
        action = "removed"
    else:
        cursor.execute("INSERT INTO favorites (user_id, anime_id) VALUES (?, ?)", (user_id, anime["id"]))
        action = "added"
        log_activity(user_id, "favorite", anime_id=anime["id"], message=f"Added {anime['title']} to favorites", cursor=cursor)

    conn.commit()
    cursor.close()
    conn.close()
    return action

def is_favorite(user_id, mal_id):
    anime = get_anime_by_mal_id(mal_id)
    if not anime: return False
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM favorites WHERE user_id = ? AND anime_id = ?", (user_id, anime["id"]))
    res = cursor.fetchone()
    conn.close()
    return res is not None

def get_user_favorites(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.* FROM animes a
        JOIN favorites f ON a.id = f.anime_id
        WHERE f.user_id = ?
        ORDER BY f.created_at DESC
    """, (user_id,))
    res = cursor.fetchall()
    conn.close()
    return res

def get_user_activity(user_id, limit=20):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ua.*, a.title as anime_title, a.mal_id, u.username as target_username
        FROM user_activity ua
        LEFT JOIN animes a ON ua.anime_id = a.id
        LEFT JOIN users u ON ua.target_user_id = u.id
        WHERE ua.user_id = ?
        ORDER BY ua.created_at DESC
        LIMIT ?
    """, (user_id, limit))
    res = cursor.fetchall()
    conn.close()
    return res

def toggle_follow(follower_id, followed_id):
    if follower_id == followed_id: return None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM follows WHERE follower_id = ? AND followed_id = ?", (follower_id, followed_id))
    exists = cursor.fetchone()

    if exists:
        cursor.execute("DELETE FROM follows WHERE follower_id = ? AND followed_id = ?", (follower_id, followed_id))
        action = "unfollowed"
    else:
        cursor.execute("INSERT INTO follows (follower_id, followed_id) VALUES (?, ?)", (follower_id, followed_id))
        action = "followed"
        target_user = get_user_by_id(followed_id)
        log_activity(follower_id, "follow", target_user_id=followed_id, message=f"Started following {target_user['username']}", cursor=cursor)
        add_notification(followed_id, "social", f"Someone started following you!", f"/user/{get_user_by_id(follower_id)['username']}")

    conn.commit()
    conn.close()
    return action

def is_following(follower_id, followed_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM follows WHERE follower_id = ? AND followed_id = ?", (follower_id, followed_id))
    res = cursor.fetchone()
    conn.close()
    return res is not None

def get_social_feed(user_id, limit=50):
    """Takip edilen kişilerin aktivitelerini getir."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ua.*, u.username, a.title as anime_title, a.mal_id, tu.username as target_username
        FROM user_activity ua
        JOIN users u ON ua.user_id = u.id
        JOIN follows f ON f.followed_id = ua.user_id
        LEFT JOIN animes a ON ua.anime_id = a.id
        LEFT JOIN users tu ON ua.target_user_id = tu.id
        WHERE f.follower_id = ?
        ORDER BY ua.created_at DESC
        LIMIT ?
    """, (user_id, limit))
    res = cursor.fetchall()
    conn.close()
    return res

def get_top_watchers(limit=10):
    """En çok izleyen kullanıcıları getir."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.username,
               COUNT(wh.id) as anime_count,
               IFNULL(SUM(wh.episode_number), 0) as total_episodes
        FROM users u
        LEFT JOIN watch_history wh ON u.id = wh.user_id
        GROUP BY u.id
        ORDER BY total_episodes DESC
        LIMIT ?
    """, (limit,))
    res = cursor.fetchall()
    conn.close()
    return [dict(row) for row in res]

def update_watch_history(user_id, anime_id, episode_number, progress=0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO watch_history (user_id, anime_id, episode_number)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, anime_id) DO UPDATE SET
            episode_number = MAX(episode_number, excluded.episode_number),
            updated_at = CURRENT_TIMESTAMP
    """, (user_id, anime_id, episode_number))

    anime = cursor.execute("SELECT title FROM animes WHERE id = ?", (anime_id,)).fetchone()
    log_activity(user_id, "watch", anime_id=anime_id, message=f"Watched Episode {episode_number} of {anime['title']}", cursor=cursor)

    conn.commit()
    conn.close()

def update_watchlist(user_id, anime_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO watchlists (user_id, anime_id, status)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, anime_id) DO UPDATE SET
            status = excluded.status
    """, (user_id, anime_id, status))

    anime = cursor.execute("SELECT title FROM animes WHERE id = ?", (anime_id,)).fetchone()
    log_activity(user_id, "watchlist", anime_id=anime_id, message=f"Moved {anime['title']} to {status}", cursor=cursor)

    conn.commit()
    conn.close()

def get_user_watchlist(user_id):
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM watchlists WHERE user_id = ?", (user_id,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def get_user_watch_history(user_id, limit=50):
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    cursor.execute("""
        SELECT wh.*, a.title, a.mal_id, a.cover_local, a.cover_url
        FROM watch_history wh
        JOIN animes a ON wh.anime_id = a.id
        WHERE wh.user_id = ?
        ORDER BY wh.updated_at DESC
        LIMIT ?
    """, (user_id, limit))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(row) for row in results]

def get_anime_full_details(mal_id: int):
    """Anime'nin tüm detaylarını getir (bölümler, türler ile birlikte)."""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()

    # Ana anime bilgilerini al
    cursor.execute("SELECT * FROM animes WHERE mal_id = ?", (mal_id,))
    anime_row = cursor.fetchone()

    if not anime_row:
        cursor.close()
        conn.close()
        return None

    # sqlite3.Row'u dict'e çevir
    anime = dict(anime_row)

    # Bölümleri al
    cursor.execute("""
        SELECT e.*, COUNT(vl.id) as video_count
        FROM episodes e
        LEFT JOIN video_links vl ON e.id = vl.episode_id
        WHERE e.anime_id = ?
        GROUP BY e.id
        ORDER BY e.episode_number
    """, (anime["id"],))
    anime["episodes_list"] = [dict(row) for row in cursor.fetchall()]

    # Türleri al
    cursor.execute("""
        SELECT g.name
        FROM genres g
        JOIN anime_genres ag ON g.id = ag.genre_id
        WHERE ag.anime_id = ?
        ORDER BY g.name
    """, (anime["id"],))
    anime["genres"] = [row["name"] for row in cursor.fetchall()]

    cursor.close()
    conn.close()
    return anime

def insert_or_update_anime(anime_data):
    """Anime'yi ekle veya güncelle."""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()

    # Önce mevcut anime'yi kontrol et
    cursor.execute("SELECT id FROM animes WHERE mal_id = ?", (anime_data["mal_id"],))
    existing = cursor.fetchone()

    if existing:
        # Güncelle
        cursor.execute("""
            UPDATE animes SET
                title = ?, title_english = ?, title_japanese = ?,
                type = ?, episodes = ?, status = ?, score = ?,
                rating = ?, popularity = ?, members = ?, favorites = ?,
                synopsis = ?, background = ?,
                year = ?, season = ?, aired_from = ?, aired_to = ?,
                duration = ?, broadcast = ?,
                cover_url = ?, cover_local = ?, updated_at = CURRENT_TIMESTAMP
            WHERE mal_id = ?
        """, (
            anime_data.get("title"), anime_data.get("title_english"), anime_data.get("title_japanese"),
            anime_data.get("type"), anime_data.get("episodes", 0), anime_data.get("status"), anime_data.get("score"),
            anime_data.get("rating"), anime_data.get("popularity"), anime_data.get("members"), anime_data.get("favorites"),
            anime_data.get("synopsis"), anime_data.get("background"),
            anime_data.get("year"), anime_data.get("season"), anime_data.get("aired_from"), anime_data.get("aired_to"),
            anime_data.get("duration"), anime_data.get("broadcast"),
            anime_data.get("cover_url"), anime_data.get("cover_local"),
            anime_data["mal_id"]
        ))
        anime_id = existing["id"]
    else:
        # Yeni ekle
        cursor.execute("""
            INSERT INTO animes (
                mal_id, title, title_english, title_japanese,
                type, episodes, status, score,
                rating, popularity, members, favorites,
                synopsis, background,
                year, season, aired_from, aired_to,
                duration, broadcast,
                cover_url, cover_local
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            anime_data["mal_id"], anime_data.get("title"), anime_data.get("title_english"), anime_data.get("title_japanese"),
            anime_data.get("type"), anime_data.get("episodes", 0), anime_data.get("status"), anime_data.get("score"),
            anime_data.get("rating"), anime_data.get("popularity"), anime_data.get("members"), anime_data.get("favorites"),
            anime_data.get("synopsis"), anime_data.get("background"),
            anime_data.get("year"), anime_data.get("season"), anime_data.get("aired_from"), anime_data.get("aired_to"),
            anime_data.get("duration"), anime_data.get("broadcast"),
            anime_data.get("cover_url"), anime_data.get("cover_local")
        ))
        anime_id = cursor.lastrowid

    conn.commit()
    cursor.close()
    conn.close()
    return anime_id

def insert_anime_titles(anime_id, titles):
    """Anime başlıklarını ekle."""
    # Basit versiyon - şimdilik sadece ana başlığı kullan
    pass

def insert_or_get_genre(name):
    """Türü ekle veya mevcut olanı getir."""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()

    # Önce mevcut türü kontrol et
    cursor.execute("SELECT id FROM genres WHERE name = ?", (name,))
    existing = cursor.fetchone()

    if existing:
        genre_id = existing["id"]
    else:
        # Yeni tür ekle
        cursor.execute("INSERT INTO genres (name) VALUES (?)", (name,))
        genre_id = cursor.lastrowid
        conn.commit()

    cursor.close()
    conn.close()
    return genre_id

def link_anime_genre(anime_id, genre_id):
    """Anime ve tür arasında ilişki oluştur."""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    # Önce mevcut ilişkiyi kontrol et
    cursor.execute("SELECT 1 FROM anime_genres WHERE anime_id = ? AND genre_id = ?", (anime_id, genre_id))
    existing = cursor.fetchone()

    if not existing:
        cursor.execute("INSERT INTO anime_genres (anime_id, genre_id) VALUES (?, ?)", (anime_id, genre_id))
        conn.commit()

    cursor.close()
    conn.close()
    return True

def insert_or_get_theme(name):
    """Temayı ekle veya mevcut olanı getir."""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()

    # Önce mevcut temayı kontrol et
    cursor.execute("SELECT id FROM themes WHERE name = ?", (name,))
    existing = cursor.fetchone()

    if existing:
        theme_id = existing["id"]
    else:
        # Yeni tema ekle
        cursor.execute("INSERT INTO themes (name) VALUES (?)", (name,))
        theme_id = cursor.lastrowid
        conn.commit()

    cursor.close()
    conn.close()
    return theme_id

def link_anime_theme(anime_id, theme_id):
    """Anime ve tema arasında ilişki oluştur."""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    # Önce mevcut ilişkiyi kontrol et
    cursor.execute("SELECT 1 FROM anime_themes WHERE anime_id = ? AND theme_id = ?", (anime_id, theme_id))
    existing = cursor.fetchone()

    if not existing:
        cursor.execute("INSERT INTO anime_themes (anime_id, theme_id) VALUES (?, ?)", (anime_id, theme_id))
        conn.commit()

    cursor.close()
    conn.close()
    return True

def insert_or_get_studio(name):
    """Stüdyoyu ekle veya mevcut olanı getir."""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()

    # Önce mevcut stüdyoyu kontrol et
    cursor.execute("SELECT id FROM studios WHERE name = ?", (name,))
    existing = cursor.fetchone()

    if existing:
        studio_id = existing["id"]
    else:
        # Yeni stüdyo ekle
        cursor.execute("INSERT INTO studios (name) VALUES (?)", (name,))
        studio_id = cursor.lastrowid
        conn.commit()

    cursor.close()
    conn.close()
    return studio_id

def link_anime_studio(anime_id, studio_id):
    """Anime ve stüdyo arasında ilişki oluştur."""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    # Önce mevcut ilişkiyi kontrol et
    cursor.execute("SELECT 1 FROM anime_studios WHERE anime_id = ? AND studio_id = ?", (anime_id, studio_id))
    existing = cursor.fetchone()

    if not existing:
        cursor.execute("INSERT INTO anime_studios (anime_id, studio_id) VALUES (?, ?)", (anime_id, studio_id))
        conn.commit()

    cursor.close()
    conn.close()
    return True

def insert_or_get_producer(name):
    """Yapımcıyı ekle veya mevcut olanı getir."""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()

    # Önce mevcut yapımcıyı kontrol et
    cursor.execute("SELECT id FROM producers WHERE name = ?", (name,))
    existing = cursor.fetchone()

    if existing:
        producer_id = existing["id"]
    else:
        # Yeni yapımcı ekle
        cursor.execute("INSERT INTO producers (name) VALUES (?)", (name,))
        producer_id = cursor.lastrowid
        conn.commit()

    cursor.close()
    conn.close()
    return producer_id

def link_anime_producer(anime_id, producer_id, role):
    """Anime ve yapımcı arasında ilişki oluştur."""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    # Önce mevcut ilişkiyi kontrol et
    cursor.execute("SELECT 1 FROM anime_producers WHERE anime_id = ? AND producer_id = ? AND role = ?", (anime_id, producer_id, role))
    existing = cursor.fetchone()

    if not existing:
        cursor.execute("INSERT INTO anime_producers (anime_id, producer_id, role) VALUES (?, ?, ?)", (anime_id, producer_id, role))
        conn.commit()

    cursor.close()
    conn.close()
    return True

def get_source_id(source_name):
    """Kaynak adından kaynak ID'sini getir, yoksa oluştur."""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()

    # Önce mevcut kaynağı kontrol et
    cursor.execute("SELECT id FROM sources WHERE name = ?", (source_name,))
    existing = cursor.fetchone()

    if existing:
        source_id = existing["id"]
    else:
        # Yeni kaynak ekle
        cursor.execute("INSERT INTO sources (name) VALUES (?)", (source_name,))
        source_id = cursor.lastrowid
        conn.commit()

    cursor.close()
    conn.close()
    return source_id

def insert_or_update_anime_source(anime_id, source_id, source_anime_id, source_slug, source_title):
    """Anime-kaynak eşleşmesini ekle veya güncelle."""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()

    # Önce mevcut eşleşmeyi kontrol et
    cursor.execute("SELECT id FROM anime_sources WHERE anime_id = ? AND source_id = ?", (anime_id, source_id))
    existing = cursor.fetchone()

    if existing:
        # Güncelle
        cursor.execute("""
            UPDATE anime_sources SET
                source_anime_id = ?, source_slug = ?, source_title = ?
            WHERE anime_id = ? AND source_id = ?
        """, (source_anime_id, source_slug, source_title, anime_id, source_id))
        anime_source_id = existing["id"]
    else:
        # Yeni ekle
        cursor.execute("""
            INSERT INTO anime_sources (anime_id, source_id, source_anime_id, source_slug, source_title)
            VALUES (?, ?, ?, ?, ?)
        """, (anime_id, source_id, source_anime_id, source_slug, source_title))
        anime_source_id = cursor.lastrowid

    conn.commit()
    cursor.close()
    conn.close()
    return anime_source_id

def insert_or_update_episode(anime_id, episode_number, title):
    """Bölümü ekle veya güncelle."""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()

    # Önce mevcut bölümü kontrol et
    cursor.execute("SELECT id FROM episodes WHERE anime_id = ? AND episode_number = ?", (anime_id, episode_number))
    existing = cursor.fetchone()

    if existing:
        # Güncelle
        cursor.execute("""
            UPDATE episodes SET
                title = ?, aired = CURRENT_DATE
            WHERE anime_id = ? AND episode_number = ?
        """, (title, anime_id, episode_number))
        episode_id = existing["id"]
    else:
        # Yeni ekle
        cursor.execute("""
            INSERT INTO episodes (anime_id, episode_number, title, aired)
            VALUES (?, ?, ?, CURRENT_DATE)
        """, (anime_id, episode_number, title))
        episode_id = cursor.lastrowid

    conn.commit()
    cursor.close()
    conn.close()
    return episode_id

def get_anime_sources(mal_id: int):
    """Anime'nin mevcut kaynaklarını getir."""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.name as source_name, s.id as source_id, asrc.source_slug, asrc.source_anime_id
        FROM anime_sources asrc
        JOIN sources s ON asrc.source_id = s.id
        JOIN animes a ON asrc.anime_id = a.id
        WHERE a.mal_id = ? AND s.is_active = 1
    """, (mal_id,))

    results = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return results

def get_all_mal_ids():
    """Tüm anime'lerin MAL ID'lerini getir."""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    cursor.execute("SELECT mal_id FROM animes")
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return [row["mal_id"] for row in results]

def get_genres():
    """Tüm türleri getir."""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM genres ORDER BY name")
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def get_anime_by_title(title_query, limit=50):
    """Başlığa göre anime ara."""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    # Search in titles and title_english
    cursor.execute("""
        SELECT * FROM animes
        WHERE title LIKE ? OR title_english LIKE ?
        ORDER BY
            CASE
                WHEN title LIKE ? THEN 1
                WHEN title_english LIKE ? THEN 2
                ELSE 3
            END,
            score DESC
        LIMIT ?
    """, (f"%{title_query}%", f"%{title_query}%", f"{title_query}%", f"{title_query}%", limit))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def get_live_search_results(query, limit=5):
    """Live search için hızlı sonuçlar."""
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    cursor.execute("""
        SELECT mal_id, title, cover_url, cover_local, type, score, year
        FROM animes
        WHERE title LIKE ? OR title_english LIKE ?
        ORDER BY
            CASE
                WHEN title LIKE ? THEN 1
                WHEN title_english LIKE ? THEN 2
                ELSE 3
            END,
            score DESC
        LIMIT ?
    """, (f"%{query}%", f"%{query}%", f"{query}%", f"{query}%", limit))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(row) for row in rows]

def insert_video_link(episode_id, source_id, video_url, quality, fansub):
    """Video linkini ekle."""
    conn = get_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO video_links (episode_id, source_id, video_url, quality, fansub)
            VALUES (?, ?, ?, ?, ?)
        """, (episode_id, source_id, video_url, quality, fansub))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"[DB] insert_video_link error: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def delete_video_links_for_episode(anime_id, episode_number):
    """Bölümün video linklerini sil."""
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    try:
        cursor.execute("""
            DELETE FROM video_links
            WHERE episode_id IN (SELECT id FROM episodes WHERE anime_id = ? AND episode_number = ?)
        """, (anime_id, episode_number))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def remove_dead_video_link(video_id):
    """Video linkini pasif yap."""
    conn = get_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE video_links SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (video_id,))
        conn.commit()
        return True
    finally:
        cursor.close()
        conn.close()

def get_video_links(anime_id: int, episode_number: int = None):
    """Anime'nin video linklerini getir. Episode number verilirse sadece o bölümün linklerini döndür."""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    
    if episode_number:
        # Belirli bölümün video linkleri
        cursor.execute("""
            SELECT vl.*, e.episode_number, e.title as episode_title, s.name as source_name
            FROM video_links vl
            JOIN episodes e ON vl.episode_id = e.id
            LEFT JOIN sources s ON vl.source_id = s.id
            WHERE e.anime_id = ? AND e.episode_number = ? AND vl.is_active = 1
            ORDER BY vl.quality DESC, vl.fansub
        """, (anime_id, episode_number))
    else:
        # Tüm video linkleri
        cursor.execute("""
            SELECT vl.*, e.episode_number, e.title as episode_title, s.name as source_name
            FROM video_links vl
            JOIN episodes e ON vl.episode_id = e.id
            LEFT JOIN sources s ON vl.source_id = s.id
            WHERE e.anime_id = ? AND vl.is_active = 1
            ORDER BY e.episode_number, vl.quality DESC, vl.fansub
        """, (anime_id,))

    results = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return results

def get_episode_by_number(anime_id: int, episode_number: int):
    """Anime ID ve bölüm numarasına göre bölümü getir."""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM episodes
        WHERE anime_id = ? AND episode_number = ?
    """, (anime_id, episode_number))
    
    episode = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return dict(episode) if episode else None

def add_review(user_id, anime_id, score, title, content, is_spoiler=False):
    """Add or update a user review for an anime."""
    conn = get_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO reviews (user_id, anime_id, score, title, content, is_spoiler)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, anime_id) DO UPDATE SET
                score = excluded.score,
                title = excluded.title,
                content = excluded.content,
                is_spoiler = excluded.is_spoiler,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, anime_id, score, title, content, int(is_spoiler)))
        conn.commit()
        return cursor.lastrowid or True
    except sqlite3.Error as e:
        print(f"[DB] add_review error: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_reviews_by_anime(anime_id, current_user_id=None):
    """Get all reviews for an anime with user info and vote counts."""
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor()

    query = """
        SELECT
            r.*,
            u.username,
            (SELECT COUNT(*) FROM review_votes WHERE review_id = r.id AND vote = 1) as helpful_count,
            (SELECT COUNT(*) FROM review_votes WHERE review_id = r.id AND vote = -1) as unhelpful_count
    """

    if current_user_id:
        query += ", (SELECT vote FROM review_votes WHERE review_id = r.id AND user_id = ?) as user_vote "
        params = (current_user_id, anime_id)
    else:
        params = (anime_id,)

    query += """
        FROM reviews r
        JOIN users u ON r.user_id = u.id
        WHERE r.anime_id = ?
        ORDER BY helpful_count DESC, r.created_at DESC
    """

    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def vote_review(review_id, user_id, vote):
    """Vote (helpful/unhelpful) on a review."""
    conn = get_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO review_votes (review_id, user_id, vote)
            VALUES (?, ?, ?)
            ON CONFLICT(review_id, user_id) DO UPDATE SET
                vote = excluded.vote
        """, (review_id, user_id, vote))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"[DB] vote_review error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def delete_review(review_id, user_id):
    """Delete a review if it belongs to the user."""
    conn = get_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM reviews WHERE id = ? AND user_id = ?", (review_id, user_id))
        if cursor.rowcount > 0:
            cursor.execute("DELETE FROM review_votes WHERE review_id = ?", (review_id,))
            conn.commit()
            return True
        return False
    except sqlite3.Error as e:
        print(f"[DB] delete_review error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("Initializing database...")
    init_database()
