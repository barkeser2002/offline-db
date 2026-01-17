import requests
import re
from typing import Dict, Any, List, Tuple
import db
from adapters import animecix, anizle, tranime, turkanime

def check_video_link_alive(url: str, timeout: int = 10) -> Tuple[bool, Dict[str, Any]]:
    """Check if a video link is still working."""
    try:
        # Some links might block HEAD requests
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        is_alive = response.status_code < 400

        quality = "unknown"
        if "1080" in url: quality = "1080p"
        elif "720" in url: quality = "720p"
        elif "480" in url: quality = "480p"

        return is_alive, {"url": url, "quality": quality, "type": "direct"}
    except Exception:
        try:
            response = requests.get(url, timeout=timeout, stream=True)
            is_alive = response.status_code < 400
            response.close()
            return is_alive, {"url": url, "quality": "unknown", "type": "direct"}
        except Exception:
            return False, {}

def ensure_episode_videos(mal_id: int, episode_number: int, anime_db_id: int, force_refresh: bool = False):
    """Ensure that an episode has video links in the database."""
    if not force_refresh:
        existing = db.get_video_links(anime_db_id, episode_number)
        if existing:
            return existing

    sources = db.get_anime_sources(mal_id)
    if not sources:
        return []

    # Get or create episode
    episode = db.get_episode_by_number(anime_db_id, episode_number)
    if not episode:
        episode_id = db.insert_or_update_episode(anime_db_id, episode_number, f"Episode {episode_number}")
    else:
        episode_id = episode["id"]

    found_links = []

    for source in sources:
        source_name = source["source_name"]
        source_id = source["source_id"]
        source_slug = source["source_slug"]
        source_anime_id = source["source_anime_id"]

        try:
            links = []
            if source_name == "anizle":
                # Try different slug patterns
                slugs = [
                    f"{source_slug}-{episode_number}-bolum",
                    f"{source_slug}-bolum-{episode_number}"
                ]
                for s in slugs:
                    links = anizle.get_episode_streams(s)
                    if links: break
            elif source_name == "animecix":
                # Animecix requires fetching all episodes to find the one matching episode_number
                cix_anime = animecix.CixAnime(id=source_anime_id, title="")
                cix_eps = cix_anime.episodes
                target_ep = None
                for ep in cix_eps:
                    match = re.search(r'(\d+)', ep.title)
                    if match and int(match.group(1)) == episode_number:
                        target_ep = ep
                        break
                if target_ep and target_ep.url:
                    links = animecix.get_episode_streams(target_ep.url)
            elif source_name == "tranime":
                # Try direct slug first
                ep_slug = f"{source_slug}-{episode_number}-bolum-izle"
                links = tranime.get_episode_streams(ep_slug)

                if not links:
                    # Fallback: get episodes and find matching number
                    tr_eps = tranime.get_anime_episodes(source_slug)
                    for ep in tr_eps:
                        if ep.episode_number == episode_number:
                            links = tranime.get_episode_streams(ep.slug)
                            break
            elif source_name == "turkanime":
                ep_slug = f"{source_slug}-{episode_number}"
                # TurkAnime might return TurkAnimeStream objects
                raw_links = turkanime.get_episode_streams(ep_slug)
                for rl in raw_links:
                    if hasattr(rl, 'url'):
                        links.append({
                            "url": rl.url,
                            "quality": getattr(rl, 'quality', '720p'),
                            "fansub": getattr(rl, 'fansub', 'TurkAnime')
                        })
                    else:
                        links.append(rl)

            for link in links:
                if isinstance(link, dict):
                    url = link.get("url") or link.get("videoUrl")
                    quality = link.get("label") or link.get("quality") or "default"
                    fansub = link.get("fansub") or source_name.capitalize()
                else:
                    url = getattr(link, 'url', None)
                    quality = getattr(link, 'quality', 'default')
                    fansub = getattr(link, 'fansub', source_name.capitalize())

                if not url or url in found_links: continue

                db.insert_video_link(episode_id, source_id, url, quality, fansub)
                found_links.append(url)

        except Exception as e:
            print(f"[VideoService] Error fetching from {source_name}: {e}")

    return db.get_video_links(anime_db_id, episode_number)

def remove_dead_video_link(video_id: int):
    """Deactivate a dead video link."""
    return db.remove_dead_video_link(video_id)
