"""
SQLite Database Operations
"""

import sqlite3
import threading
from sqlite3 import Error
from config import DB_PATH

# Thread-local storage for database connections
_local = threading.local()


class ConnectionWrapper:
    """
    Wraps a sqlite3 connection to prevent accidental closing
    while allowing access to all other methods.
    """

    def __init__(self, conn):
        self.conn = conn

    def __getattr__(self, name):
        return getattr(self.conn, name)

    def close(self):
        """
        Don't actually close the connection, just rollback any uncommitted transaction
        to ensure a clean state for the next user.
        """
        try:
            self.conn.rollback()
        except sqlite3.Error:
            pass

    def __enter__(self):
        self.conn.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.conn.__exit__(exc_type, exc_val, exc_tb)


def get_connection():
    """Create database connection (Thread-local pooling)."""
    if not hasattr(_local, "connection") or _local.connection is None:
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            _local.connection = conn
        except Error as e:
            print(f"[DB] Connection error: {e}")
            return None

    return ConnectionWrapper(_local.connection)


def close_thread_connection():
    """Explicitly close the current thread's connection."""
    if hasattr(_local, "connection") and _local.connection:
        try:
            _local.connection.close()
        except sqlite3.Error:
            pass
        finally:
            _local.connection = None


def init_database():
    """
    Create database tables.
    """
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    # Main anime table
    cursor.execute(
        """
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
    """
    )

    # Users table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        xp INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    )

    # Episodes table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS episodes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        anime_id INTEGER NOT NULL,
        episode_number INTEGER NOT NULL,
        title TEXT,
        aired DATE,
        FOREIGN KEY (anime_id) REFERENCES animes(id)
    )
    """
    )

    # Video links table
    cursor.execute(
        """
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
    """
    )

    # Migration for video_links table
    try:
        # Check if video_url column exists, if not rename url to video_url
        cursor.execute("PRAGMA table_info(video_links)")
        columns = [row[1] for row in cursor.fetchall()]
        if "url" in columns and "video_url" not in columns:
            cursor.execute("ALTER TABLE video_links RENAME COLUMN url TO video_url")

        # Add source_id if missing
        if "source_id" not in columns:
            cursor.execute("ALTER TABLE video_links ADD COLUMN source_id INTEGER")

        # Add fansub if missing
        if "fansub" not in columns:
            cursor.execute("ALTER TABLE video_links ADD COLUMN fansub TEXT")

        # Add timestamps if missing
        if "created_at" not in columns:
            cursor.execute(
                "ALTER TABLE video_links ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            )
        if "updated_at" not in columns:
            cursor.execute(
                "ALTER TABLE video_links ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            )
    except sqlite3.OperationalError:
        pass

    # Watch history
    cursor.execute(
        """
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
    )
    """
    )

    # Watchlist
    cursor.execute(
        """
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
    """
    )

    # Comments table (Threaded support)
    cursor.execute(
        """
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
    """
    )

    # Notifications table
    cursor.execute(
        """
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
    """
    )

    # Favorites table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS favorites (
        user_id INTEGER NOT NULL,
        anime_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, anime_id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (anime_id) REFERENCES animes(id)
    )
    """
    )

    # User Activity Feed
    cursor.execute(
        """
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
    """
    )

    # Following System
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS follows (
        follower_id INTEGER NOT NULL,
        followed_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (follower_id, followed_id),
        FOREIGN KEY (follower_id) REFERENCES users(id),
        FOREIGN KEY (followed_id) REFERENCES users(id)
    )
    """
    )

    # Migration: Add parent_id to comments if it doesn't exist
    try:
        cursor.execute("ALTER TABLE comments ADD COLUMN parent_id INTEGER DEFAULT NULL")
    except sqlite3.OperationalError:
        pass

    # Migration: Add progress to watch_history
    try:
        cursor.execute(
            "ALTER TABLE watch_history ADD COLUMN progress INTEGER DEFAULT 0"
        )
    except sqlite3.OperationalError:
        pass

    # Migration: Add XP and Level to users
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN xp INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN level INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        pass

    # Badges table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS badges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        icon TEXT
    )
    """
    )

    # User Badges table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS user_badges (
        user_id INTEGER NOT NULL,
        badge_id INTEGER NOT NULL,
        awarded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, badge_id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (badge_id) REFERENCES badges(id)
    )
    """
    )

    # Initial Badges
    initial_badges = [
        ("Otaku Beginner", "Watch your first episode", "🔰"),
        ("Anime Critic", "Write your first review", "✍️"),
        ("Social Butterfly", "Follow 5 other users", "🦋"),
        ("Rising Star", "Reach Level 5", "⭐"),
        ("Anime Sensei", "Reach Level 10", "👑"),
        ("Collector", "Create 3 collections", "📦"),
    ]
    for name, desc, icon in initial_badges:
        cursor.execute(
            "INSERT OR IGNORE INTO badges (name, description, icon) VALUES (?, ?, ?)",
            (name, desc, icon),
        )

    # Genres table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS genres (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    """
    )

    # Anime-Genre relation table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS anime_genres (
        anime_id INTEGER NOT NULL,
        genre_id INTEGER NOT NULL,
        FOREIGN KEY (anime_id) REFERENCES animes(id),
        FOREIGN KEY (genre_id) REFERENCES genres(id),
        PRIMARY KEY (anime_id, genre_id)
    )
    """
    )

    # Themes table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS themes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    """
    )

    # Anime-Theme relation table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS anime_themes (
        anime_id INTEGER NOT NULL,
        theme_id INTEGER NOT NULL,
        FOREIGN KEY (anime_id) REFERENCES animes(id),
        FOREIGN KEY (theme_id) REFERENCES themes(id),
        PRIMARY KEY (anime_id, theme_id)
    )
    """
    )

    # Studios table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS studios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    """
    )

    # Anime-Studio relation table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS anime_studios (
        anime_id INTEGER NOT NULL,
        studio_id INTEGER NOT NULL,
        FOREIGN KEY (anime_id) REFERENCES animes(id),
        FOREIGN KEY (studio_id) REFERENCES studios(id),
        PRIMARY KEY (anime_id, studio_id)
    )
    """
    )

    # Producers/Licensors table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS producers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    """
    )

    # Anime-Producer relation table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS anime_producers (
        anime_id INTEGER NOT NULL,
        producer_id INTEGER NOT NULL,
        role TEXT NOT NULL,  -- 'producer' or 'licensor'
        FOREIGN KEY (anime_id) REFERENCES animes(id),
        FOREIGN KEY (producer_id) REFERENCES producers(id),
        PRIMARY KEY (anime_id, producer_id, role)
    )
    """
    )

    # Sources table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        base_url TEXT,
        is_active BOOLEAN DEFAULT 1
    )
    """
    )

    # Anime-Source mappings
    cursor.execute(
        """
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
    """
    )

    # Reviews table
    cursor.execute(
        """
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
    """
    )

    # Review Votes
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS review_votes (
        review_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        vote INTEGER NOT NULL, -- 1: Helpful, -1: Not Helpful
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (review_id, user_id),
        FOREIGN KEY (review_id) REFERENCES reviews(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """
    )

    # Collections
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS collections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        is_public BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """
    )

    # Collection Items
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS collection_items (
        collection_id INTEGER NOT NULL,
        anime_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (collection_id, anime_id),
        FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE,
        FOREIGN KEY (anime_id) REFERENCES animes(id) ON DELETE CASCADE
    )
    """
    )

    # Characters
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS characters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mal_id INTEGER UNIQUE NOT NULL,
        name TEXT NOT NULL,
        image_url TEXT,
        about TEXT
    )
    """
    )

    # People (Voice Actors and Staff)
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS people (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mal_id INTEGER UNIQUE NOT NULL,
        name TEXT NOT NULL,
        image_url TEXT
    )
    """
    )

    # Anime Characters
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS anime_characters (
        anime_id INTEGER NOT NULL,
        character_id INTEGER NOT NULL,
        role TEXT,
        PRIMARY KEY (anime_id, character_id),
        FOREIGN KEY (anime_id) REFERENCES animes(id),
        FOREIGN KEY (character_id) REFERENCES characters(id)
    )
    """
    )

    # Character Voice Actors
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS character_voice_actors (
        anime_id INTEGER NOT NULL,
        character_id INTEGER NOT NULL,
        person_id INTEGER NOT NULL,
        language TEXT,
        PRIMARY KEY (anime_id, character_id, person_id),
        FOREIGN KEY (anime_id) REFERENCES animes(id),
        FOREIGN KEY (character_id) REFERENCES characters(id),
        FOREIGN KEY (person_id) REFERENCES people(id)
    )
    """
    )

    # Anime Staff
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS anime_staff (
        anime_id INTEGER NOT NULL,
        person_id INTEGER NOT NULL,
        position TEXT,
        PRIMARY KEY (anime_id, person_id, position),
        FOREIGN KEY (anime_id) REFERENCES animes(id),
        FOREIGN KEY (person_id) REFERENCES people(id)
    )
    """
    )

    conn.commit()
    cursor.close()
    conn.close()
    return True


