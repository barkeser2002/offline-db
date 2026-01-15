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
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("[DB] Tablolar başarıyla oluşturuldu (InnoDB).")
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
        """, (anime_id, episode_number, title or f"{episode_number}. Bölüm"))
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


if __name__ == "__main__":
    print("Veritabanı başlatılıyor...")
    init_database()
