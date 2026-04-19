# 🗺️ AniScraper Development Plan — 6 Month Roadmap
## Voor Jules: Dit is je complete werklijst. Lees dit altijd eerst.

---

## ⚡ Hızlı Bağlam (Proje Özeti)

Bu proje bir anime izleme platformudur:
- **Backend**: Django + DRF + Celery + Redis + Django Channels (WebSocket)
- **Frontend**: Next.js (TypeScript) + TailwindCSS + NextUI
- **DB**: SQLite (dev) → PostgreSQL (prod)
- **Auth**: JWT tabanlı  
- **WatchParty**: Gerçek zamanlı WebSocket tabanlı birlikte izleme odaları

**Kod kalitesi hedefleri**:
- Güvenlik: OWASP Top 10'a tam uyum
- Performans: N+1 query yok, her endpoint ≤100ms (p95)
- Erişilebilirlik: WCAG 2.1 AA
- Test coverage: ≥80%

---

## ✅ YAPILDI (Şu Ana Kadar Tamamlanan)

### Güvenlik
- [x] LocalStorage path traversal koruması (`_get_safe_path`)
- [x] RoomViewSet IDOR fix (host-only update/delete)
- [x] WatchParty WebSocket auth (DenyConnection for anonymous)
- [x] Audit logs IDOR fix (users/views.py)
- [x] IP spoofing / rate limit bypass fix (core/utils.py + billing/views.py)
- [x] Subscribe endpoint rate limiting
- [x] Chat XSS fix
- [x] Emote DoS rate limiting

### Performans
- [x] WatchTimeBadgeStrategy: `distinct().count()` → `set(values_list(...))`
- [x] ConsumptionBadgeStrategy: List loading → DB subqueries (pilot-connoisseur, loyal-fan, type counts, otaku)
- [x] GenreBadgeStrategy: Python-level aggregation
- [x] ConsistencyBadgeStrategy: Queryset caching
- [x] RoomViewSet N+1: `select_related('episode__season__anime')`
- [x] Admin views N+1: `list_select_related` eklendi
- [x] EpisodeViewSet: gereksiz `select_related` kaldırıldı
- [x] HomeViewSet: gereksiz `select_related` kaldırıldı
- [x] UserProfileAPIView: gereksiz `select_related` kaldırıldı
- [x] KeyServeView: gereksiz `select_related` kaldırıldı
- [x] AnimeViewSet list: `prefetch_related('genres')` eklendi
- [x] WebSocket bildirimleri Celery'e taşındı

### Erişilebilirlik / UX
- [x] Avatar bileşenlerine alt text eklendi
- [x] Switch bileşenlerine aria-label
- [x] Arama inputlarına aria-label + focus states
- [x] Chat input disabled state (boş mesaj)
- [x] Admin upload formu isRequired
- [x] Klavye focus visibility (focus-visible ring)
- [x] Storage path traversal testleri eklendi

---

## 📅 AY 1 — Güvenlik Derinleştirmesi (Mart 2026)

### 1.1 CSRF & Session Güvenliği
**Hedef dosyalar**: `aniscrap_core/settings.py`, `users/views.py`
- [x] CSRF_TRUSTED_ORIGINS kontrolü — production URL'leri ekle
- [x] Session cookie güvenlik ayarları: `SESSION_COOKIE_SECURE=True`, `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SAMESITE='Lax'`
- [x] `SECURE_BROWSER_XSS_FILTER = True` ayarı
- [x] `SECURE_CONTENT_TYPE_NOSNIFF = True` ayarı
- [x] `X_FRAME_OPTIONS = 'DENY'` confirm edilmesi

### 1.2 API Rate Limiting Genişletme
**Hedef dosyalar**: `aniscrap_core/settings.py`, `users/views.py`, `content/views.py`
- [x] Tüm authentication endpoint'lerine rate limit (login, register, password reset)
- [x] WatchLog create endpoint'ine rate limit (spam önleme)
- [x] Review create endpoint'ine rate limit
- [x] django-ratelimit veya DRF throttling genişletme
- [x] Rate limit aşımında 429 + Retry-After header dönme