def get_anime_by_mal_id(mal_id: int):
    """Get anime by MAL ID."""
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
        cursor.execute(
            """
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
        """,
            (username, email, password_hash),
        )
        conn.commit()
        user_id = cursor.lastrowid
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        cursor.close()
        conn.close()


def serialize_for_json(data):
    """Simple version for JSON serialization."""
    if isinstance(data, list):
        return [serialize_for_json(i) for i in data]
    if isinstance(data, sqlite3.Row):
        return dict(data)
    if isinstance(data, dict):
        return {k: serialize_for_json(v) for k, v in data.items()}
    return data


def add_comment(
    user_id, anime_id, episode_number, content, is_spoiler=False, parent_id=None
):
    """Add comment."""
    conn = get_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO comments (user_id, anime_id, episode_number, content, is_spoiler, parent_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (user_id, anime_id, episode_number, content, is_spoiler, parent_id),
    )
    conn.commit()
    comment_id = cursor.lastrowid

    # Award XP for commenting
    add_xp(user_id, 5, "Commented on an episode")

    # If it's a reply, notify the parent comment owner
    if parent_id:
        cursor.execute(
            "SELECT user_id, content FROM comments WHERE id = ?", (parent_id,)
        )
        parent = cursor.fetchone()
        if parent and parent["user_id"] != user_id:
            cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
            replier = cursor.fetchone()

            cursor.execute("SELECT mal_id FROM animes WHERE id = ?", (anime_id,))
            anime = cursor.fetchone()

            msg = (
                f"{replier['username']} replied to your comment: \"{content[:30]}...\""
            )
            link = f"/player?mal_id={anime['mal_id']}&ep={episode_number}#comment-{comment_id}"

            add_notification(parent["user_id"], "reply", msg, link)

    cursor.close()
    conn.close()
    return comment_id


def get_comments(anime_id, episode_number):
    """Get episode comments (Threaded)."""
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT c.*, u.username
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.anime_id = ? AND c.episode_number = ?
        ORDER BY c.created_at ASC
    """,
        (anime_id, episode_number),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # Build thread structure
    comments = [dict(row) for row in rows]
    comment_map = {c["id"]: c for c in comments}
    root_comments = []

    for c in comments:
        c["replies"] = []
        if c["parent_id"] and c["parent_id"] in comment_map:
            comment_map[c["parent_id"]]["replies"].append(c)
        else:
            root_comments.append(c)

    # Reverse root comments to show newest first
    root_comments.reverse()
    return root_comments


def get_episode_comments(anime_id, episode_number):
    """Alias for get_comments."""
    return get_comments(anime_id, episode_number)


def add_notification(user_id, type, message, link=None):
    """Add notification."""
    conn = get_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO notifications (user_id, type, message, link)
        VALUES (?, ?, ?, ?)
    """,
        (user_id, type, message, link),
    )
    conn.commit()
    notif_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return notif_id


def get_unread_notifications(user_id, limit=20):
    """Get unread notifications."""
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM notifications
        WHERE user_id = ? AND is_read = 0
        ORDER BY created_at DESC
        LIMIT ?
    """,
        (user_id, limit),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(row) for row in rows]


def mark_notifications_read(user_id, notification_ids=None):
    """Mark notifications as read."""
    conn = get_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    if notification_ids:
        placeholders = ",".join(["?"] * len(notification_ids))
        cursor.execute(
            f"UPDATE notifications SET is_read = 1 WHERE user_id = ? AND id IN ({placeholders})",
            [user_id] + notification_ids,
        )
    else:
        cursor.execute(
            "UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user_id,)
        )
    conn.commit()
    cursor.close()
    conn.close()
    return True


def delete_comment(comment_id, user_id):
    """Delete comment."""
    conn = get_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM comments WHERE id = ? AND user_id = ?", (comment_id, user_id)
    )
    affected = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    return affected > 0


def get_trending_anime(limit=10, days=7):
    """Get trending anime."""
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT a.*, COUNT(wh.id) as watch_count
        FROM animes a
        LEFT JOIN watch_history wh ON a.id = wh.anime_id
        GROUP BY a.id
        ORDER BY watch_count DESC
        LIMIT ?
    """,
        (limit,),
    )
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results


