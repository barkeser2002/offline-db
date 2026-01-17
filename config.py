"""
Yapılandırma dosyası
"""
import os
from dotenv import load_dotenv

load_dotenv()

# SQLite Veritabanı Ayarları
DB_PATH = os.getenv("DB_PATH", "anime_db.sqlite")

# Jikan API (MyAnimeList)
JIKAN_API_BASE = "https://api.jikan.moe/v4"
JIKAN_RATE_LIMIT = 1.0  # saniye (API rate limit)

# Cover resimleri klasörü
COVER_DIR = "./covers"

# Güncellenen anime'lerin takibi
UPDATED_IDS_FILE = "updated_mal_ids.json"

# Flask API ayarları
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8988"))

# Adaptör ayarları
ADAPTERS = {
    "animecix": True,
    "animely": False,  # Devre dışı - çalışmıyor
    "anizle": True,
    "tranime": True,
    "turkanime": True  # Yeni eklendi
}

# FlareSolverr ayarları (CloudFlare bypass için)
FLARESOLVERR_URL = "http://node-kyb.bariskeser.com:8191/v1"

# Paralel işlem sayısı (30-200 arası önerilir)
MAX_WORKERS = 200

# Video işlemleri için paralel worker sayısı
VIDEO_WORKERS = 100

# Batch senkronizasyon varsayılan boyutları
DEFAULT_BATCH_SIZE = 50
MAX_BATCH_SIZE = 200

# HTTP Timeout
HTTP_TIMEOUT = 30

# Proxy Whitelist (SSRF Koruması)
ALLOWED_PROXY_DOMAINS = [
    "anizmplayer.com",
    "cdn.bunny.sh",
    "video.bunnycdn.com",
]

# Web API Ayarları
API_HOST = "0.0.0.0"
API_PORT = 8988
