"""
BYPASS Modülü, TürkAnime'deki şifreyle saklanan elementlerini çözmek
ve firewall'i kandirmak için gerekli fonksiyonlari / rutinleri içerir.

- Fetch(url)->str                   Firefox TLS & HTTP/3 taklitli GET Request fonksiyonu

- obtain_key()->bytes               TürkAnime'nin iframe şifrelerken kullandigi AES anahtari bulur
- decrypt_cipher(key, data)->str    CryptoJS.AES.decrypt python implementasyonu
- get_real_url(cipher)->str         TürkAnime'nin iframe şifresini çözüp gerçek video URL'sini getir

- decrypt_jsjiamiv7(cipher, key):   Reverse jsjiamiv7 -> decodeURIComponent(base64(RC4(KSA + PRGA)))
- obtain_csrf()->str                TürkAnime'nin encrypted tuttuğu csrf tokeni bul, decryptle,getir
- unmask_real_url(masked_url):      Alucard, Bankai, Amaterasu, HDVID url maskesini çöz.
"""
import os
import re
from base64 import b64decode
import json
from hashlib import md5
from tempfile import NamedTemporaryFile

try:
    from appdirs import user_cache_dir
except ImportError:
    def user_cache_dir():
        return os.path.join(os.path.expanduser("~"), ".cache")

try:
    from Crypto.Cipher import AES
except ImportError:
    try:
        from Cryptodome.Cipher import AES
    except ImportError:
        AES = None
        print("[TurkAnime] UYARI: pycryptodome yüklü değil!")

try:
    from curl_cffi import requests as curl_requests
except ImportError:
    curl_requests = None
    print("[TurkAnime] UYARI: curl_cffi yüklü değil!")

import requests as std_requests

# FlareSolverr entegrasyonu
FLARESOLVERR_URL = os.environ.get("FLARESOLVERR_URL", "http://node-kyb.bariskeser.com:8191/v1")

session = None
BASE_URL = "https://www.turkanime.co"
ALT_BASE_URLS = [
    "https://www.turkanime.co",
    "https://turkanime.co", 
    "https://www.turkanime.life",
    "https://turkanime.life"
]


class CFBypassError(Exception):
    """CloudFlare bypass hatası"""
    pass


def _flaresolverr_request(url: str, method: str = "GET") -> dict:
    """FlareSolverr ile CloudFlare bypass"""
    try:
        payload = {
            "cmd": "request.get" if method == "GET" else "request.post",
            "url": url,
            "maxTimeout": 60000
        }
        resp = std_requests.post(FLARESOLVERR_URL, json=payload, timeout=65)
        data = resp.json()
        if data.get("status") == "ok":
            return {
                "text": data.get("solution", {}).get("response", ""),
                "cookies": data.get("solution", {}).get("cookies", []),
                "status_code": data.get("solution", {}).get("status", 200)
            }
    except Exception as e:
        print(f"[FlareSolverr] Hata: {e}")
    return None


def _try_curl_cffi_direct(url: str) -> tuple:
    """curl_cffi ile direkt bağlantı dene - farklı impersonate'ler ile"""
    if not curl_requests:
        return None, None
    
    impersonates = ["chrome120", "chrome110", "chrome", "firefox"]
    
    for imp in impersonates:
        try:
            sess = curl_requests.Session(impersonate=imp, allow_redirects=True)
            sess.headers.update({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
                "Upgrade-Insecure-Requests": "1",
            })
            resp = sess.get(url, timeout=8)  # Daha kısa timeout
            if resp.status_code == 200 and "cf-browser-verification" not in resp.text.lower():
                return sess, resp
        except Exception:
            continue
    
    return None, None