def get_personalized_recommendations(user_id, limit=5):
    """Personalized recommendations (Genre-based)."""
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor()

    # Find the top 3 genres the user watches/likes most
    cursor.execute(
        """
        SELECT g.id, g.name, COUNT(*) as count
        FROM watch_history wh
        JOIN anime_genres ag ON wh.anime_id = ag.anime_id
        JOIN genres g ON ag.genre_id = g.id
        WHERE wh.user_id = ?
        GROUP BY g.id
        ORDER BY count DESC
        LIMIT 3
    """,
        (user_id,),
    )
    top_genres = cursor.fetchall()

    if not top_genres:
        # Fallback to random if no data
        cursor.execute("SELECT * FROM animes ORDER BY RANDOM() LIMIT ?", (limit,))
        results = cursor.fetchall()
    else:
        genre_ids = [row["id"] for row in top_genres]
        placeholders = ",".join(["?"] * len(genre_ids))

        # Get high-rated anime with these genres that the user hasn't watched yet
        cursor.execute(
            f"""
            SELECT DISTINCT a.* FROM animes a
            JOIN anime_genres ag ON a.id = ag.anime_id
            WHERE ag.genre_id IN ({placeholders})
            AND a.id NOT IN (SELECT anime_id FROM watch_history WHERE user_id = ?)
            ORDER BY a.score DESC, a.popularity ASC
            LIMIT ?
        """,
            (*genre_ids, user_id, limit),
        )
        results = cursor.fetchall()

        # Fill with random if not enough results
        if len(results) < limit:
            needed = limit - len(results)
            existing_ids = [row["id"] for row in results]
            if not existing_ids:
                existing_ids = [-1]
            placeholders_existing = ",".join(["?"] * len(existing_ids))

            cursor.execute(
                f"""
                SELECT * FROM animes
                WHERE id NOT IN ({placeholders_existing})
                AND id NOT IN (SELECT anime_id FROM watch_history WHERE user_id = ?)
                ORDER BY RANDOM()
                LIMIT ?
            """,
                (*existing_ids, user_id, needed),
            )
            results.extend(cursor.fetchall())

    cursor.close()
    conn.close()
    return results


def discover_animes(filters, limit=24, offset=0):
    """Discover anime (Advanced Filtering)."""
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
                where_clauses.append(
                    f"""
                    (SELECT COUNT(*) FROM anime_genres ag
                     WHERE ag.anime_id = a.id AND ag.genre_id IN ({placeholders})) = ?
                """
                )
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


def log_activity(
    user_id, type, anime_id=None, target_user_id=None, message=None, cursor=None
):
    """Log user activity."""
    query = """
        INSERT INTO user_activity (user_id, type, anime_id, target_user_id, message)
        VALUES (?, ?, ?, ?, ?)
    """
    params = (user_id, type, anime_id, target_user_id, message)

    if cursor:
        cursor.execute(query, params)
        return True

    conn = get_connection()
    if not conn:
        return False
    try:
        conn.execute(query, params)
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()


def get_user_stats(user_id):
    """Calculate user statistics."""
    conn = get_connection()
    if not conn:
        return {}
    cursor = conn.cursor()

    # Get User basic info (XP, Level)
    cursor.execute("SELECT xp, level FROM users WHERE id = ?", (user_id,))
    user_row = cursor.fetchone()
    xp = user_row["xp"] if user_row else 0
    level = user_row["level"] if user_row else 1

    # Number of watched anime and total episodes watched
    cursor.execute(
        "SELECT COUNT(*), SUM(episode_number) FROM watch_history WHERE user_id = ?",
        (user_id,),
    )
    row = cursor.fetchone()
    total_watched = row[0]
    total_episodes = row[1] or 0

    # Favorites count, Followers and Following
    cursor.execute(
        """
        SELECT
            (SELECT COUNT(*) FROM favorites WHERE user_id = ?),
            (SELECT COUNT(*) FROM follows WHERE followed_id = ?),
            (SELECT COUNT(*) FROM follows WHERE follower_id = ?)
    """,
        (user_id, user_id, user_id),
    )
    row = cursor.fetchone()
    total_favorites = row[0]
    followers = row[1]
    following = row[2]

    # Watchlist distribution
    cursor.execute(
        "SELECT status, COUNT(*) as count FROM watchlists WHERE user_id = ? GROUP BY status",
        (user_id,),
    )
    watchlist_counts = {row["status"]: row["count"] for row in cursor.fetchall()}

    # Badges
    cursor.execute(
        """
        SELECT b.name, b.icon, b.description FROM badges b
        JOIN user_badges ub ON b.id = ub.badge_id
        WHERE ub.user_id = ?
    """,
        (user_id,),
    )
    badges = [dict(r) for r in cursor.fetchall()]

    cursor.close()
    conn.close()

    # Calculate XP to next level: next_level_xp = (current_level)**2 * 100
    # Current level L was calculated from int(sqrt(xp/100)) + 1
    # So to get to level L+1, you need (L)**2 * 100 XP
    next_level_xp = (level**2) * 100
    current_level_base_xp = ((level - 1) ** 2) * 100

    progress_xp = xp - current_level_base_xp
    needed_xp = next_level_xp - current_level_base_xp
    progress_percent = (
        min(100, int((progress_xp / needed_xp) * 100)) if needed_xp > 0 else 100
    )

    return {
        "xp": xp,
        "level": level,
        "next_level_xp": next_level_xp,
        "progress_percent": progress_percent,
        "total_watched": total_watched,
        "total_episodes": total_episodes,
        "total_favorites": total_favorites,
        "followers": followers,
        "following": following,
        "watchlist_counts": watchlist_counts,
        "badges": badges,
    }


def toggle_favorite(user_id, mal_id):
    """Toggle favorite."""
    anime = get_anime_by_mal_id(mal_id)
    if not anime:
        return None

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM favorites WHERE user_id = ? AND anime_id = ?",
        (user_id, anime["id"]),
    )
    is_fav = cursor.fetchone()

    if is_fav:
        cursor.execute(
            "DELETE FROM favorites WHERE user_id = ? AND anime_id = ?",
            (user_id, anime["id"]),
        )
        action = "removed"
    else:
        cursor.execute(
            "INSERT INTO favorites (user_id, anime_id) VALUES (?, ?)",
            (user_id, anime["id"]),
        )
        action = "added"
        log_activity(
            user_id,
            "favorite",
            anime_id=anime["id"],
            message=f"Added {anime['title']} to favorites",
            cursor=cursor,
        )

    conn.commit()
    cursor.close()
    conn.close()
    return action


