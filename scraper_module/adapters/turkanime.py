"""
TurkAnime.tv Adaptörü
Türk anime çeviri sitesi - CloudFlare korumalı
"""

import re
from typing import List, Optional, Tuple
from dataclasses import dataclass

try:
    from .turkanime_bypass import fetch, get_real_url, unmask_real_url, BASE_URL
except ImportError:
    from adapters.turkanime_bypass import fetch, get_real_url, unmask_real_url, BASE_URL


@dataclass
class TurkAnimeEpisode:
    """Bölüm bilgisi"""

    episode_number: int
    title: str
    slug: str
    url: str


@dataclass
class TurkAnimeStream:
    """Video stream bilgisi"""

    url: str
    quality: str
    fansub: str
    player: str  # Alucard, Bankai, Sibnet vs.


@dataclass
class TurkAnime:
    """TurkAnime anime objesi"""

    id: str
    title: str
    slug: str
    url: str
    episodes: List[TurkAnimeEpisode] = None

    def __post_init__(self):
        if self.episodes is None:
            self.episodes = []


def search_anime(query: str) -> List[Tuple[str, str, str]]:
    """
    Anime ara.

    Returns:
        List of (anime_id, slug, title)
    """
    results = []
    try:
        # TurkAnime arama endpoint'i
        html = fetch(f"/arama?q={query}")

        # Anime kartlarını parse et
        # Pattern: <a href="/anime/slug" class="...">Title</a>
        pattern = r'href="(/anime/([^"]+))"[^>]*>([^<]+)</a>'
        matches = re.findall(pattern, html, re.IGNORECASE)

        for url, slug, title in matches:
            # ID olarak slug kullan
            anime_id = slug
            title = title.strip()
            if title and slug:
                results.append((anime_id, slug, title))

        # Tekrarları kaldır
        seen = set()
        unique_results = []
        for item in results:
            if item[1] not in seen:
                seen.add(item[1])
                unique_results.append(item)

        return unique_results[:10]  # İlk 10 sonuç

    except Exception as e:
        print(f"[TurkAnime] Arama hatası: {e}")
        return []


def get_anime_details(slug: str) -> Optional[TurkAnime]:
    """
    Anime detaylarını getir.
    """
    try:
        html = fetch(f"/anime/{slug}")

        # Başlığı çıkar
        title_match = re.search(r"<h1[^>]*>([^<]+)</h1>", html)
        title = title_match.group(1).strip() if title_match else slug

        anime = TurkAnime(id=slug, title=title, slug=slug, url=f"/anime/{slug}")

        return anime

    except Exception as e:
        print(f"[TurkAnime] Detay hatası: {e}")
        return None


def get_anime_episodes(slug: str) -> List[TurkAnimeEpisode]:
    """
    Anime bölümlerini getir.
    """
    episodes = []
    try:
        # Bölüm listesi sayfası
        html = fetch(f"/anime/{slug}")

        # Bölüm linklerini bul
        # Pattern: href="/video/slug-X-bolum"
        pattern = r'href="(/video/([^"]+))"[^>]*>\s*(?:<[^>]+>)*\s*(\d+)\.\s*Bölüm'
        matches = re.findall(pattern, html, re.IGNORECASE)

        if not matches:
            # Alternatif pattern
            pattern = r'href="(/video/([^"]+)-(\d+)-bolum[^"]*)"'
            matches = re.findall(pattern, html, re.IGNORECASE)

        for url, ep_slug, ep_num in matches:
            try:
                ep_number = int(ep_num)
                episodes.append(
                    TurkAnimeEpisode(
                        episode_number=ep_number,
                        title=f"{ep_number}. Bölüm",
                        slug=ep_slug,
                        url=url,
                    )
                )
            except ValueError:
                continue

        # Sırala
        episodes.sort(key=lambda x: x.episode_number)

        return episodes

    except Exception as e:
        print(f"[TurkAnime] Bölüm listesi hatası: {e}")
        return []


