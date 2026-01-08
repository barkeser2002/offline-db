"""
Yapılandırma dosyası
"""

# MySQL Veritabanı Ayarları
DB_CONFIG = {
    "host": "ip.bariskeser.com",
    "user": "bariskeser",
    "password": "B@ris3422",
    "database": "anime-index",
    "charset": "utf8mb4",
    "collation": "utf8mb4_unicode_ci"
}

# Jikan API (MyAnimeList)
JIKAN_API_BASE = "https://api.jikan.moe/v4"
JIKAN_RATE_LIMIT = 1.0  # saniye (API rate limit)

# Cover resimleri klasörü
COVER_DIR = "./covers"

# Güncellenen anime'lerin takibi
UPDATED_IDS_FILE = "updated_mal_ids.json"

# Adaptör ayarları
ADAPTERS = {
    "animecix": True,
    "animely": False,  # Devre dışı - çalışmıyor
    "anizle": True,
    "tranime": True,
    "turkanime": True  # Yeni eklendi
}

# FlareSolverr ayarları (CloudFlare bypass için)
FLARESOLVERR_URL = "http://localhost:8191/v1"

# Paralel işlem sayısı (30-200 arası önerilir)
MAX_WORKERS = 200

# Video işlemleri için paralel worker sayısı
VIDEO_WORKERS = 100

# Batch senkronizasyon varsayılan boyutları
DEFAULT_BATCH_SIZE = 50
MAX_BATCH_SIZE = 200

# HTTP Timeout
HTTP_TIMEOUT = 30

# Web API Ayarları
API_HOST = "0.0.0.0"
API_PORT = 8988