def is_favorite(user_id, mal_id):
    anime = get_anime_by_mal_id(mal_id)
    if not anime:
        return False
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM favorites WHERE user_id = ? AND anime_id = ?",
        (user_id, anime["id"]),
    )
    res = cursor.fetchone()
    conn.close()
    return res is not None


def get_user_favorites(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT a.* FROM animes a
        JOIN favorites f ON a.id = f.anime_id
        WHERE f.user_id = ?
        ORDER BY f.created_at DESC
    """,
        (user_id,),
    )
    res = cursor.fetchall()
    conn.close()
    return res


def get_user_activity(user_id, limit=20):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT ua.*, a.title as anime_title, a.mal_id, u.username as target_username
        FROM user_activity ua
        LEFT JOIN animes a ON ua.anime_id = a.id
        LEFT JOIN users u ON ua.target_user_id = u.id
        WHERE ua.user_id = ?
        ORDER BY ua.created_at DESC
        LIMIT ?
    """,
        (user_id, limit),
    )
    res = cursor.fetchall()
    conn.close()
    return res


def toggle_follow(follower_id, followed_id):
    if follower_id == followed_id:
        return None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM follows WHERE follower_id = ? AND followed_id = ?",
        (follower_id, followed_id),
    )
    exists = cursor.fetchone()

    if exists:
        cursor.execute(
            "DELETE FROM follows WHERE follower_id = ? AND followed_id = ?",
            (follower_id, followed_id),
        )
        action = "unfollowed"
    else:
        cursor.execute(
            "INSERT INTO follows (follower_id, followed_id) VALUES (?, ?)",
            (follower_id, followed_id),
        )
        action = "followed"
        target_user = get_user_by_id(followed_id)
        log_activity(
            follower_id,
            "follow",
            target_user_id=followed_id,
            message=f"Started following {target_user['username']}",
            cursor=cursor,
        )
        add_notification(
            followed_id,
            "social",
            f"Someone started following you!",
            f"/user/{get_user_by_id(follower_id)['username']}",
        )

        # Award XP for following
        add_xp(follower_id, 10, "Followed a user")

    conn.commit()
    conn.close()
    return action


def add_xp(user_id, amount, reason="Activity"):
    """Add XP to a user and handle leveling up."""
    conn = get_connection()
    if not conn:
        return None
    cursor = conn.cursor()

    # Get current XP and level
    cursor.execute("SELECT xp, level FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.close()
        conn.close()
        return None

    old_xp = user["xp"] or 0
    old_level = user["level"] or 1
    new_xp = old_xp + amount

    # Calculate new level: level = sqrt(xp/100) + 1
    new_level = int((new_xp / 100) ** 0.5) + 1

    cursor.execute(
        "UPDATE users SET xp = ?, level = ? WHERE id = ?", (new_xp, new_level, user_id)
    )

    # Check for level up notification
    if new_level > old_level:
        add_notification(
            user_id,
            "system",
            f"🎉 Congratulations! You reached Level {new_level}!",
            "/profile",
        )

        # Check for Level-based Badges
        if new_level == 5:
            award_badge(user_id, "Rising Star", cursor)
        elif new_level == 10:
            award_badge(user_id, "Anime Sensei", cursor)

    # Check for other badges
    check_milestone_badges(user_id, cursor)

    conn.commit()
    cursor.close()
    conn.close()
    return {
        "new_xp": new_xp,
        "new_level": new_level,
        "leveled_up": new_level > old_level,
    }


def award_badge(user_id, badge_name, cursor):
    """Award a badge to a user if they don't have it yet."""
    cursor.execute("SELECT id, icon FROM badges WHERE name = ?", (badge_name,))
    badge = cursor.fetchone()
    if not badge:
        return False

    try:
        cursor.execute(
            "INSERT INTO user_badges (user_id, badge_id) VALUES (?, ?)",
            (user_id, badge["id"]),
        )
        add_notification(
            user_id,
            "system",
            f"🏅 New Badge Unlocked: {badge_name} {badge['icon']}!",
            "/profile",
        )
        return True
    except sqlite3.IntegrityError:
        return False


def check_milestone_badges(user_id, cursor):
    """Check and award milestone badges."""
    # 1. First Episode
    cursor.execute(
        "SELECT COUNT(*) as count FROM watch_history WHERE user_id = ?", (user_id,)
    )
    if cursor.fetchone()["count"] >= 1:
        award_badge(user_id, "Otaku Beginner", cursor)

    # 2. First Review
    cursor.execute(
        "SELECT COUNT(*) as count FROM reviews WHERE user_id = ?", (user_id,)
    )
    if cursor.fetchone()["count"] >= 1:
        award_badge(user_id, "Anime Critic", cursor)

    # 3. Follow 5 users
    cursor.execute(
        "SELECT COUNT(*) as count FROM follows WHERE follower_id = ?", (user_id,)
    )
    if cursor.fetchone()["count"] >= 5:
        award_badge(user_id, "Social Butterfly", cursor)

    # 4. Create 3 collections
    cursor.execute(
        "SELECT COUNT(*) as count FROM collections WHERE user_id = ?", (user_id,)
    )
    if cursor.fetchone()["count"] >= 3:
        award_badge(user_id, "Collector", cursor)


def get_user_badges(user_id):
    """Get all badges for a user."""
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT b.*, ub.awarded_at
        FROM badges b
        JOIN user_badges ub ON b.id = ub.badge_id
        WHERE ub.user_id = ?
        ORDER BY ub.awarded_at DESC
    """,
        (user_id,),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(row) for row in rows]


def get_users_watching_anime(anime_id):
    """Get IDs of users who have this anime in their 'watching' list."""
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id FROM watchlists WHERE anime_id = ? AND status = 'watching'",
        (anime_id,),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [row["user_id"] for row in rows]


def get_anime_title_by_id(anime_id):
    """Get anime title by internal ID."""
    conn = get_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    cursor.execute("SELECT title FROM animes WHERE id = ?", (anime_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row["title"] if row else None


def is_following(follower_id, followed_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM follows WHERE follower_id = ? AND followed_id = ?",
        (follower_id, followed_id),
    )
    res = cursor.fetchone()
    conn.close()
    return res is not None


def get_social_feed(user_id, limit=50):
    """Get activities of followed users."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT ua.*, u.username, a.title as anime_title, a.mal_id, tu.username as target_username
        FROM user_activity ua
        JOIN users u ON ua.user_id = u.id
        JOIN follows f ON f.followed_id = ua.user_id
        LEFT JOIN animes a ON ua.anime_id = a.id
        LEFT JOIN users tu ON ua.target_user_id = tu.id
        WHERE f.follower_id = ?
        ORDER BY ua.created_at DESC
        LIMIT ?
    """,
        (user_id, limit),
    )
    res = cursor.fetchall()
    conn.close()
    return res


def get_global_activity(limit=50):
    """Get latest activities of all users."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT ua.*, u.username, a.title as anime_title, a.mal_id, tu.username as target_username
        FROM user_activity ua
        JOIN users u ON ua.user_id = u.id
        LEFT JOIN animes a ON ua.anime_id = a.id
        LEFT JOIN users tu ON ua.target_user_id = tu.id
        ORDER BY ua.created_at DESC
        LIMIT ?
    """,
        (limit,),
    )
    res = cursor.fetchall()
    conn.close()
    return res


def get_top_watchers(limit=10):
    """Get top watchers."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT u.id, u.username, u.level, u.xp,
               COUNT(wh.id) as anime_count,
               IFNULL(SUM(wh.episode_number), 0) as total_episodes
        FROM users u
        LEFT JOIN watch_history wh ON u.id = wh.user_id
        GROUP BY u.id
        ORDER BY total_episodes DESC, u.xp DESC
        LIMIT ?
    """,
        (limit,),
    )
    res = cursor.fetchall()
    conn.close()
    return [dict(row) for row in res]


def update_watch_history(user_id, anime_id, episode_number, progress=0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO watch_history (user_id, anime_id, episode_number, progress)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, anime_id) DO UPDATE SET
            episode_number = MAX(episode_number, excluded.episode_number),
            progress = CASE WHEN excluded.episode_number >= episode_number THEN excluded.progress ELSE progress END,
            updated_at = CURRENT_TIMESTAMP
    """,
        (user_id, anime_id, episode_number, progress),
    )

    anime_row = cursor.execute(
        "SELECT title FROM animes WHERE id = ?", (anime_id,)
    ).fetchone()
    if anime_row:
        log_activity(
            user_id,
            "watch",
            anime_id=anime_id,
            message=f"Watched Episode {episode_number} of {anime_row['title']}",
            cursor=cursor,
        )

    conn.commit()
    conn.close()

    # Award XP for watching
    add_xp(user_id, 10, "Watched an episode")