### 1.3 Input Validasyonu
**Hedef dosyalar**: `users/serializers.py`, `content/serializers.py`, `apps/watchparty/serializers.py`
- [x] Username XSS pattern validation (sadece alphanumeric + _- izin ver)
- [x] Bio alanı HTML escape / strip validasyonu
- [x] Review content sanitization (bleach kullan)
- [x] Magnet link URL validation (sadece magnet: ve https:// izin ver)
- [x] File upload MIME type validation (covers/storage alanları)

### 1.4 Dependency Security Audit
**Hedef**: `requirements.txt`, `frontend/package.json`
- [x] `pip-audit` çalıştır, tüm bilinen CVE'leri gider
- [x] `npm audit` → tüm HIGH ve CRITICAL'ları fix et
- [x] Channels >= 4.x, Django >= 5.x güncel versiyona geç
- [x] `djangorestframework-simplejwt` en son versiyona güncelle

### 1.5 Security Headers (Middleware)
**Hedef dosyalar**: `aniscrap_core/settings.py`
- [x] Content-Security-Policy header ekle (nonce tabanlı inline script koruması)
- [x] Referrer-Policy: strict-origin-when-cross-origin
- [x] Permissions-Policy header (camera, microphone deny)
- [x] HSTS header (Strict-Transport-Security) - sadece prod

---

## 📅 AY 2 — Performans & Önbellekleme (Nisan 2026)

### 2.1 Redis Caching Stratejisi
**Hedef dosyalar**: `content/views.py`, `users/views.py`, `aniscrap_core/settings.py`
- [x] `django-cacheops` veya native Django cache framework kur
- [x] AnimeViewSet list cache: 5 dakika TTL
- [x] HomeViewSet trending/seasonal cache: 10 dakika TTL
- [x] Badge hesaplama sonuçları cache (user.id bazlı): 30 dakika TTL
- [x] Cache invalidation strategy: signal tabanlı (AnimeAdmin'de save signal → cache clear)

### 2.2 Database Optimizasyonları
**Hedef dosyalar**: tüm `models.py` dosyaları
- [x] WatchLog modeline `db_index=True` ekle (user + watched_at combined index)
- [x] Subscription modeline compound index (user, anime)
- [x] Room modelinde `is_active` field için index
- [ ] `django-pgbouncer` veya connection pooling kur (production için)
- [ ] Slow query logger ekle (≥100ms sorguları logla)

### 2.3 Kalan N+1 Sorgu Tespiti
**Hedef**: tüm DRF viewset'ler
- [ ] `django-debug-toolbar` + `nplusone` kur (sadece development)
- [ ] `billing/views.py` viewset'lerini incele
- [ ] `scraper_module/views.py` incele
- [x] GenreBadgeStrategy genre_savant: hâlâ list tabanlı → subquery'e geç
- [x] Bildirim endpoint'lerinde N+1 kontrol et

### 2.4 Celery Task Optimizasyonları
**Hedef dosyalar**: `content/tasks.py`, `users/badge_system.py`
- [ ] Badge hesaplama task'ını Celery'e taşı (senkron değil asenkron)
- [ ] Failed task retry stratejisi `max_retries=3, countdown=60)` ekle
- [ ] Task result backend ayarla (Redis)
- [ ] Flower dashboard kur (Celery monitoring)
- [ ] Beat scheduler: periyodik badge re-evaluation task (günde 1 kez full re-check)

### 2.5 Frontend Performansı
**Hedef**: `frontend/src/` tüm pages
- [ ] `next/image` kullan — tüm `<img>` taglarını `<Image>` ile değiştir
- [ ] Route-based code splitting doğrula (`loading.tsx` her route'a)
- [ ] `React.memo` ve `useMemo` kritik bileşenlere (PartyPanel, AnimeCard)
- [ ] API response pagination (infinite scroll için cursor pagination)
- [ ] Lighthouse score ≥90 (Performance, Accessibility, Best Practices, SEO)

---

## 📅 AY 3 — Özellik Geliştirmesi (Mayıs 2026)

### 3.1 Gelişmiş Arama
**Hedef**: `content/views.py`, `frontend/src/app/discovery/`
- [ ] Full-text search (Django + PostgreSQL `SearchVector` veya Elasticsearch entegrasyonu)
- [ ] Genre + type + status multi-filter kombinasyonu
- [x] Rating bazlı sıralama (review ortalaması)
- [ ] Arama sonuçlarını highlight et (hangi alanda eşleşti)
- [ ] Arama geçmişi (son 10 arama, localStorage)
- [ ] Autocomplete endpoint (prefix bazlı anime önerisi)

### 3.2 Kullanıcı Öneri Sistemi  
**Yeni dosyalar**: `content/recommendations.py`, `content/api/views.py`
- [ ] Collaborative filtering (benzer kullanıcıların izlediği animeler)
- [ ] Content-based filtering (izlenen anime'lerin genre'larına göre öneri)
- [ ] `/api/v1/anime/recommended/` endpoint'i
- [ ] "Çünkü X izledin" açıklama metni
- [ ] Öneri logic'ini Celery task olarak çalıştır (günlük hesaplama)

### 3.3 WatchParty İyileştirmeleri
**Hedef**: `apps/watchparty/`, `frontend/src/components/watchparty/`
- [x] Room şifresi (private rooms): Room modeline `password` alanı ekle
- [ ] Chat mesajı silme (host yetkisi)
- [x] Katılımcı limit (Room modeline `max_participants` alanı)
- [ ] Watch history sync (herkes aynı pozisyonda)
- [ ] Emoji reaction burst animasyonu (frontend)
- [ ] Party modu: host pause/play kontrolü audience'a yayınla

### 3.4 Bildirim Sistemi Geliştirmesi
**Hedef**: `users/models.py` (Notification), `users/views.py`, `frontend/src/app/notifications/`
- [ ] Email bildirimleri (yeni bölüm çıktığında subscriber'lara mail)
- [ ] Push notification (Web Push API + Service Worker)
- [ ] Bildirim tercihleri sayfası (hangi bildirim türleri aktif)
- [ ] Bildirim gruplama (aynı anime'den birden fazla epizot bildirimi → tek bildirim)
- [x] Okundu/okunmadı bulk işlem endpoint'i

### 3.5 Sosyal Özellikler
**Yeni dosyalar**: `users/social.py`, migration'lar
- [ ] Kullanıcı takip sistemi (Follow model: follower, following)
- [ ] Aktivite akışı: takip ettiklerinin badge kazanımları, izlemeleri
- [ ] Profil public/private seçeneği
- [ ] Kullanıcı listeleri (watchlist, completed, dropped)
- [ ] Liste paylaşma (public link ile)

---

## 📅 AY 4 — Test Kapsamı & Kalite (Haziran 2026)

### 4.1 Backend Test Coverage ≥80%
**Hedef**: `*/tests/` klasörleri
- [ ] `users/badge_system.py` tüm badge'ler için unit test (her badge strategy)
- [ ] `core/storage.py` path traversal + upload/delete/exists testleri (YAPILDI, genişlet)
- [ ] `apps/watchparty/consumers.py` WebSocket testleri (YAPILDI, genişlet)
- [x] `users/views.py` IDOR + auth testleri (YAPILDI, genişlet)
- [ ] `billing/views.py` payment flow testleri
- [x] `content/views.py` N+1 query assertion testleri (assertNumQueries)
- [ ] Celery task'ların mock testi
- [ ] Cache invalidation testleri
- [ ] `pytest-cov` ile coverage raporu üret (CI'da minimum %80 enforce et)

### 4.2 Integration Testleri
**Yeni dosyalar**: `tests/integration/`
- [ ] Tam WatchParty akışı: oda oluştur → katıl → mesaj gönder → çık
- [ ] Badge kazanım akışı: watch log oluştur → badge sistemi tetikle → verify
- [ ] Subscription akışı: abone ol → epizot yayınla → bildirim al
- [ ] Auth akışı: register → login → JWT refresh → logout
- [ ] Admin upload akışı: anime oluştur → epizot ekle → video yükle

### 4.3 E2E Testleri (Playwright)
**Yeni klasör**: `e2e/`
- [ ] Playwright kur (`npx playwright install`)
- [ ] Kritik kullanıcı yolculukları test et:
  - Anasayfa → Anime detay → İzle → WatchLog kaydı
  - Kayıt → Login → Profil güncelle
  - WatchParty oluştur → Başka kullanıcı katılsın → Chat
  - Admin panel → Anime yükle
- [ ] CI'da Firefox + Chromium + WebKit karşılaştırmalı test

### 4.4 Yük Testleri
**Araçlar**: Locust veya k6
- [ ] `/api/v1/anime/` endpoint'i: 100 concurrent kullanıcı, 10 saniye → ≥5 req/s
- [ ] WebSocket: 50 concurrent WatchParty bağlantısı
- [ ] Badge sistemi: 1000 WatchLog insert → badge hesaplama ≤2 saniye
- [ ] Sonuçları `.jules/performance-benchmarks.md`'a kaydet

### 4.5 CI/CD Güçlendirme
**Hedef**: `.github/workflows/`
- [ ] Branch protection rules: main'e direct push kapat, PR + review zorunlu
- [ ] GitHub Actions: `pytest --cov` + coverage badge
- [ ] GitHub Actions: `flake8` + `black` linting
- [ ] GitHub Actions: `npm run lint` + TypeScript typecheck
- [ ] GitHub Actions: Security scan (`bandit` Python, `npm audit`)
- [ ] Dependabot kur (weekly dependency update PR'ları)

---

## 📅 AY 5 — Frontend İyileştirmeleri (Temmuz 2026)

### 5.1 PWA (Progressive Web App)
**Hedef**: `frontend/src/`
- [ ] `next-pwa` paketi kur
- [ ] Service Worker ile offline support (anime detay sayfaları cache)
- [ ] Web App Manifest (`manifest.json`) güncelle
- [ ] Push notification kaydı (Web Push API)
- [ ] Install prompt (Android + Chrome)

### 5.2 Erişilebilirlik Audit (WCAG 2.1 AA)
**Hedef**: tüm `frontend/src/app/` pages
- [ ] `axe-core` + `jest-axe` ile automated a11y test
- [ ] Klavye navigasyonu: tab order logical mi? (focus trap modallarda)
- [ ] Screen reader test: NVDA/VoiceOver ile kritik akışlar
- [ ] Color contrast oranı: tüm metin ≥4.5:1 (WCAG AA)
- [ ] `role`, `aria-*`, `tabIndex` review
- [ ] Skip navigation link ekle (ilk fokuslanabilir eleman)
- [ ] Form hata mesajları `aria-describedby` ile input'a bağla

### 5.3 Internationalization (i18n)
**Paket**: `next-intl`
- [ ] Türkçe + İngilizce dil desteği
- [ ] Tüm hardcoded string'leri `t('key')` fonksiyonuyla değiştir
- [ ] `/tr/` ve `/en/` route prefix
- [ ] Dil seçicisi (navbar'a flag + dil adı dropdown)
- [ ] Sayılar + tarihler için locale-aware formatters

### 5.4 Tema & Tasarım Sistemi
**Hedef**: `frontend/src/components/`, `tailwind.config.ts`
- [ ] Dark / Light / Auto tema geçişi (system preference respect)
- [ ] Renk tokenları tanımla (CSS variables: --color-primary, --color-surface, vs.)
- [ ] Design token dökümanı (`DESIGN_TOKENS.md`)
- [ ] Animasyon: page transition (framer-motion ile)
- [ ] Skeleton loading state tüm listeler için
- [ ] Empty state bileşeni (her liste için custom illustrasyon)

### 5.5 Mobile & Responsive
- [ ] Tüm sayfaları 375px+ viewport'ta test et
- [ ] WatchParty mobile layout (panel overlay yerine bottom sheet)
- [ ] Video player mobile gesture (swipe forward/backward)
- [ ] Touch targets minimum 44×44px (WCAG 2.5.5)
- [ ] Hamburger menu animasyonu iyileştirme

---

## 📅 AY 6 — DevOps & Infrastructure (Ağustos 2026)

### 6.1 Containerization
**Yeni dosyalar**: `Dockerfile`, `docker-compose.yml`, `docker-compose.prod.yml`
- [ ] Backend Dockerfile (multi-stage build: builder + runtime)
- [ ] Frontend Dockerfile (Next.js standalone output)
- [ ] `docker-compose.yml` (dev): Django + Celery + Redis + PostgreSQL + Next.js
- [ ] Health check endpoint'leri: `/api/health/` (DB + Redis check)
- [ ] `.dockerignore` ekle

### 6.2 Monitoring & Observability
**Araçlar**: Prometheus + Grafana veya Sentry
- [ ] Sentry entegrasyonu (hem frontend hem backend)
- [ ] `django-prometheus` ile metrics endpoint (`/metrics`)
- [ ] Celery task başarı/başarısızlık metrikleri
- [ ] Custom dashboard: DAU, badge kazanım rate, WatchParty kullanımı
- [ ] Alert: error rate >1% → Slack/email bildirim

### 6.3 Yapılandırılmış Logging
**Hedef**: `aniscrap_core/settings.py`
- [ ] JSON format logging (structlog kur)
- [ ] Request ID middleware (her request'e UUID ekle, tüm log satırlarında)
- [ ] Audit log: admin action'ları logla (kim, ne zaman, ne yaptı)
- [ ] Log rotation (logrotate veya CloudWatch)
- [ ] Sensitive data masking (token, password loglanmasın)

### 6.4 API Dokümantasyonu
**Araç**: drf-spectacular (OpenAPI 3.0)
- [x] `drf-spectacular` kur + Swagger UI ekle (`/api/docs/`)
- [x] Tüm ViewSet'lere `@extend_schema` decorator ekle
- [x] Request/Response örnekleri her endpoint için
- [x] Authentication akışı dokümante et (JWT flow)
- [ ] Postman collection otomatik üret

### 6.5 Backup & Disaster Recovery
- [ ] PostgreSQL automated daily backup (pg_dump → S3)
- [ ] Redis dump periyodik backup
- [ ] Media dosyaları (cover görselleri) S3 migration
- [ ] `django-storages` ile S3 backend (`MEDIA_ROOT` → S3)
- [ ] Recovery drill: backup'tan restore test et (yılda 1 kez)

### 6.6 Migration Planning
**KRITIK**: SQLite → PostgreSQL
- [ ] `pgloader` ile SQLite → PostgreSQL migration scripti
- [ ] Full-text search: `GIN index` + `SearchVector` geç
- [ ] Tüm `order_by` ifadelerini PostgreSQL uyumlu yap (case-sensitive dikkat)
- [ ] Tüm datetime sorgularını `USE_TZ=True` ile test et
- [ ] Connection pooling: PgBouncer kur

---

## 🔁 Devam Eden Görevler (Her Sprint)

- [ ] `.jules/bolt.md` — her performans iyileştirmesinden sonra not ekle
- [ ] `.jules/sentinel.md` — her güvenlik fix'inden sonra vulnerability + prevention ekle
- [ ] `.jules/palette.md` — her UI/UX değişikliğinden sonra öğrenilenler ekle
- [ ] Kod review: karmaşık logic'ler için `# JULES:` comment bırak
- [ ] `test_plan.md` güncelle (yeni feature → yeni test case ekle)
- [ ] Tüm migration'lar `--check` ile CI'da test edilsin

---

## 🏗️ Mimari Kararlar (Değiştirme, Sebep Sor)

1. **Badge sistemi** `BadgeStrategy` pattern kullanıyor — yeni badge eklemek için yeni class yaz, `STRATEGIES` listine ekle
2. **Storage backend** `LocalStorage` sadece dev içindir — prod'da S3StorageBackend (Ay 6'da yapılacak)
3. **WebSocket** Django Channels kullanıyor — Celery notification offloading zaten var (`content/tasks.py`)
4. **Auth** `djangorestframework-simplejwt` — token refresh frontend'de her 5 dakikada yapılıyor
5. **Frontend** Next.js App Router kullanıyor — tüm yeni sayfa `app/` altına, `pages/` kullanma
6. **Rate limiting** hem DRF throttling hem Redis tabanlı custom — ikisini karıştırma, bir tanesi seç

---

## ⚠️ Bilinen Sorunlar & Teknik Borç

- [x] `content/admin.py` EpisodeAdmin: `search_fields` ile admin N+1 riski — `search_fields` çakıştığında DB full-scan yapıyor
- `users/badge_system.py` GenreBadgeStrategy `genre_savant`: hâlâ list tabanlı `episode_ids` kullanıyor → subquery'e çevir (YAPILDI)
- `scraper_module/` — test coverage %0, teknik borç yüksek
- [x] `blueprints/` klasörü boş — ne içereceği belirsiz, silinebilir veya dokümante edilmeli
- [x] `replace.py`, `patch_test.py`, `verify_navbar.py` vb. root klasördeki artefact dosyaları — temizle
- [x] `db.sqlite3` versiyon kontrolüne eklenmemeli — `.gitignore`'a ekle
- [x] Frontend `next.config.ts`'de `eslint.ignoreDuringBuilds: true` — bunu kaldır, lint hatalarını gider

---

## 🎯 Jules için Çalışırken Kurallar

1. **Önce oku**: Değiştireceğin dosyayı tam oku, asla hunklerle çalışma
2. **Test yaz**: Yeni feature → önce test, sonra implement (TDD)
3. **Güvenliği öncele**: Güvenlik fix'leri daima önce gider, `sentinel.md`'ye yaz
4. **Performans ölç**: N+1 fix öncesi ve sonrası `assertNumQueries` ile doğrula
5. **Çakışmayan değişiklik**: Aynı dosyaya birden fazla PR açma — tek PR'da birleştir
6. **Açık bırakma**: Her PR ya merged ya closed olmalı, limbo'da kalmasın
7. **Migration dikkat**: Her model değişikliği `makemigrations` + `migrate` gerektirir
8. **.jules/ dosyalarına ekle**: Her fix sonrası ilgili MD dosyasına öğreni yaz