def _get_cf_session():
    """CloudFlare bypass session oluştur"""
    # Önce FlareSolverr dene
    result = _flaresolverr_request(BASE_URL)
    if result and result.get("status_code") == 200:
        # Yeni bir session oluştur ve çerezleri aktar
        if curl_requests:
            cf_session = curl_requests.Session(impersonate="firefox", allow_redirects=True)
        else:
            cf_session = std_requests.Session()
        
        for cookie in result.get("cookies", []):
            cf_session.cookies.set(cookie.get("name"), cookie.get("value"))
        
        cf_session.last_method = "flaresolverr"
        cf_session._cached_text = result.get("text", "")
        return cf_session
    
    return None


def fetch(path, headers={}):
    """Curl-cffi kullanarak HTTP/3 ve Firefox TLS Fingerprint Impersonation
       eyleyerek GET request atmak IUAM aktif olmadigi sürece CF'yi bypassliyor. """
    global session, BASE_URL
    
    # Init: Çerezleri cart curt oluştur, yeni domain geldiyse yönlendir.
    if session is None:
        # Önce alternatif URL'leri curl_cffi ile dene
        for alt_url in ALT_BASE_URLS:
            sess, resp = _try_curl_cffi_direct(alt_url + "/")
            if sess and resp:
                session = sess
                BASE_URL = resp.url
                BASE_URL = BASE_URL[:-1] if BASE_URL.endswith('/') else BASE_URL
                print(f"[TurkAnime] Bağlantı başarılı: {BASE_URL}")
                break
        
        # curl_cffi başarısız olduysa FlareSolverr dene
        if session is None:
            print(f"[TurkAnime] curl_cffi başarısız, FlareSolverr deneniyor...")
            cf_session = _get_cf_session()
            if cf_session is not None:
                session = cf_session
                print(f"[TurkAnime] CF bypass başarılı (FlareSolverr)")
            else:
                # Son çare: Normal requests
                session = std_requests.Session()
                session.headers.update({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
                })
                print(f"[TurkAnime] UYARI: CF bypass yapılamadı, bazı özellikler çalışmayabilir")
    
    if path is None:
        return ""
    
    # Get request'i yolla
    path = path if path.startswith("/") else "/" + path
    headers["X-Requested-With"] = "XMLHttpRequest"
    
    try:
        resp = session.get(BASE_URL + path, headers=headers, timeout=15)
        if resp.status_code == 403 or "cf-browser-verification" in resp.text.lower():
            # CF engeli - FlareSolverr dene
            result = _flaresolverr_request(BASE_URL + path)
            if result and result.get("text"):
                return result.get("text", "")
            raise ConnectionError("Cloudflare engeli aşılamadı")
        return resp.text
    except Exception as e:
        # Hata durumunda FlareSolverr ile tekrar dene
        result = _flaresolverr_request(BASE_URL + path)
        if result and result.get("text"):
            return result.get("text", "")
        raise ConnectionError(f"Bağlantı hatası: {e}")


"""
Videoların gerçek URL'lerini decryptleyen fonksiyonlar
örn: eyJjdCI6IldXUmRNWFdCMG15T253dXUmRNWFd3V -> https://dv97.sibnet.ru/15/80/112314.mp4
"""

def obtain_key() -> bytes:
    """
    Şifreli iframe url'sini decryptlemek için gerekli anahtarı döndürür. 
    Javascript dosyalarının isimleri ve anahtar, periyodik olarak değiştiğinden,
    güncel şifre için aşağıdaki algoritmayla tersine mühendislik yapıyoruz:

    - /embed/ endpointin çağırdığı 2. javascript dosyasını aç.
    - Bu dosyanın içinde çağırılan diğer iki javascript dosyasını da regexle bul.
    - Bu iki dosyadan içinde "decrypt" ifadesi geçeni seç
    - Bir liste olarak obfuscate edilmiş bu javascript dosyasından şifreyi edin.
    """

    try:
        # İlk javascript dosyasını ve importladığı dosyaları bul.
        js1 = fetch(
                re.findall(
                    r"/embed/js/embeds\..*?\.js",
                    fetch("/embed/#/url/"))[1]
            )
        js1_imports = re.findall("[a-z0-9]{16}",js1)
        # Bu dosyalardan içinde "decrypt" ifadesi geçen dosyayı bul.
        j2 = fetch(f'/embed/js/embeds.{js1_imports[0]}.js')
        if "'decrypt'" not in j2:
            j2 = fetch(f'/embed/js/embeds.{js1_imports[1]}.js')
        # Obfuscated listeyi parse'la.
        match = re.search(
                'function a\\d_0x[\\w]{1,4}\\(\\){var _0x\\w{3,8}=\\[(.*?)\\];',j2
            )
        if match is None:
            return b""
        obfuscate_list = match.group(1)
        # Listedeki en uzun elemanı, yani şifremizi bul.
        return max(
            obfuscate_list.split("','"),
            key=lambda i:len( re.sub(r"\\x\d\d","?",i))
        ).encode()
    except (IndexError, AttributeError):
        return b""