def update_watchlist(user_id, anime_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO watchlists (user_id, anime_id, status)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, anime_id) DO UPDATE SET
            status = excluded.status
    """,
        (user_id, anime_id, status),
    )

    anime = cursor.execute(
        "SELECT title FROM animes WHERE id = ?", (anime_id,)
    ).fetchone()
    log_activity(
        user_id,
        "watchlist",
        anime_id=anime_id,
        message=f"Moved {anime['title']} to {status}",
        cursor=cursor,
    )

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
    cursor.execute(
        """
        SELECT wh.*, a.title, a.mal_id, a.cover_local, a.cover_url
        FROM watch_history wh
        JOIN animes a ON wh.anime_id = a.id
        WHERE wh.user_id = ?
        ORDER BY wh.updated_at DESC
        LIMIT ?
    """,
        (user_id, limit),
    )
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(row) for row in results]


def get_anime_full_details(mal_id: int):
    """Get full details of an anime (including episodes and genres)."""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()

    # Get main anime info
    cursor.execute("SELECT * FROM animes WHERE mal_id = ?", (mal_id,))
    anime_row = cursor.fetchone()

    if not anime_row:
        cursor.close()
        conn.close()
        return None

    # Convert sqlite3.Row to dict
    anime = dict(anime_row)

    # Get episodes
    cursor.execute(
        """
        SELECT e.*, COUNT(vl.id) as video_count
        FROM episodes e
        LEFT JOIN video_links vl ON e.id = vl.episode_id
        WHERE e.anime_id = ?
        GROUP BY e.id
        ORDER BY e.episode_number
    """,
        (anime["id"],),
    )
    anime["episodes_list"] = [dict(row) for row in cursor.fetchall()]

    # Get genres
    cursor.execute(
        """
        SELECT g.name
        FROM genres g
        JOIN anime_genres ag ON g.id = ag.genre_id
        WHERE ag.anime_id = ?
        ORDER BY g.name
    """,
        (anime["id"],),
    )
    anime["genres"] = [row["name"] for row in cursor.fetchall()]

    # Get characters
    anime["characters"] = get_anime_characters(anime["id"])

    # Get staff
    anime["staff"] = get_anime_staff(anime["id"])

    cursor.close()
    conn.close()
    return anime


def insert_or_update_anime(anime_data):
    """Insert or update anime."""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()

    # Check for existing anime first
    cursor.execute("SELECT id FROM animes WHERE mal_id = ?", (anime_data["mal_id"],))
    existing = cursor.fetchone()

    if existing:
        # Update
        cursor.execute(
            """
            UPDATE animes SET
                title = ?, title_english = ?, title_japanese = ?,
                type = ?, episodes = ?, status = ?, score = ?,
                rating = ?, popularity = ?, members = ?, favorites = ?,
                synopsis = ?, background = ?,
                year = ?, season = ?, aired_from = ?, aired_to = ?,
                duration = ?, broadcast = ?,
                cover_url = ?, cover_local = ?, updated_at = CURRENT_TIMESTAMP
            WHERE mal_id = ?
        """,
            (
                anime_data.get("title"),
                anime_data.get("title_english"),
                anime_data.get("title_japanese"),
                anime_data.get("type"),
                anime_data.get("episodes", 0),
                anime_data.get("status"),
                anime_data.get("score"),
                anime_data.get("rating"),
                anime_data.get("popularity"),
                anime_data.get("members"),
                anime_data.get("favorites"),
                anime_data.get("synopsis"),
                anime_data.get("background"),
                anime_data.get("year"),
                anime_data.get("season"),
                anime_data.get("aired_from"),
                anime_data.get("aired_to"),
                anime_data.get("duration"),
                anime_data.get("broadcast"),
                anime_data.get("cover_url"),
                anime_data.get("cover_local"),
                anime_data["mal_id"],
            ),
        )
        anime_id = existing["id"]
    else:
        # Insert new
        cursor.execute(
            """
            INSERT INTO animes (
                mal_id, title, title_english, title_japanese,
                type, episodes, status, score,
                rating, popularity, members, favorites,
                synopsis, background,
                year, season, aired_from, aired_to,
                duration, broadcast,
                cover_url, cover_local
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                anime_data["mal_id"],
                anime_data.get("title"),
                anime_data.get("title_english"),
                anime_data.get("title_japanese"),
                anime_data.get("type"),
                anime_data.get("episodes", 0),
                anime_data.get("status"),
                anime_data.get("score"),
                anime_data.get("rating"),
                anime_data.get("popularity"),
                anime_data.get("members"),
                anime_data.get("favorites"),
                anime_data.get("synopsis"),
                anime_data.get("background"),
                anime_data.get("year"),
                anime_data.get("season"),
                anime_data.get("aired_from"),
                anime_data.get("aired_to"),
                anime_data.get("duration"),
                anime_data.get("broadcast"),
                anime_data.get("cover_url"),
                anime_data.get("cover_local"),
            ),
        )
        anime_id = cursor.lastrowid

    conn.commit()
    cursor.close()
    conn.close()
    return anime_id