def get_episode_streams(episode_slug: str) -> List[TurkAnimeStream]:
    """
    Bölüm video stream'lerini getir.

    Args:
        episode_slug: Bölüm slug'ı (örn: "one-piece-1-bolum")
    """
    streams = []
    try:
        # Video sayfasını getir
        html = fetch(f"/video/{episode_slug}")

        # Fansub seçeneklerini bul
        fansub_pattern = r'data-fansub="([^"]+)"[^>]*data-video="([^"]+)"'
        fansub_matches = re.findall(fansub_pattern, html)

        if fansub_matches:
            for fansub, video_id in fansub_matches:
                # Her fansub için videoları getir
                video_streams = _get_video_sources(video_id, fansub)
                streams.extend(video_streams)
        else:
            # Direkt video kaynaklarını bul
            # iframe src pattern
            iframe_pattern = r'<iframe[^>]+src="([^"]+)"'
            iframe_matches = re.findall(iframe_pattern, html)

            for iframe_url in iframe_matches:
                if "turkanime" in iframe_url or "embed" in iframe_url:
                    try:
                        real_url = (
                            get_real_url(iframe_url)
                            if "eyJ" in iframe_url
                            else iframe_url
                        )
                        streams.append(
                            TurkAnimeStream(
                                url=real_url,
                                quality="720p",
                                fansub="TurkAnime",
                                player="embed",
                            )
                        )
                    except:
                        pass

        # Şifreli video URL'lerini çöz
        encrypted_pattern = r'data-encrypt="([^"]+)"'
        encrypted_matches = re.findall(encrypted_pattern, html)

        for cipher in encrypted_matches:
            try:
                real_url = get_real_url(cipher)
                if real_url:
                    streams.append(
                        TurkAnimeStream(
                            url=real_url,
                            quality="720p",
                            fansub="TurkAnime",
                            player="decrypt",
                        )
                    )
            except:
                pass

        return streams

    except Exception as e:
        print(f"[TurkAnime] Stream hatası: {e}")
        return []


def _get_video_sources(video_id: str, fansub: str) -> List[TurkAnimeStream]:
    """
    Video ID'den kaynakları getir.
    """
    streams = []
    try:
        # Video kaynakları endpoint'i
        html = fetch(f"/ajax/video?id={video_id}")

        # Player linklerini parse et
        player_pattern = r'href="([^"]+)"[^>]*>([^<]+)</a>'
        player_matches = re.findall(player_pattern, html)

        for player_url, player_name in player_matches:
            player_name = player_name.strip()

            # TurkAnime player URL'leri mask'li olabilir
            if "turkanime" in player_url and "/player/" in player_url:
                try:
                    real_url = unmask_real_url(player_url)
                    streams.append(
                        TurkAnimeStream(
                            url=real_url,
                            quality="720p",
                            fansub=fansub,
                            player=player_name,
                        )
                    )
                except:
                    pass
            elif player_url.startswith("http"):
                streams.append(
                    TurkAnimeStream(
                        url=player_url,
                        quality="720p",
                        fansub=fansub,
                        player=player_name,
                    )
                )

    except Exception as e:
        print(f"[TurkAnime] Video kaynakları hatası: {e}")

    return streams


def get_episode_by_number(slug: str, episode_number: int) -> Optional[TurkAnimeEpisode]:
    """
    Belirli bölümü getir.
    """
    # Önce direkt URL dene
    ep_slug = f"{slug}-{episode_number}-bolum"

    try:
        html = fetch(f"/video/{ep_slug}")
        if html and "404" not in html[:500]:
            return TurkAnimeEpisode(
                episode_number=episode_number,
                title=f"{episode_number}. Bölüm",
                slug=ep_slug,
                url=f"/video/{ep_slug}",
            )
    except:
        pass

    # Yoksa bölüm listesinden bul
    episodes = get_anime_episodes(slug)
    for ep in episodes:
        if ep.episode_number == episode_number:
            return ep

    return None


# Test
if __name__ == "__main__":
    print("TurkAnime Adaptör Testi")
    print("-" * 50)

    # Arama testi
    results = search_anime("one piece")
    print(f"Arama sonuçları: {len(results)}")
    for r in results[:3]:
        print(f"  - {r[2]} ({r[1]})")

    if results:
        slug = results[0][1]

        # Bölüm testi
        episodes = get_anime_episodes(slug)
        print(f"\nBölümler: {len(episodes)}")
        for ep in episodes[:3]:
            print(f"  - {ep.episode_number}. Bölüm: {ep.slug}")

        # Stream testi
        if episodes:
            streams = get_episode_streams(episodes[0].slug)
            print(f"\nStreamler: {len(streams)}")
            for s in streams[:3]:
                print(f"  - [{s.player}] {s.fansub}: {s.url[:60]}...")