def decrypt_cipher(key: bytes, data: bytes) -> str:
    """ CryptoJS.AES.decrypt'in python implementasyonu
        referans:
            - https://stackoverflow.com/a/36780727
            - https://gist.github.com/ysfchn/e96304fb41375bad0fdf9a5e837da631
    """
    if AES is None:
        print("[TurkAnime] AES modülü yüklü değil!")
        return ""
    
    def salted_key(data: bytes, salt: bytes, output: int = 48):
        assert len(salt) == 8, len(salt)
        data += salt
        key = md5(data).digest()
        final_key = key
        while len(final_key) < output:
            key = md5(key + data).digest()
            final_key += key
        return final_key[:output]
    def unpad(data: bytes) -> bytes:
        return data[:-(data[-1] if isinstance(data[-1],int) else ord(data[-1]))]
    # Remove URL path from the string.
    b64 = b64decode(data)
    cipher = json.loads(b64)
    cipher_text = b64decode(cipher["ct"])
    iv = bytes.fromhex(cipher["iv"])
    salt = bytes.fromhex(cipher["s"])
    # Create new AES object with using salted key as key.
    crypt = AES.new(salted_key(key, salt, output=32), iv=iv, mode=AES.MODE_CBC)
    # Decrypt link and unpad it.
    try:
        return unpad(crypt.decrypt(cipher_text)).decode("utf-8")
    except (UnicodeDecodeError, ValueError):
        return ""



def get_real_url(url_cipher: str, cache=True) -> str:
    """ Videonun gerçek url'sini decrypt'le, parolayı da cache'le. """
    cache_dir = user_cache_dir()
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, "turkanimu_key.cache")

    # Daha önceden cache'lenmiş key varsa onunla şifreyi çözmeyi dene.
    if cache and os.path.isfile(cache_file):
        with open(cache_file,"r",encoding="utf-8") as f:
            cached_key = f.read().strip().encode()
            plaintext = decrypt_cipher(cached_key, url_cipher.encode())
        if plaintext:
            return plaintext

    # Cache'lenmiş key işe yaramadıysa, yeni key'i edin ve decryptlemeyi dene.
    key = obtain_key()
    plaintext = decrypt_cipher(key, url_cipher.encode())
    if not plaintext:
        raise ValueError("Embed URLsinin şifresi çözülemedi.")
    # Cache'i güncelle
    if cache:
        with open(cache_file,"w",encoding="utf-8") as f:
            f.write(key.decode("utf-8"))
    return plaintext




"""
TürkAnime'nin kendi player'larından url çıkartan fonksiyonlar (Alucard, Bankai, Amaterasu vs.)
örn: http://turkanime.co/sources/UW1EN2VPcExLUXpiaDRqcnV0d -> https://alucard.stream/cdn/playlist/3S3CtAJxAZ
"""

PLAYERJS_URL = "/js/player.js"
PLAYERJS_CSRF = None