def insert_anime_titles(anime_id, titles):
    """Insert anime titles."""
    # Simple version - just use main title for now
    pass


def insert_or_get_genre(name):
    """Insert or get genre."""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()

    # Check existing genre first
    cursor.execute("SELECT id FROM genres WHERE name = ?", (name,))
    existing = cursor.fetchone()

    if existing:
        genre_id = existing["id"]
    else:
        # Insert new genre
        cursor.execute("INSERT INTO genres (name) VALUES (?)", (name,))
        genre_id = cursor.lastrowid
        conn.commit()

    cursor.close()
    conn.close()
    return genre_id


def link_anime_genre(anime_id, genre_id):
    """Create relationship between anime and genre."""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    # Check existing relation first
    cursor.execute(
        "SELECT 1 FROM anime_genres WHERE anime_id = ? AND genre_id = ?",
        (anime_id, genre_id),
    )
    existing = cursor.fetchone()

    if not existing:
        cursor.execute(
            "INSERT INTO anime_genres (anime_id, genre_id) VALUES (?, ?)",
            (anime_id, genre_id),
        )
        conn.commit()

    cursor.close()
    conn.close()
    return True


def sync_anime_genres(anime_id, genres_list):
    """
    Sync anime genres in bulk.
    genres_list: [{"name": "Action", ...}, ...]
    """
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    try:
        # 1. Cache existing genres
        cursor.execute("SELECT id, name FROM genres")
        genre_map = {row["name"]: row["id"] for row in cursor.fetchall()}

        anime_genre_links = []

        for g in genres_list:
            name = g.get("name")
            if not name:
                continue

            if name in genre_map:
                genre_id = genre_map[name]
            else:
                try:
                    cursor.execute("INSERT INTO genres (name) VALUES (?)", (name,))
                    genre_id = cursor.lastrowid
                    genre_map[name] = genre_id
                except sqlite3.IntegrityError:
                    # Another process might have added it
                    cursor.execute("SELECT id FROM genres WHERE name = ?", (name,))
                    res = cursor.fetchone()
                    if res:
                        genre_id = res["id"]
                        genre_map[name] = genre_id
                    else:
                        continue

            anime_genre_links.append((anime_id, genre_id))

        # 2. Add links in bulk
        if anime_genre_links:
            cursor.executemany(
                """
                INSERT OR IGNORE INTO anime_genres (anime_id, genre_id)
                VALUES (?, ?)
            """,
                anime_genre_links,
            )
            conn.commit()

        return True
    except Error as e:
        print(f"[DB] sync_anime_genres error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def insert_or_get_theme(name):
    """Insert or get theme."""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()

    # Check existing theme first
    cursor.execute("SELECT id FROM themes WHERE name = ?", (name,))
    existing = cursor.fetchone()

    if existing:
        theme_id = existing["id"]
    else:
        # Insert new theme
        cursor.execute("INSERT INTO themes (name) VALUES (?)", (name,))
        theme_id = cursor.lastrowid
        conn.commit()

    cursor.close()
    conn.close()
    return theme_id


def link_anime_theme(anime_id, theme_id):
    """Create relationship between anime and theme."""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    # Check existing relation first
    cursor.execute(
        "SELECT 1 FROM anime_themes WHERE anime_id = ? AND theme_id = ?",
        (anime_id, theme_id),
    )
    existing = cursor.fetchone()

    if not existing:
        cursor.execute(
            "INSERT INTO anime_themes (anime_id, theme_id) VALUES (?, ?)",
            (anime_id, theme_id),
        )
        conn.commit()

    cursor.close()
    conn.close()
    return True


def insert_or_get_studio(name):
    """Insert or get studio."""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()

    # Check existing studio first
    cursor.execute("SELECT id FROM studios WHERE name = ?", (name,))
    existing = cursor.fetchone()

    if existing:
        studio_id = existing["id"]
    else:
        # Insert new studio
        cursor.execute("INSERT INTO studios (name) VALUES (?)", (name,))
        studio_id = cursor.lastrowid
        conn.commit()

    cursor.close()
    conn.close()
    return studio_id


def link_anime_studio(anime_id, studio_id):
    """Create relationship between anime and studio."""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    # Check existing relation first
    cursor.execute(
        "SELECT 1 FROM anime_studios WHERE anime_id = ? AND studio_id = ?",
        (anime_id, studio_id),
    )
    existing = cursor.fetchone()

    if not existing:
        cursor.execute(
            "INSERT INTO anime_studios (anime_id, studio_id) VALUES (?, ?)",
            (anime_id, studio_id),
        )
        conn.commit()

    cursor.close()
    conn.close()
    return True


def insert_or_get_producer(name):
    """Insert or get producer."""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()

    # Check existing producer first
    cursor.execute("SELECT id FROM producers WHERE name = ?", (name,))
    existing = cursor.fetchone()

    if existing:
        producer_id = existing["id"]
    else:
        # Insert new producer
        cursor.execute("INSERT INTO producers (name) VALUES (?)", (name,))
        producer_id = cursor.lastrowid
        conn.commit()

    cursor.close()
    conn.close()
    return producer_id


def link_anime_producer(anime_id, producer_id, role):
    """Create relationship between anime and producer."""
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    # Check existing relation first
    cursor.execute(
        "SELECT 1 FROM anime_producers WHERE anime_id = ? AND producer_id = ? AND role = ?",
        (anime_id, producer_id, role),
    )
    existing = cursor.fetchone()

    if not existing:
        cursor.execute(
            "INSERT INTO anime_producers (anime_id, producer_id, role) VALUES (?, ?, ?)",
            (anime_id, producer_id, role),
        )
        conn.commit()

    cursor.close()
    conn.close()
    return True


def get_source_id(source_name):
    """Get source ID from source name, create if not exists."""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()

    # Check existing source first
    cursor.execute("SELECT id FROM sources WHERE name = ?", (source_name,))
    existing = cursor.fetchone()

    if existing:
        source_id = existing["id"]
    else:
        # Insert new source
        cursor.execute("INSERT INTO sources (name) VALUES (?)", (source_name,))
        source_id = cursor.lastrowid
        conn.commit()

    cursor.close()
    conn.close()
    return source_id


def insert_or_update_anime_source(
    anime_id, source_id, source_anime_id, source_slug, source_title
):
    """Insert or update anime-source mapping."""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()

    # Check existing mapping first
    cursor.execute(
        "SELECT id FROM anime_sources WHERE anime_id = ? AND source_id = ?",
        (anime_id, source_id),
    )
    existing = cursor.fetchone()

    if existing:
        # Update
        cursor.execute(
            """
            UPDATE anime_sources SET
                source_anime_id = ?, source_slug = ?, source_title = ?
            WHERE anime_id = ? AND source_id = ?
        """,
            (source_anime_id, source_slug, source_title, anime_id, source_id),
        )
        anime_source_id = existing["id"]
    else:
        # Insert new
        cursor.execute(
            """
            INSERT INTO anime_sources (anime_id, source_id, source_anime_id, source_slug, source_title)
            VALUES (?, ?, ?, ?, ?)
        """,
            (anime_id, source_id, source_anime_id, source_slug, source_title),
        )
        anime_source_id = cursor.lastrowid

    conn.commit()
    cursor.close()
    conn.close()
    return anime_source_id


def insert_or_update_episode(anime_id, episode_number, title):
    """Insert or update episode."""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()

    # Check existing episode first
    cursor.execute(
        "SELECT id FROM episodes WHERE anime_id = ? AND episode_number = ?",
        (anime_id, episode_number),
    )
    existing = cursor.fetchone()

    if existing:
        # Update
        cursor.execute(
            """
            UPDATE episodes SET
                title = ?, aired = CURRENT_DATE
            WHERE anime_id = ? AND episode_number = ?
        """,
            (title, anime_id, episode_number),
        )
        episode_id = existing["id"]
    else:
        # Insert new
        cursor.execute(
            """
            INSERT INTO episodes (anime_id, episode_number, title, aired)
            VALUES (?, ?, ?, CURRENT_DATE)
        """,
            (anime_id, episode_number, title),
        )
        episode_id = cursor.lastrowid

    conn.commit()
    cursor.close()
    conn.close()
    return episode_id


def get_anime_sources(mal_id: int):
    """Get current sources for an anime."""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT s.name as source_name, s.id as source_id, asrc.source_slug, asrc.source_anime_id
        FROM anime_sources asrc
        JOIN sources s ON asrc.source_id = s.id
        JOIN animes a ON asrc.anime_id = a.id
        WHERE a.mal_id = ? AND s.is_active = 1
    """,
        (mal_id,),
    )

    results = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return results


def get_all_mal_ids():
    """Get MAL IDs of all anime."""
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
    """Get all genres."""
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
    """Search anime by title."""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    # Search in titles and title_english
    cursor.execute(
        """
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
    """,
        (
            f"%{title_query}%",
            f"%{title_query}%",
            f"{title_query}%",
            f"{title_query}%",
            limit,
        ),
    )
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results


def get_live_search_results(query, limit=5):
    """Fast results for live search."""
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    cursor.execute(
        """
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
    """,
        (f"%{query}%", f"%{query}%", f"{query}%", f"{query}%", limit),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(row) for row in rows]


def insert_video_link(episode_id, source_id, video_url, quality, fansub):
    """Add video link."""
    conn = get_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO video_links (episode_id, source_id, video_url, quality, fansub)
            VALUES (?, ?, ?, ?, ?)
        """,
            (episode_id, source_id, video_url, quality, fansub),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"[DB] insert_video_link error: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def delete_video_links_for_episode(anime_id, episode_number):
    """Delete video links for an episode."""
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            DELETE FROM video_links
            WHERE episode_id IN (SELECT id FROM episodes WHERE anime_id = ? AND episode_number = ?)
        """,
            (anime_id, episode_number),
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def remove_dead_video_link(video_id):
    """Make video link inactive."""
    conn = get_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE video_links SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (video_id,),
        )
        conn.commit()
        return True
    finally:
        cursor.close()
        conn.close()


def get_video_links(anime_id: int, episode_number: int = None):
    """Get video links for an anime. If episode number is provided, return only for that episode."""
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()

    if episode_number:
        # Video links for specific episode
        cursor.execute(
            """
            SELECT vl.*, e.episode_number, e.title as episode_title, s.name as source_name
            FROM video_links vl
            JOIN episodes e ON vl.episode_id = e.id
            LEFT JOIN sources s ON vl.source_id = s.id
            WHERE e.anime_id = ? AND e.episode_number = ? AND vl.is_active = 1
            ORDER BY vl.quality DESC, vl.fansub
        """,
            (anime_id, episode_number),
        )
    else:
        # All video links
        cursor.execute(
            """
            SELECT vl.*, e.episode_number, e.title as episode_title, s.name as source_name
            FROM video_links vl
            JOIN episodes e ON vl.episode_id = e.id
            LEFT JOIN sources s ON vl.source_id = s.id
            WHERE e.anime_id = ? AND vl.is_active = 1
            ORDER BY e.episode_number, vl.quality DESC, vl.fansub
        """,
            (anime_id,),
        )

    results = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return results


def get_episode_by_number(anime_id: int, episode_number: int):
    """Get episode by anime ID and episode number."""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM episodes
        WHERE anime_id = ? AND episode_number = ?
    """,
        (anime_id, episode_number),
    )

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
        cursor.execute(
            """
            INSERT INTO reviews (user_id, anime_id, score, title, content, is_spoiler)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, anime_id) DO UPDATE SET
                score = excluded.score,
                title = excluded.title,
                content = excluded.content,
                is_spoiler = excluded.is_spoiler,
                updated_at = CURRENT_TIMESTAMP
        """,
            (user_id, anime_id, score, title, content, int(is_spoiler)),
        )
        conn.commit()

        # Award XP for reviewing
        add_xp(user_id, 50, "Wrote a review")

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
        cursor.execute(
            """
            INSERT INTO review_votes (review_id, user_id, vote)
            VALUES (?, ?, ?)
            ON CONFLICT(review_id, user_id) DO UPDATE SET
                vote = excluded.vote
        """,
            (review_id, user_id, vote),
        )
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
        cursor.execute(
            "DELETE FROM reviews WHERE id = ? AND user_id = ?", (review_id, user_id)
        )
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


