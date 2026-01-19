# AniScrap

**AniScrap**, modern ve ölçeklenebilir bir anime yayın ve yönetim platformudur. Django, Celery ve Redis altyapısı üzerine inşa edilmiş olup, HLS yayın, video şifreleme ve gelişmiş bir yönetim paneli sunar.

## 🚀 Özellikler

*   **Video İşleme:** FFmpeg ile otomatik HLS transcoding (H.265/HEVC), segmentleme ve şifreleme.
*   **Gelişmiş Yönetim Paneli:** Django-Unfold tabanlı, sunucu sağlığı (CPU/RAM), bant genişliği ve içerik istatistiklerini gösteren dashboard.
*   **Akıllı İçerik Yönetimi:** Anime ve bölümler için Soft Delete özelliği, toplu işlemler.
*   **Reklam Sistemi:** Dinamik reklam yerleşimi (AdSlots).
*   **Ödeme ve Abonelik:** Shopier entegrasyonu ve abonelik planları.
*   **Güvenlik:** IP tabanlı ban sistemi, oturum hızı sınırlama (Rate Throttling).
*   **Scraping:** Otomatik içerik çekme modülü (`scraper_module`).

## 🛠️ Teknoloji Yığını

*   **Backend:** Python 3, Django 5.0+
*   **API:** Django REST Framework
*   **Veritabanı:** MySQL (Prod), SQLite (Dev)
*   **Kuyruk & Önbellek:** Redis, Celery
*   **Video:** FFmpeg, libtorrent
*   **Frontend:** Django Templates, Tailwind CSS, Plyr, Hls.js

## 📋 Gereksinimler

Kuruluma başlamadan önce sisteminizde aşağıdakilerin yüklü olduğundan emin olun:

*   Python 3.10 veya üzeri
*   Redis Server
*   FFmpeg (Video işleme için gereklidir)
*   MySQL (Prod ortamı için opsiyonel)

## ⚙️ Kurulum

1.  **Depoyu Klonlayın:**
    ```bash
    git clone https://github.com/bariskeser/aniscrap-core.git
    cd aniscrap-core
    ```

2.  **Sanal Ortam Oluşturun:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows için: venv\Scripts\activate
    ```

3.  **Bağımlılıkları Yükleyin:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Ortam Değişkenleri:**
    Varsayılan olarak proje SQLite veritabanı kullanacak şekilde ayarlanmamıştır. Geliştirme ortamı için `USE_SQLITE` değişkenini kullanabilirsiniz.

    Linux/Mac:
    ```bash
    export USE_SQLITE=True
    ```
    Windows (Powershell):
    ```powershell
    $env:USE_SQLITE="True"
    ```

5.  **Veritabanı Kurulumu:**
    Otomatik kurulum komutunu kullanarak veritabanını oluşturun ve varsayılan yönetici hesabını açın:
    ```bash
    python manage.py migrate
    # Veya tam kurulum için (migration + superuser + site settings):
    python manage.py init_aniscrap
    ```
    *Not: `init_aniscrap` komutu `admin` kullanıcısını `123123123` şifresiyle oluşturur.*

6.  **Sunucuyu Başlatın:**
    ```bash
    python manage.py runserver
    ```

7.  **Celery Worker (Arka Plan İşleri):**
    Video işleme gibi görevler için Celery worker'ı ayrı bir terminalde çalıştırın:
    ```bash
    celery -A aniscrap_core worker -l info
    ```

## 🌐 Kullanım

*   **Ana Sayfa:** `http://localhost:8000/`
*   **Yönetim Paneli:** `http://localhost:8000/admin/`
    *   Kullanıcı: `admin`
    *   Şifre: `123123123` (Eğer `init_aniscrap` çalıştırıldıysa)

## 📁 Proje Yapısı

*   `aniscrap_core/`: Proje ayarları.
*   `core/`: Temel modeller, dashboard ve yardımcı araçlar.
*   `content/`: Anime, Bölüm ve Video modelleri.
*   `users/`: Kullanıcı yönetimi.
*   `billing/`: Ödeme ve abonelik sistemleri.
*   `scraper_module/`: İçerik botları.

## 📝 Notlar

*   Video yüklemeleri ve encode işlemleri arka planda Celery ile yapılır. Redis servisinin çalıştığından emin olun.
*   Prod ortamında `DEBUG=False` ve MySQL kullanılması önerilir.
