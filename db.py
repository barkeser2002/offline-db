"""
MySQL Veritabanı İşlemleri
"""

import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG

def get_connection():
    """Veritabanı bağlantısı oluştur."""
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"],
            charset=DB_CONFIG["charset"],
            collation=DB_CONFIG["collation"]
        )
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
        id INT AUTO_INCREMENT PRIMARY KEY,
        mal_id INT UNIQUE NOT NULL,
        anidb_id INT,
        anilist_id INT,
        tvdb_id INT,
        imdb_id VARCHAR(20),
        
        title VARCHAR(500) NOT NULL,
        title_english VARCHAR(500),
        title_japanese VARCHAR(500),
        
        type VARCHAR(50),
        source VARCHAR(100),
        episodes INT DEFAULT 0,
        status VARCHAR(100),
        airing BOOLEAN DEFAULT FALSE,
        
        aired_from DATE,
        aired_to DATE,
        duration VARCHAR(50),
        rating VARCHAR(100),
        
        score DECIMAL(4,2),
        scored_by INT,
        `rank` INT,
        popularity INT,
        members INT,
        favorites INT,
        
        synopsis TEXT,
        background TEXT,
        season VARCHAR(20),
        year INT,
        broadcast VARCHAR(100),
        
        cover_url VARCHAR(500),
        cover_local VARCHAR(255),
        trailer_url VARCHAR(500),
        
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        
        INDEX idx_mal_id (mal_id),
        INDEX idx_title (title(100)),
        INDEX idx_year (year),
        INDEX idx_score (score)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    
    # Alternatif isimler tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS anime_titles (
        id INT AUTO_INCREMENT PRIMARY KEY,
        anime_id INT NOT NULL,
        title VARCHAR(500) NOT NULL,
        title_type VARCHAR(50),
        
        INDEX idx_anime_id (anime_id),
        INDEX idx_title (title(100))
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    
    # Türler tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS genres (
        id INT AUTO_INCREMENT PRIMARY KEY,
        mal_id INT UNIQUE,
        name VARCHAR(100) NOT NULL UNIQUE,
        
        INDEX idx_name (name)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    
    # Anime-Tür ilişki tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS anime_genres (
        anime_id INT NOT NULL,
        genre_id INT NOT NULL,
        
        PRIMARY KEY (anime_id, genre_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    
    # Temalar tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS themes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        mal_id INT UNIQUE,
        name VARCHAR(100) NOT NULL UNIQUE,
        
        INDEX idx_name (name)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    
    # Anime-Tema ilişki tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS anime_themes (
        anime_id INT NOT NULL,
        theme_id INT NOT NULL,
        
        PRIMARY KEY (anime_id, theme_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    
    # Stüdyolar tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS studios (
        id INT AUTO_INCREMENT PRIMARY KEY,
        mal_id INT UNIQUE,
        name VARCHAR(200) NOT NULL,
        
        INDEX idx_name (name)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    
    # Anime-Stüdyo ilişki tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS anime_studios (
        anime_id INT NOT NULL,
        studio_id INT NOT NULL,
        
        PRIMARY KEY (anime_id, studio_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    
    # Yapımcılar tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS producers (
        id INT AUTO_INCREMENT PRIMARY KEY,
        mal_id INT UNIQUE,
        name VARCHAR(200) NOT NULL,
        
        INDEX idx_name (name)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    
    # Anime-Yapımcı ilişki tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS anime_producers (
        anime_id INT NOT NULL,
        producer_id INT NOT NULL,
        producer_type VARCHAR(50),  -- producer, licensor
        
        PRIMARY KEY (anime_id, producer_id, producer_type)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    
    # Bölümler tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS episodes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        anime_id INT NOT NULL,
        episode_number INT NOT NULL,
        title VARCHAR(500),
        
        UNIQUE KEY unique_anime_episode (anime_id, episode_number),
        INDEX idx_anime_id (anime_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    
    # Kaynaklar/Adaptörler tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sources (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL UNIQUE,  -- animecix, animely, anizle, tranime
        base_url VARCHAR(255),
        is_active BOOLEAN DEFAULT TRUE,
        
        INDEX idx_name (name)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    
    # Varsayılan kaynakları ekle
    cursor.execute("""
    INSERT IGNORE INTO sources (name, base_url, is_active) VALUES
        ('animecix', 'https://animecix.tv/', TRUE),
        ('animely', 'https://animely.net', FALSE),
        ('anizle', 'https://anizm.pro', TRUE),
        ('tranime', 'https://www.tranimeizle.io', TRUE),
        ('turkanime', 'https://www.turkanime.co', TRUE)
    """)
    
    # Anime-Kaynak eşleşme tablosu (anime'nin hangi kaynakta hangi slug ile bulunduğu)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS anime_sources (
        id INT AUTO_INCREMENT PRIMARY KEY,
        anime_id INT NOT NULL,
        source_id INT NOT NULL,
        source_anime_id VARCHAR(100),  -- kaynaktaki anime ID'si
        source_slug VARCHAR(255),       -- kaynaktaki slug
        source_title VARCHAR(500),      -- kaynaktaki başlık
        
        UNIQUE KEY unique_anime_source (anime_id, source_id),
        INDEX idx_anime_id (anime_id),
        INDEX idx_source_id (source_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    
    # Video linkleri tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS video_links (
        id INT AUTO_INCREMENT PRIMARY KEY,
        episode_id INT NOT NULL,
        source_id INT NOT NULL,
        
        fansub VARCHAR(100),
        quality VARCHAR(50),
        video_url TEXT NOT NULL,
        iframe_url TEXT,
        
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        
        INDEX idx_episode_id (episode_id),
        INDEX idx_source_id (source_id),
        INDEX idx_fansub (fansub)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # Kullanıcılar tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) NOT NULL UNIQUE,
        email VARCHAR(100) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_username (username)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # İzleme Geçmişi tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS watch_history (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        anime_id INT NOT NULL,
        episode_number INT NOT NULL,
        progress_percent FLOAT DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

        UNIQUE KEY unique_user_anime (user_id, anime_id),
        INDEX idx_user_history (user_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (anime_id) REFERENCES animes(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # İzleme Listesi tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS watchlists (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        anime_id INT NOT NULL,
        status ENUM('watching', 'completed', 'on-hold', 'dropped', 'plan-to-watch') DEFAULT 'plan-to-watch',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        UNIQUE KEY unique_user_anime_watchlist (user_id, anime_id),
        INDEX idx_user_watchlist (user_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (anime_id) REFERENCES animes(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    
    # Yorumlar tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        anime_id INT NOT NULL,
        episode_number INT NOT NULL,
        content TEXT NOT NULL,
        is_spoiler BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        INDEX idx_anime_episode (anime_id, episode_number),
        INDEX idx_user_comments (user_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (anime_id) REFERENCES animes(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    conn.commit()
    cursor.close()
    conn.close()
    
    print("[DB] Database tables created successfully (InnoDB).")
    return True


def get_anime_by_mal_id(mal_id: int):
    """MAL ID ile anime'yi getir."""
    conn = get_connection()
    if not conn:
        return None
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM animes WHERE mal_id = %s", (mal_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result


def get_anime_by_title(title: str):
    """Başlık ile anime'yi ara (daha esnek)."""
    conn = get_connection()
    if not conn:
        return None
    
    cursor = conn.cursor(dictionary=True)
    
    # Boşlukları ve tireleri normalleştirerek ara
    search_term = f"%{title.replace('-', ' ')}%"

    # Hem ana başlıkta hem de alternatif başlıklarda ara (tek sorgu)
    query = """
        SELECT a.*
        FROM animes a
        LEFT JOIN anime_titles at ON a.id = at.anime_id
        WHERE
            REPLACE(a.title, '-', ' ') LIKE %s OR
            REPLACE(a.title_english, '-', ' ') LIKE %s OR
            REPLACE(a.title_japanese, '-', ' ') LIKE %s OR
            REPLACE(at.title, '-', ' ') LIKE %s
        GROUP BY a.id
        ORDER BY
            CASE
                WHEN REPLACE(a.title, '-', ' ') LIKE %s THEN 1
                WHEN REPLACE(a.title_english, '-', ' ') LIKE %s THEN 2
                ELSE 3
            END,
            a.popularity ASC
        LIMIT 10
    """
    
    params = (
        search_term,
        search_term,
        search_term,
        search_term,
        search_term,
        search_term,
    )
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return results


def insert_or_update_anime(anime_data: dict) -> int:
    """
    Anime'yi ekle veya güncelle.
    Returns: anime_id
    """
    conn = get_connection()
    if not conn:
        return 0
    
    cursor = conn.cursor()
    
    # Önce mevcut anime'yi kontrol et
    cursor.execute("SELECT id FROM animes WHERE mal_id = %s", (anime_data.get("mal_id"),))
    existing = cursor.fetchone()
    
    if existing:
        anime_id = existing[0]
        # Güncelle
        cursor.execute("""
            UPDATE animes SET
                anidb_id = %s, anilist_id = %s, tvdb_id = %s, imdb_id = %s,
                title = %s, title_english = %s, title_japanese = %s,
                type = %s, source = %s, episodes = %s, status = %s, airing = %s,
                aired_from = %s, aired_to = %s, duration = %s, rating = %s,
                score = %s, scored_by = %s, `rank` = %s, popularity = %s,
                members = %s, favorites = %s, synopsis = %s, background = %s,
                season = %s, year = %s, broadcast = %s,
                cover_url = %s, cover_local = %s, trailer_url = %s
            WHERE id = %s
        """, (
            anime_data.get("anidb_id"), anime_data.get("anilist_id"),
            anime_data.get("tvdb_id"), anime_data.get("imdb_id"),
            anime_data.get("title"), anime_data.get("title_english"),
            anime_data.get("title_japanese"), anime_data.get("type"),
            anime_data.get("source"), anime_data.get("episodes"),
            anime_data.get("status"), anime_data.get("airing"),
            anime_data.get("aired_from"), anime_data.get("aired_to"),
            anime_data.get("duration"), anime_data.get("rating"),
            anime_data.get("score"), anime_data.get("scored_by"),
            anime_data.get("rank"), anime_data.get("popularity"),
            anime_data.get("members"), anime_data.get("favorites"),
            anime_data.get("synopsis"), anime_data.get("background"),
            anime_data.get("season"), anime_data.get("year"),
            anime_data.get("broadcast"), anime_data.get("cover_url"),
            anime_data.get("cover_local"), anime_data.get("trailer_url"),
            anime_id
        ))
    else:
        # Ekle
        cursor.execute("""
            INSERT INTO animes (
                mal_id, anidb_id, anilist_id, tvdb_id, imdb_id,
                title, title_english, title_japanese,
                type, source, episodes, status, airing,
                aired_from, aired_to, duration, rating,
                score, scored_by, `rank`, popularity, members, favorites,
                synopsis, background, season, year, broadcast,
                cover_url, cover_local, trailer_url
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            anime_data.get("mal_id"), anime_data.get("anidb_id"),
            anime_data.get("anilist_id"), anime_data.get("tvdb_id"),
            anime_data.get("imdb_id"), anime_data.get("title"),
            anime_data.get("title_english"), anime_data.get("title_japanese"),
            anime_data.get("type"), anime_data.get("source"),
            anime_data.get("episodes"), anime_data.get("status"),
            anime_data.get("airing"), anime_data.get("aired_from"),
            anime_data.get("aired_to"), anime_data.get("duration"),
            anime_data.get("rating"), anime_data.get("score"),
            anime_data.get("scored_by"), anime_data.get("rank"),
            anime_data.get("popularity"), anime_data.get("members"),
            anime_data.get("favorites"), anime_data.get("synopsis"),
            anime_data.get("background"), anime_data.get("season"),
            anime_data.get("year"), anime_data.get("broadcast"),
            anime_data.get("cover_url"), anime_data.get("cover_local"),
            anime_data.get("trailer_url")
        ))
        anime_id = cursor.lastrowid
    
    conn.commit()
    cursor.close()
    conn.close()
    return anime_id


def insert_anime_titles(anime_id: int, titles: list):
    """Alternatif başlıkları ekle."""
    conn = get_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    # Önce mevcut başlıkları sil
    cursor.execute("DELETE FROM anime_titles WHERE anime_id = %s", (anime_id,))
    
    # Yeni başlıkları ekle
    for title_info in titles:
        cursor.execute("""
            INSERT INTO anime_titles (anime_id, title, title_type)
            VALUES (%s, %s, %s)
        """, (anime_id, title_info.get("title"), title_info.get("type")))
    
    conn.commit()
    cursor.close()
    conn.close()


def insert_or_get_genre(mal_id: int, name: str) -> int:
    """Tür ekle veya mevcut ID'yi getir."""
    conn = get_connection()
    if not conn:
        return 0
    
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM genres WHERE mal_id = %s OR name = %s", (mal_id, name))
    existing = cursor.fetchone()
    
    if existing:
        genre_id = existing[0]
    else:
        cursor.execute("INSERT INTO genres (mal_id, name) VALUES (%s, %s)", (mal_id, name))
        genre_id = cursor.lastrowid
    
    conn.commit()
    cursor.close()
    conn.close()
    return genre_id


def link_anime_genre(anime_id: int, genre_id: int):
    """Anime-Tür ilişkisi oluştur."""
    conn = get_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    cursor.execute("""
        INSERT IGNORE INTO anime_genres (anime_id, genre_id)
        VALUES (%s, %s)
    """, (anime_id, genre_id))
    conn.commit()
    cursor.close()
    conn.close()


def insert_or_get_theme(mal_id: int, name: str) -> int:
    """Tema ekle veya mevcut ID'yi getir."""
    conn = get_connection()
    if not conn:
        return 0
    
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM themes WHERE mal_id = %s OR name = %s", (mal_id, name))
    existing = cursor.fetchone()
    
    if existing:
        theme_id = existing[0]
    else:
        cursor.execute("INSERT INTO themes (mal_id, name) VALUES (%s, %s)", (mal_id, name))
        theme_id = cursor.lastrowid
    
    conn.commit()
    cursor.close()
    conn.close()
    return theme_id


def link_anime_theme(anime_id: int, theme_id: int):
    """Anime-Tema ilişkisi oluştur."""
    conn = get_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    cursor.execute("""
        INSERT IGNORE INTO anime_themes (anime_id, theme_id)
        VALUES (%s, %s)
    """, (anime_id, theme_id))
    conn.commit()
    cursor.close()
    conn.close()


def insert_or_get_studio(mal_id: int, name: str) -> int:
    """Stüdyo ekle veya mevcut ID'yi getir."""
    conn = get_connection()
    if not conn:
        return 0
    
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM studios WHERE mal_id = %s OR name = %s", (mal_id, name))
    existing = cursor.fetchone()
    
    if existing:
        studio_id = existing[0]
    else:
        cursor.execute("INSERT INTO studios (mal_id, name) VALUES (%s, %s)", (mal_id, name))
        studio_id = cursor.lastrowid
    
    conn.commit()
    cursor.close()
    conn.close()
    return studio_id


def link_anime_studio(anime_id: int, studio_id: int):
    """Anime-Stüdyo ilişkisi oluştur."""
    conn = get_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    cursor.execute("""
        INSERT IGNORE INTO anime_studios (anime_id, studio_id)
        VALUES (%s, %s)
    """, (anime_id, studio_id))
    conn.commit()
    cursor.close()
    conn.close()


def insert_or_get_producer(mal_id: int, name: str) -> int:
    """Yapımcı ekle veya mevcut ID'yi getir."""
    conn = get_connection()
    if not conn:
        return 0
    
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM producers WHERE mal_id = %s OR name = %s", (mal_id, name))
    existing = cursor.fetchone()
    
    if existing:
        producer_id = existing[0]
    else:
        cursor.execute("INSERT INTO producers (mal_id, name) VALUES (%s, %s)", (mal_id, name))
        producer_id = cursor.lastrowid
    
    conn.commit()
    cursor.close()
    conn.close()
    return producer_id


def link_anime_producer(anime_id: int, producer_id: int, producer_type: str = "producer"):
    """Anime-Yapımcı ilişkisi oluştur."""
    conn = get_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    cursor.execute("""
        INSERT IGNORE INTO anime_producers (anime_id, producer_id, producer_type)
        VALUES (%s, %s, %s)
    """, (anime_id, producer_id, producer_type))
    conn.commit()
    cursor.close()
    conn.close()


def get_source_id(source_name: str) -> int:
    """Kaynak ID'sini getir."""
    conn = get_connection()
    if not conn:
        return 0
    
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM sources WHERE name = %s", (source_name,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else 0


def insert_or_update_anime_source(anime_id: int, source_id: int, source_anime_id: str, 
                                   source_slug: str, source_title: str):
    """Anime-Kaynak eşleşmesi ekle veya güncelle."""
    conn = get_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO anime_sources (anime_id, source_id, source_anime_id, source_slug, source_title)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            source_anime_id = VALUES(source_anime_id),
            source_slug = VALUES(source_slug),
            source_title = VALUES(source_title)
    """, (anime_id, source_id, source_anime_id, source_slug, source_title))
    conn.commit()
    cursor.close()
    conn.close()


def get_anime_source(anime_id: int, source_id: int):
    """Anime için belirli kaynaktaki eşleşmeyi getir."""
    conn = get_connection()
    if not conn:
        return None
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM anime_sources 
        WHERE anime_id = %s AND source_id = %s
    """, (anime_id, source_id))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result


def insert_or_update_episode(anime_id: int, episode_number: int, title: str = None) -> int:
    """Bölüm ekle veya güncelle."""
    conn = get_connection()
    if not conn:
        return 0
    
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id FROM episodes WHERE anime_id = %s AND episode_number = %s
    """, (anime_id, episode_number))
    existing = cursor.fetchone()
    
    if existing:
        episode_id = existing[0]
        if title:
            cursor.execute("UPDATE episodes SET title = %s WHERE id = %s", (title, episode_id))
    else:
        cursor.execute("""
            INSERT INTO episodes (anime_id, episode_number, title)
            VALUES (%s, %s, %s)
        """, (anime_id, episode_number, title or f"Episode {episode_number}"))
        episode_id = cursor.lastrowid
    
    conn.commit()
    cursor.close()
    conn.close()
    return episode_id


def insert_video_link(episode_id: int, source_id: int, fansub: str, quality: str, 
                      video_url: str, iframe_url: str = None):
    """Video linki ekle."""
    conn = get_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    # Aynı link varsa güncelle, yoksa ekle
    cursor.execute("""
        INSERT INTO video_links (episode_id, source_id, fansub, quality, video_url, iframe_url)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            video_url = VALUES(video_url),
            iframe_url = VALUES(iframe_url),
            is_active = TRUE,
            updated_at = CURRENT_TIMESTAMP
    """, (episode_id, source_id, fansub, quality, video_url, iframe_url))
    
    conn.commit()
    cursor.close()
    conn.close()


def delete_video_links_for_episode(anime_id: int, episode_number: int, source_id: int = None):
    """Bölümün video linklerini sil."""
    conn = get_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    # Get episode_id from anime_id and episode_number
    cursor.execute("SELECT id FROM episodes WHERE anime_id = %s AND episode_number = %s", (anime_id, episode_number))
    episode = cursor.fetchone()
    if not episode:
        return
    episode_id = episode[0]

    if source_id:
        cursor.execute("""
            DELETE FROM video_links WHERE episode_id = %s AND source_id = %s
        """, (episode_id, source_id))
    else:
        cursor.execute("DELETE FROM video_links WHERE episode_id = %s", (episode_id,))
    
    conn.commit()
    cursor.close()
    conn.close()


def get_video_links(anime_id: int = None, episode_number: int = None, source_name: str = None):
    """Video linklerini getir."""
    conn = get_connection()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    
    query = """
        SELECT 
            vl.*, 
            e.episode_number, e.title as episode_title,
            s.name as source_name,
            a.title as anime_title, a.mal_id
        FROM video_links vl
        JOIN episodes e ON vl.episode_id = e.id
        JOIN sources s ON vl.source_id = s.id
        JOIN animes a ON e.anime_id = a.id
        WHERE vl.is_active = TRUE
    """
    params = []
    
    if anime_id:
        query += " AND a.id = %s"
        params.append(anime_id)
    
    if episode_number:
        query += " AND e.episode_number = %s"
        params.append(episode_number)
    
    if source_name:
        query += " AND s.name = %s"
        params.append(source_name)
    
    query += " ORDER BY e.episode_number, s.name, vl.fansub"
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results


def get_all_mal_ids():
    """Veritabanındaki tüm MAL ID'lerini getir."""
    conn = get_connection()
    if not conn:
        return []
    
    cursor = conn.cursor()
    cursor.execute("SELECT mal_id FROM animes")
    results = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return results

# ─────────────────────────────────────────────────────────────────────────────
# KULLANICI İŞLEMLERİ
# ─────────────────────────────────────────────────────────────────────────────

def get_user_by_username(username: str):
    conn = get_connection()
    if not conn: return None
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def get_user_by_id(user_id: int):
    conn = get_connection()
    if not conn: return None
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def create_user(username, email, password_hash):
    conn = get_connection()
    if not conn: return None
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
            (username, email, password_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return user_id
    except Error as e:
        print(f"[DB] User creation error: {e}")
        return None

def update_watch_history(user_id: int, anime_id: int, episode_number: int, progress_percent: float):
    conn = get_connection()
    if not conn: return False
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO watch_history (user_id, anime_id, episode_number, progress_percent)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            episode_number = VALUES(episode_number),
            progress_percent = VALUES(progress_percent),
            updated_at = CURRENT_TIMESTAMP
    """, (user_id, anime_id, episode_number, progress_percent))
    conn.commit()
    cursor.close()
    conn.close()
    return True

def get_user_watch_history(user_id: int, limit: int = 10):
    conn = get_connection()
    if not conn: return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT wh.*, a.title, a.mal_id, a.cover_url, a.cover_local, a.episodes as total_episodes
        FROM watch_history wh
        JOIN animes a ON wh.anime_id = a.id
        WHERE wh.user_id = %s
        ORDER BY wh.updated_at DESC
        LIMIT %s
    """, (user_id, limit))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def update_watchlist(user_id: int, anime_id: int, status: str):
    conn = get_connection()
    if not conn: return False
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO watchlists (user_id, anime_id, status)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            status = VALUES(status)
    """, (user_id, anime_id, status))
    conn.commit()
    cursor.close()
    conn.close()
    return True

def get_user_watchlist(user_id: int):
    conn = get_connection()
    if not conn: return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT wl.*, a.title, a.mal_id, a.cover_url, a.cover_local, a.score, a.type, a.episodes as total_episodes
        FROM watchlists wl
        JOIN animes a ON wl.anime_id = a.id
        WHERE wl.user_id = %s
        ORDER BY wl.created_at DESC
    """, (user_id,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def get_user_stats(user_id: int):
    """Kullanıcı izleme istatistiklerini hesapla."""
    import re
    conn = get_connection()
    if not conn: return None
    cursor = conn.cursor(dictionary=True)

    # 1. Toplam izlenen bölüm sayısı (Benzersiz her anime için ulaşılan en yüksek bölüm numarasını topla)
    # NOT: Eğer watch_history her bölüm için ayrı satır tutsaydı COUNT(*) olurdu.
    # Ancak mevcut tablo yapısı (UNIQUE user_id, anime_id) ulaşılan son bölümü tutuyor gibi görünüyor.
    cursor.execute("SELECT SUM(episode_number) as total_episodes FROM watch_history WHERE user_id = %s", (user_id,))
    res_eps = cursor.fetchone()
    total_episodes = int(res_eps["total_episodes"] or 0)

    # 2. Toplam izleme süresi tahmini (dakika)
    cursor.execute("""
        SELECT wh.episode_number, a.duration
        FROM watch_history wh
        JOIN animes a ON wh.anime_id = a.id
        WHERE wh.user_id = %s
    """, (user_id,))
    watches = cursor.fetchall()

    total_minutes = 0
    for watch in watches:
        duration_str = watch["duration"] or "24 min"
        mins_per_ep = 0
        hr_match = re.search(r'(\d+)\s*hr', duration_str)
        if hr_match:
            mins_per_ep += int(hr_match.group(1)) * 60
        min_match = re.search(r'(\d+)\s*min', duration_str)
        if min_match:
            mins_per_ep += int(min_match.group(1))

        if mins_per_ep == 0: mins_per_ep = 24 # Varsayılan

        # episode_number o anime'de kaçıncı bölüme gelindiğini gösteriyor.
        total_minutes += mins_per_ep * watch["episode_number"]

    # 3. Tür dağılımı
    cursor.execute("""
        SELECT g.name, COUNT(*) as count
        FROM watch_history wh
        JOIN anime_genres ag ON wh.anime_id = ag.anime_id
        JOIN genres g ON ag.genre_id = g.id
        WHERE wh.user_id = %s
        GROUP BY g.name
        ORDER BY count DESC
        LIMIT 5
    """, (user_id,))
    genres = cursor.fetchall()

    # 4. İzleme listesi durumları
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM watchlists
        WHERE user_id = %s
        GROUP BY status
    """, (user_id,))
    watchlist_stats = cursor.fetchall()

    cursor.close()
    conn.close()

    return {
        "total_episodes": total_episodes,
        "total_minutes": total_minutes,
        "genres": genres,
        "watchlist": watchlist_stats
    }

# ─────────────────────────────────────────────────────────────────────────────
# SOSYAL İŞLEMLER (YORUMLAR)
# ─────────────────────────────────────────────────────────────────────────────

def add_comment(user_id: int, anime_id: int, episode_number: int, content: str, is_spoiler: bool = False):
    conn = get_connection()
    if not conn: return None
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO comments (user_id, anime_id, episode_number, content, is_spoiler)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, anime_id, episode_number, content, is_spoiler))
        conn.commit()
        comment_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return comment_id
    except Error as e:
        print(f"[DB] Comment add error: {e}")
        return None

def get_comments(anime_id: int, episode_number: int):
    conn = get_connection()
    if not conn: return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.*, u.username
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.anime_id = %s AND c.episode_number = %s
        ORDER BY c.created_at DESC
    """, (anime_id, episode_number))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def get_episode_comments(anime_id: int, episode_number: int):
    """Alias for get_comments to maintain compatibility."""
    return get_comments(anime_id, episode_number)

def get_anime_genres(anime_id: int):
    conn = get_connection()
    if not conn: return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT g.* FROM genres g
        JOIN anime_genres ag ON g.id = ag.genre_id
        WHERE ag.anime_id = %s
    """, (anime_id,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def get_anime_studios(anime_id: int):
    conn = get_connection()
    if not conn: return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT s.* FROM studios s
        JOIN anime_studios ast ON s.id = ast.studio_id
        WHERE ast.anime_id = %s
    """, (anime_id,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def get_anime_full_details(mal_id: int):
    """Anime'nin tüm detaylarını (türler, stüdyolar, bölümler) getir."""
    anime = get_anime_by_mal_id(mal_id)
    if not anime:
        return None

    anime_id = anime["id"]
    anime["genres"] = get_anime_genres(anime_id)
    anime["studios"] = get_anime_studios(anime_id)

    # Bölümleri getir
    conn = get_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT e.*,
                   (SELECT COUNT(*) FROM video_links WHERE episode_id = e.id AND is_active = TRUE) as video_count
            FROM episodes e
            WHERE e.anime_id = %s
            ORDER BY e.episode_number
        """, (anime_id,))
        anime["episodes_list"] = cursor.fetchall()
        cursor.close()
        conn.close()
    else:
        anime["episodes_list"] = []

    return anime

def get_user_stats(user_id: int):
    conn = get_connection()
    if not conn: return None
    cursor = conn.cursor(dictionary=True)

    stats = {}

    # Toplam izlenen bölüm sayısı
    cursor.execute("SELECT COUNT(*) as total_watched FROM watch_history WHERE user_id = %s", (user_id,))
    stats["total_watched"] = cursor.fetchone()["total_watched"]

    # İzleme listesindeki durumlar
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM watchlists
        WHERE user_id = %s
        GROUP BY status
    """, (user_id,))
    stats["watchlist_counts"] = {row["status"]: row["count"] for row in cursor.fetchall()}

    # En çok izlenen türler
    cursor.execute("""
        SELECT g.name, COUNT(*) as count
        FROM watch_history wh
        JOIN anime_genres ag ON wh.anime_id = ag.anime_id
        JOIN genres g ON ag.genre_id = g.id
        WHERE wh.user_id = %s
        GROUP BY g.id
        ORDER BY count DESC
        LIMIT 5
    """, (user_id,))
    stats["favorite_genres"] = cursor.fetchall()

    cursor.close()
    conn.close()
    return stats

def delete_comment(comment_id: int, user_id: int):
    """Sadece yorumun sahibi silebilir."""
    conn = get_connection()
    if not conn: return False
    cursor = conn.cursor()
    cursor.execute("DELETE FROM comments WHERE id = %s AND user_id = %s", (comment_id, user_id))
    affected = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    return affected > 0

def get_trending_anime(limit: int = 10, days: int = 7):
    """Son X günde en çok izlenen anime'leri getir."""
    conn = get_connection()
    if not conn: return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT a.*, COUNT(wh.id) as watch_count
        FROM animes a
        JOIN watch_history wh ON a.id = wh.anime_id
        WHERE wh.updated_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
        GROUP BY a.id
        ORDER BY watch_count DESC
        LIMIT %s
    """, (days, limit))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def get_personalized_recommendations(user_id: int, limit: int = 5):
    """Kullanıcının izleme geçmişine göre tür bazlı öneriler getir."""
    conn = get_connection()
    if not conn: return []
    cursor = conn.cursor(dictionary=True)

    # 1. Kullanıcının en çok izlediği 3 türü bul
    cursor.execute("""
        SELECT g.id, COUNT(*) as weight
        FROM watch_history wh
        JOIN anime_genres ag ON wh.anime_id = ag.anime_id
        JOIN genres g ON ag.genre_id = g.id
        WHERE wh.user_id = %s
        GROUP BY g.id
        ORDER BY weight DESC
        LIMIT 3
    """, (user_id,))
    top_genres = [row['id'] for row in cursor.fetchall()]

    if not top_genres:
        # Eğer geçmişi yoksa en popülerlerden öner
        cursor.execute("SELECT * FROM animes ORDER BY popularity ASC LIMIT %s", (limit,))
        results = cursor.fetchall()
    else:
        # 2. Bu türlerdeki, kullanıcının henüz izlemediği en iyi anime'leri bul
        genre_placeholders = ",".join(["%s"] * len(top_genres))
        query = f"""
            SELECT a.*
            FROM animes a
            JOIN anime_genres ag ON a.id = ag.anime_id
            WHERE ag.genre_id IN ({genre_placeholders})
            AND a.id NOT IN (SELECT anime_id FROM watch_history WHERE user_id = %s)
            GROUP BY a.id
            ORDER BY a.score DESC
            LIMIT %s
        """
        cursor.execute(query, (*top_genres, user_id, limit))
        results = cursor.fetchall()

    cursor.close()
    conn.close()
    return results

# ─────────────────────────────────────────────────────────────────────────────
# KEŞFET VE ÖNERİ SİSTEMİ
# ─────────────────────────────────────────────────────────────────────────────

def get_genres():
    """Tüm türleri getir."""
    conn = get_connection()
    if not conn: return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM genres ORDER BY name ASC")
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def discover_animes(filters: dict, limit: int = 24, offset: int = 0):
    """
    Gelişmiş filtreleme ile anime ara.
    filters: {genres: [], year_min: int, year_max: int, status: str, type: str, min_score: float, sort: str}
    """
    conn = get_connection()
    if not conn: return []
    cursor = conn.cursor(dictionary=True)

    query = "SELECT a.* FROM animes a"
    where_clauses = []
    params = []

    # Tür filtreleme (JOIN gerekli)
    if filters.get("genres"):
        genre_ids = filters["genres"]
        placeholders = ",".join(["%s"] * len(genre_ids))
        query += f" JOIN anime_genres ag ON a.id = ag.anime_id"
        where_clauses.append(f"ag.genre_id IN ({placeholders})")
        params.extend(genre_ids)

    # Yıl filtreleme
    if filters.get("year_min"):
        where_clauses.append("a.year >= %s")
        params.append(filters["year_min"])
    if filters.get("year_max"):
        where_clauses.append("a.year <= %s")
        params.append(filters["year_max"])

    # Durum (Status)
    if filters.get("status"):
        where_clauses.append("a.status = %s")
        params.append(filters["status"])

    # Tip (TV, Movie, vb.)
    if filters.get("type"):
        where_clauses.append("a.type = %s")
        params.append(filters["type"])

    # Minimum Puan
    if filters.get("min_score"):
        where_clauses.append("a.score >= %s")
        params.append(filters["min_score"])

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    # Gruplama (Tür filtresi varsa duplicate önlemek için)
    if filters.get("genres"):
        query += " GROUP BY a.id"
        # Birden fazla tür seçildiyse "tümünü içeren" mantığı istenirse burası değişir.
        # Şu an "herhangi birini içeren" mantığı var.

    # Sıralama
    sort = filters.get("sort", "popularity")
    sort_map = {
        "score": "a.score DESC",
        "popularity": "a.popularity ASC",
        "newest": "a.year DESC, a.aired_from DESC",
        "title": "a.title ASC"
    }
    query += f" ORDER BY {sort_map.get(sort, 'a.popularity ASC')}"

    # Limit & Offset
    query += " LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def get_personalized_recommendations(user_id: int, limit: int = 10):
    """Kullanıcının izleme geçmişine göre tür bazlı öneriler sunar."""
    conn = get_connection()
    if not conn: return []
    cursor = conn.cursor(dictionary=True)

    # 1. Kullanıcının en çok izlediği ilk 3 türü bul
    cursor.execute("""
        SELECT ag.genre_id, COUNT(*) as count
        FROM watch_history wh
        JOIN anime_genres ag ON wh.anime_id = ag.anime_id
        WHERE wh.user_id = %s
        GROUP BY ag.genre_id
        ORDER BY count DESC
        LIMIT 3
    """, (user_id,))
    top_genres = [row["genre_id"] for row in cursor.fetchall()]

    if not top_genres:
        # Geçmiş yoksa genel trending/top anime döndür
        cursor.close()
        conn.close()
        return get_trending_anime(limit)

    # 2. Bu türlerdeki, kullanıcının henüz izlemediği yüksek puanlı anime'leri bul
    placeholders = ",".join(["%s"] * len(top_genres))
    query = f"""
        SELECT a.*, g.name as main_genre
        FROM animes a
        JOIN anime_genres ag ON a.id = ag.anime_id
        JOIN genres g ON ag.genre_id = g.id
        WHERE ag.genre_id IN ({placeholders})
        AND a.id NOT IN (SELECT anime_id FROM watch_history WHERE user_id = %s)
        GROUP BY a.id
        ORDER BY a.score DESC, a.popularity ASC
        LIMIT %s
    """
    params = top_genres + [user_id, limit]

    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

# ─────────────────────────────────────────────────────────────────────────────
# JSON SERİLEŞTİRME YARDIMCI FONKSİYONU
# ─────────────────────────────────────────────────────────────────────────────

def serialize_for_json(data):
    """Datetime ve Decimal tiplerini JSON için string/float'a çevir."""
    from decimal import Decimal
    from datetime import datetime, date
    if isinstance(data, list):
        return [serialize_for_json(item) for item in data]
    elif isinstance(data, dict):
        return {k: serialize_for_json(v) for k, v in data.items()}
    elif isinstance(data, (datetime, date)):
        return data.isoformat()
    elif isinstance(data, Decimal):
        return float(data)
    else:
        return data


if __name__ == "__main__":
    print("Initializing database...")
    init_database()