# ─────────────────────────────────────────────────────────────────────────────
# COLLECTION OPERATIONS
# ─────────────────────────────────────────────────────────────────────────────


def create_collection(user_id, name, description=None, is_public=True):
    """Create a new collection."""
    conn = get_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO collections (user_id, name, description, is_public)
            VALUES (?, ?, ?, ?)
        """,
            (user_id, name, description, int(is_public)),
        )
        conn.commit()
        col_id = cursor.lastrowid

        # Award XP for creating a collection
        add_xp(user_id, 20, "Created a collection")

        return col_id
    except sqlite3.Error:
        return None
    finally:
        cursor.close()
        conn.close()


def get_user_collections(user_id, only_public=False):
    """Get user collections."""
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    query = "SELECT c.*, (SELECT COUNT(*) FROM collection_items WHERE collection_id = c.id) as item_count FROM collections c WHERE user_id = ?"
    if only_public:
        query += " AND is_public = 1"
    query += " ORDER BY created_at DESC"

    cursor.execute(query, (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def get_collection_details(collection_id):
    """Get collection details and items."""
    conn = get_connection()
    if not conn:
        return None
    cursor = conn.cursor()

    # Collection info
    cursor.execute(
        """
        SELECT c.*, u.username
        FROM collections c
        JOIN users u ON c.user_id = u.id
        WHERE c.id = ?
    """,
        (collection_id,),
    )
    collection = cursor.fetchone()
    if not collection:
        cursor.close()
        conn.close()
        return None

    col_dict = dict(collection)

    # Anime list
    cursor.execute(
        """
        SELECT a.* FROM animes a
        JOIN collection_items ci ON a.id = ci.anime_id
        WHERE ci.collection_id = ?
        ORDER BY ci.created_at DESC
    """,
        (collection_id,),
    )
    col_dict["animes"] = [dict(row) for row in cursor.fetchall()]

    cursor.close()
    conn.close()
    return col_dict


def add_to_collection(collection_id, anime_id):
    """Add anime to collection."""
    conn = get_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT OR IGNORE INTO collection_items (collection_id, anime_id)
            VALUES (?, ?)
        """,
            (collection_id, anime_id),
        )
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        cursor.close()
        conn.close()


