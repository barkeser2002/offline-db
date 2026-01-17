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
        url TEXT NOT NULL,
        quality TEXT,
        is_active BOOLEAN DEFAULT 1,
        FOREIGN KEY (episode_id) REFERENCES episodes(id)
    )
    """)

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

    # Yorumlar tablosu
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
    )
    """)

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
    return result

# Basit placeholder fonksiyonları
def serialize_for_json(data):
    """JSON serileştirme için basit versiyon."""
    return data

def add_comment(user_id, anime_id, episode_number, content, is_spoiler=False):
    """Yorum ekle."""
    conn = get_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO comments (user_id, anime_id, episode_number, content, is_spoiler)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, anime_id, episode_number, content, is_spoiler))
    conn.commit()
    comment_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return comment_id

def get_episode_comments(anime_id, episode_number):
    """Bölüm yorumlarını getir."""
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, u.username
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.anime_id = ? AND c.episode_number = ?
        ORDER BY c.created_at DESC
    """, (anime_id, episode_number))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

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
    """Anime keşfet."""
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    query = "SELECT * FROM animes"
    params = []

    if filters.get("genres"):
        # Basitleştirilmiş - genre filtresi yok
        pass

    query += " ORDER BY score DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor.execute(query, params)
    results = cursor.fetchall()
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

def get_user_stats(user_id):
    return {
        "total_watched": 0,
        "total_episodes": 0,
        "watchlist_counts": {},
        "favorite_genres": []
    }

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
    cursor.execute("SELECT * FROM watch_history WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?", (user_id, limit))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

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
                title = ?, title_english = ?, type = ?, episodes = ?,
                status = ?, score = ?, synopsis = ?, year = ?, season = ?,
                cover_url = ?, cover_local = ?, updated_at = CURRENT_TIMESTAMP
            WHERE mal_id = ?
        """, (
            anime_data.get("title"), anime_data.get("title_english"),
            anime_data.get("type"), anime_data.get("episodes", 0),
            anime_data.get("status"), anime_data.get("score"),
            anime_data.get("synopsis"), anime_data.get("year"),
            anime_data.get("season"), anime_data.get("cover_url"),
            anime_data.get("cover_local"), anime_data["mal_id"]
        ))
        anime_id = existing["id"]
    else:
        # Yeni ekle
        cursor.execute("""
            INSERT INTO animes (
                mal_id, title, title_english, type, episodes, status,
                score, synopsis, year, season, cover_url, cover_local
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            anime_data["mal_id"], anime_data.get("title"),
            anime_data.get("title_english"), anime_data.get("type"),
            anime_data.get("episodes", 0), anime_data.get("status"),
            anime_data.get("score"), anime_data.get("synopsis"),
            anime_data.get("year"), anime_data.get("season"),
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

def insert_or_get_genre(mal_id, name):
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

def insert_or_get_theme(mal_id, name):
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

def insert_or_get_studio(mal_id, name):
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

def insert_or_get_producer(mal_id, name):
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
    cursor.execute("""
        SELECT * FROM animes
        WHERE title LIKE ? OR title_english LIKE ?
        ORDER BY score DESC
        LIMIT ?
    """, (f"%{title_query}%", f"%{title_query}%", limit))
    results = cursor.fetchall()
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

if __name__ == "__main__":
    print("Initializing database...")
    init_database()