def decrypt_jsjiamiv7(ciphertext, key):
    """
    jsjiamiv7 obfuscator ile şifrelenmiş bi cipher'ı decryptleyen fonksiyon
    - Cipher nedense non-standart bir alfabeyle translate edilmiş, onu normal base64 alfabesine çevir
    - Sonra base64 decode eyle
    - Sonra RC4 (KSA + PRGA) algoritması ile şifreyi çöz https://en.wikipedia.org/wiki/RC4
    - Galiba bu internette ilk. v5, v6 decode'layan buldum da, v7 decodelayan proje bulamadım.
    """
    _CUSTOM = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/"
    _STD    = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    _TRANSLATE = str.maketrans(_CUSTOM, _STD)
    t = ciphertext.translate(_TRANSLATE)
    t += "=" * (-len(t) % 4)
    data = b64decode(t).decode("utf-8")

    S = list(range(256))
    j = 0
    klen = len(key)
    # KSA
    for i in range(256):
        j = (j + S[i] + ord(key[i % klen])) & 0xff
        S[i], S[j] = S[j], S[i]
    # PRGA
    i = j = 0
    out = []
    for ch in data:
        i = (i + 1) & 0xff
        j = (j + S[i]) & 0xff
        S[i], S[j] = S[j], S[i]
        out.append(chr(ord(ch) ^ S[(S[i] + S[j]) & 0xff]))
    return "".join(out)


def obtain_csrf():
    """
    /js/player.js dosyasındaki jsjiamiv7 ile şifrelenmiş csrf tokeni edin.
    - regex ile key'i çıkar ve ciphertext olabilecek bütün text'leri çıkar
    - bütün adayları key ile decryptlemeyi dene, başarılı çıkan sonuç csrf tokenidir.
    """
    res = fetch(PLAYERJS_URL)
    # Key'i çıkar
    key = re.findall(r"csrf-token':[^\n\)]+'([^']+)'\)", res, re.IGNORECASE)
    # Bütün Ciphertext adaylarını çıkar
    candidates = re.findall(r"'([a-zA-Z\d\+\/]{96,156})',",res)
    assert key and candidates
    key = key[0]

    # Hepsini decrypt'lemeyi dene, başarılı olanı döndür
    decrypted_list = [decrypt_jsjiamiv7(ct,key) for ct in candidates]
    return next((i for i in decrypted_list if re.search(r"^[a-zA-Z/\+]+$",i)), None)


def unmask_real_url(url_mask):
    """ TürkAnime'nin kendi playerlarının url maskesini çözer. """
    global PLAYERJS_CSRF
    assert "turkanime" in url_mask
    if PLAYERJS_CSRF is None:
        try:
            PLAYERJS_CSRF = obtain_csrf()
            if PLAYERJS_CSRF is None:
                raise LookupError
        except:
            print("ERROR: CSRF bulunamadı.")
            return url_mask

    MASK = url_mask.split("/player/")[1]
    headers = {"Csrf-Token": PLAYERJS_CSRF, "cf_clearance": "dull"}
    res = fetch(f"/sources/{MASK}/false",headers)

    try:
        url = json.loads(res)["response"]["sources"][-1]["file"]
        if url.startswith("//"):
            url = "https:" + url
    except:
        return url_mask
    return url


def get_alucard_m3u8(url):
    """ MPV'nin video'yu oynatabilmesi için en yüksek çözünürlüklü alucard m3u8 stream'i indir"""
    global session, BASE_URL
    if curl_requests:
        if session is None:
            session = curl_requests.Session(impersonate="firefox", allow_redirects=True)
            res = session.get(BASE_URL)
            assert res.status_code == 200, ConnectionError
            BASE_URL = res.url
            BASE_URL = BASE_URL[:-1] if BASE_URL.endswith('/') else BASE_URL

        res = session.get(url)
        m3u8_url = re.findall("https://.*",res.text)[-1]
        res = session.get(m3u8_url)
        with NamedTemporaryFile(suffix=".m3u8", delete=False) as m3u8:
            m3u8.write(res.text.encode())
        return m3u8.name
    else:
        return url