def remove_from_collection(collection_id, anime_id):
    """Remove anime from collection."""
    conn = get_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM collection_items WHERE collection_id = ? AND anime_id = ?",
        (collection_id, anime_id),
    )
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    conn.close()
    return affected > 0


def delete_collection(collection_id, user_id):
    """Delete collection."""
    conn = get_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM collections WHERE id = ? AND user_id = ?", (collection_id, user_id)
    )
    affected = cursor.rowcount
    if affected > 0:
        cursor.execute(
            "DELETE FROM collection_items WHERE collection_id = ?", (collection_id,)
        )
        conn.commit()
    cursor.close()
    conn.close()
    return affected > 0


def update_collection(collection_id, user_id, name, description, is_public):
    """Update collection."""
    conn = get_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE collections SET name = ?, description = ?, is_public = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ?
    """,
        (name, description, int(is_public), collection_id, user_id),
    )
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    conn.close()
    return affected > 0


# ─────────────────────────────────────────────────────────────────────────────
# CHARACTER & STAFF OPERATIONS
# ─────────────────────────────────────────────────────────────────────────────


def insert_or_update_character(char_data):
    """Insert or update character."""
    conn = get_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO characters (mal_id, name, image_url, about)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(mal_id) DO UPDATE SET
                name = excluded.name,
                image_url = excluded.image_url,
                about = excluded.about
        """,
            (
                char_data["mal_id"],
                char_data["name"],
                char_data.get("image_url"),
                char_data.get("about"),
            ),
        )
        conn.commit()
        # Get internal ID
        cursor.execute(
            "SELECT id FROM characters WHERE mal_id = ?", (char_data["mal_id"],)
        )
        return cursor.fetchone()["id"]
    except sqlite3.Error:
        return None
    finally:
        cursor.close()
        conn.close()


def insert_or_update_person(person_data):
    """Insert or update person (voice actor or staff)."""
    conn = get_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO people (mal_id, name, image_url)
            VALUES (?, ?, ?)
            ON CONFLICT(mal_id) DO UPDATE SET
                name = excluded.name,
                image_url = excluded.image_url
        """,
            (person_data["mal_id"], person_data["name"], person_data.get("image_url")),
        )
        conn.commit()
        cursor.execute(
            "SELECT id FROM people WHERE mal_id = ?", (person_data["mal_id"],)
        )
        return cursor.fetchone()["id"]
    except sqlite3.Error:
        return None
    finally:
        cursor.close()
        conn.close()


def link_anime_character(anime_id, character_id, role):
    """Link anime and character."""
    conn = get_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT OR REPLACE INTO anime_characters (anime_id, character_id, role)
            VALUES (?, ?, ?)
        """,
            (anime_id, character_id, role),
        )
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        cursor.close()
        conn.close()


def link_character_voice_actor(anime_id, character_id, person_id, language):
    """Link character with voice actor for a specific anime."""
    conn = get_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT OR REPLACE INTO character_voice_actors (anime_id, character_id, person_id, language)
            VALUES (?, ?, ?, ?)
        """,
            (anime_id, character_id, person_id, language),
        )
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        cursor.close()
        conn.close()


def link_anime_staff(anime_id, person_id, position):
    """Link anime and staff."""
    conn = get_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT OR REPLACE INTO anime_staff (anime_id, person_id, position)
            VALUES (?, ?, ?)
        """,
            (anime_id, person_id, position),
        )
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        cursor.close()
        conn.close()


def get_anime_characters(anime_id, limit=20):
    """Get characters and their voice actors for an anime."""
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT c.*, ac.role, p.name as va_name, p.image_url as va_image, p.mal_id as va_mal_id, cva.language
            FROM anime_characters ac
            JOIN characters c ON ac.character_id = c.id
            LEFT JOIN character_voice_actors cva ON (
                ac.anime_id = cva.anime_id AND
                ac.character_id = cva.character_id AND
                cva.language = 'Japanese'
            )
            LEFT JOIN people p ON cva.person_id = p.id
            WHERE ac.anime_id = ?
            ORDER BY CASE WHEN ac.role = 'Main' THEN 1 ELSE 2 END, c.name
            LIMIT ?
        """,
            (anime_id, limit),
        )
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error:
        return []
    finally:
        cursor.close()
        conn.close()


def get_anime_staff(anime_id, limit=20):
    """Get staff for an anime."""
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT p.*, ast.position
            FROM anime_staff ast
            JOIN people p ON ast.person_id = p.id
            WHERE ast.anime_id = ?
            ORDER BY ast.position
            LIMIT ?
        """,
            (anime_id, limit),
        )
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error:
        return []
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    print("Initializing database...")
    init_database()
