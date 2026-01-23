import os
import uuid
import random
import subprocess
import logging
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mass_mail
from .models import VideoFile, Episode, Subscription

logger = logging.getLogger(__name__)

# ==================== FFmpeg Helper Functions ====================

def _check_ffmpeg_available() -> bool:
    """Check if FFmpeg is available on the system"""
    try:
        # Windows uses 'where', Unix uses 'which'
        cmd = 'where' if os.name == 'nt' else 'which'
        result = subprocess.run([cmd, 'ffmpeg'], capture_output=True)
        return result.returncode == 0
    except:
        return False


def _get_video_duration(video_path: str) -> float:
    """Get video duration in seconds using FFprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return float(result.stdout.strip())
    except:
        return 0.0


def _get_video_resolution(video_path: str) -> tuple:
    """Get video resolution (width, height) using FFprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'error', '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'csv=p=0', video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        parts = result.stdout.strip().split(',')
        return int(parts[0]), int(parts[1])
    except:
        return 1920, 1080  # Default


# Quality presets for transcoding
QUALITY_PRESETS = {
    '1080p': {'height': 1080, 'bitrate': '5000k', 'audio_bitrate': '192k'},
    '720p': {'height': 720, 'bitrate': '2500k', 'audio_bitrate': '128k'},
    '480p': {'height': 480, 'bitrate': '1000k', 'audio_bitrate': '96k'},
}


# ==================== Transcoding Tasks ====================

@shared_task(bind=True, max_retries=3)
def encode_episode(self, episode_id, source_path, quality='1080p', upload_to_storage=False):
    """
    Downloads, transcodes to H.265, segments to HLS with AES-128 encryption.
    
    Args:
        episode_id: Episode ID to encode
        source_path: Path to source video file
        quality: Video quality (1080p, 720p, 480p)
        upload_to_storage: Whether to upload to external storage
    """
    try:
        episode = Episode.objects.get(id=episode_id)
        preset = QUALITY_PRESETS.get(quality, QUALITY_PRESETS['720p'])
        
        logger.info(f"Starting encode for {episode} at {quality}")

        # Prepare Output Directory
        output_dir = os.path.join(settings.MEDIA_ROOT, 'videos', str(episode.id), quality)
        os.makedirs(output_dir, exist_ok=True)

        # Encryption Key Generation
        encryption_key = uuid.uuid4().hex
        key_file_path = os.path.join(output_dir, 'segment.key')

        with open(key_file_path, 'w') as f:
            f.write(encryption_key)

        # Key Info File for FFmpeg
        key_uri = f"/api/key/{encryption_key}/"
        key_info_path = os.path.join(output_dir, 'key_info.txt')
        with open(key_info_path, 'w') as f:
            f.write(f"{key_uri}\n")
            f.write(f"{key_file_path}\n")

        # HLS output paths
        hls_output = os.path.join(output_dir, 'index.m3u8')
        segment_filename = os.path.join(output_dir, 'segment_%03d.ts')

        if _check_ffmpeg_available():
            # FFmpeg command with CPU optimization
            # -threads: Use multiple cores
            # -preset: faster = less CPU, slower = better quality
            cmd = [
                'ffmpeg', '-y',
                '-i', source_path,
                # Video encoding
                '-c:v', 'libx265',
                '-tag:v', 'hvc1',
                '-preset', 'medium',  # Balance between speed and quality
                '-crf', '23',  # Constant quality factor
                '-vf', f"scale=-2:{preset['height']}",  # Maintain aspect ratio
                '-b:v', preset['bitrate'],
                '-maxrate', preset['bitrate'],
                '-bufsize', str(int(preset['bitrate'].replace('k', '')) * 2) + 'k',
                # Audio encoding
                '-c:a', 'aac',
                '-ar', '48000',
                '-b:a', preset['audio_bitrate'],
                # HLS settings
                '-hls_time', '10',
                '-hls_playlist_type', 'vod',
                '-hls_key_info_file', key_info_path,
                '-hls_segment_filename', segment_filename,
                # CPU optimization
                '-threads', '0',  # Auto-detect CPU cores
                hls_output
            ]

            logger.info(f"Running FFmpeg: {' '.join(cmd[:10])}...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise Exception(f"FFmpeg failed: {result.stderr[:500]}")
        else:
            # Mock HLS for testing without FFmpeg
            logger.warning("FFmpeg not available, creating mock HLS")
            with open(hls_output, 'w') as f:
                f.write("#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:10\n")
                f.write("#EXT-X-MEDIA-SEQUENCE:0\n#EXTINF:10.000000,\n")
                f.write("segment_000.ts\n#EXT-X-ENDLIST")

        # Calculate file size
        total_size = 0
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if file.endswith(('.ts', '.m3u8', '.key')):
                    total_size += os.path.getsize(os.path.join(root, file))

        # Upload to external storage if requested
        if upload_to_storage:
            try:
                from core.storage import get_storage
                storage = get_storage()
                remote_path = f"videos/{episode.id}/{quality}/index.m3u8"
                storage.upload(hls_output, remote_path)
                hls_output = storage.get_stream_url(remote_path)
                logger.info(f"Uploaded to storage: {remote_path}")
            except Exception as e:
                logger.warning(f"Storage upload failed, keeping local: {e}")

        # Save to Database
        VideoFile.objects.update_or_create(
            episode=episode,
            quality=quality,
            defaults={
                'hls_path': hls_output,
                'encryption_key': encryption_key,
                'file_size_bytes': total_size,
                'is_hardcoded': False
            }
        )

        logger.info(f"Successfully encoded {episode} to {quality} ({total_size} bytes)")
        return f"Successfully encoded {episode} to {quality}"

    except Episode.DoesNotExist:
        return f"Episode {episode_id} not found"
    except Exception as e:
        logger.exception(f"Encoding failed for episode {episode_id}")
        self.retry(exc=e, countdown=60)


@shared_task
def encode_episode_multi_quality(episode_id, source_path, qualities=None, upload_to_storage=False):
    """
    Encode episode in multiple quality levels.
    
    Args:
        episode_id: Episode ID  
        source_path: Source video file path
        qualities: List of qualities to encode (default: all based on source)
        upload_to_storage: Upload to external storage
    """
    if qualities is None:
        # Determine qualities based on source resolution
        width, height = _get_video_resolution(source_path)
        
        if height >= 1080:
            qualities = ['1080p', '720p', '480p']
        elif height >= 720:
            qualities = ['720p', '480p']
        else:
            qualities = ['480p']
    
    results = []
    for quality in qualities:
        result = encode_episode.delay(episode_id, source_path, quality, upload_to_storage)
        results.append(result.id)
    
    logger.info(f"Started multi-quality encode for episode {episode_id}: {qualities}")
    return {'episode_id': episode_id, 'tasks': results, 'qualities': qualities}


# ==================== Thumbnail Generation ====================

@shared_task
def generate_thumbnail(episode_id, source_path=None, force=False):
    """
    Generate thumbnail for an episode from video.
    Selects a random frame between 4-6 minutes.
    
    Args:
        episode_id: Episode ID
        source_path: Path to video file (optional, uses existing video)
        force: Force regenerate even if thumbnail exists
    """
    try:
        episode = Episode.objects.select_related('season__anime').get(id=episode_id)
        
        # Skip if thumbnail exists and not forcing
        if episode.thumbnail and not force:
            logger.info(f"Thumbnail already exists for {episode}")
            return f"Thumbnail already exists for episode {episode_id}"
        
        # Find source video if not provided
        if not source_path:
            video_file = episode.video_files.first()
            if video_file and os.path.exists(video_file.hls_path.replace('.m3u8', '.mp4')):
                source_path = video_file.hls_path.replace('.m3u8', '.mp4')
            else:
                return f"No video source found for episode {episode_id}"
        
        if not _check_ffmpeg_available():
            logger.warning("FFmpeg not available for thumbnail generation")
            return "FFmpeg not available"
        
        # Get video duration
        duration = _get_video_duration(source_path)
        
        if duration < 60:
            # Very short video, take frame at 25%
            timestamp = duration * 0.25
        else:
            # Random frame between 4-6 minutes (or 20-30% for shorter videos)
            min_time = min(240, duration * 0.2)  # 4 min or 20%
            max_time = min(360, duration * 0.3)  # 6 min or 30%
            timestamp = random.uniform(min_time, max_time)
        
        # Output path
        thumbnail_dir = os.path.join(settings.MEDIA_ROOT, 'thumbnails', str(episode.season.anime.id))
        os.makedirs(thumbnail_dir, exist_ok=True)
        thumbnail_filename = f"ep_{episode.id}_{uuid.uuid4().hex[:8]}.jpg"
        thumbnail_path = os.path.join(thumbnail_dir, thumbnail_filename)
        
        # FFmpeg command to extract frame
        cmd = [
            'ffmpeg', '-y',
            '-ss', str(timestamp),
            '-i', source_path,
            '-vframes', '1',
            '-q:v', '2',  # High quality JPEG
            '-vf', 'scale=1280:-2',  # 720p width, maintain aspect
            thumbnail_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Thumbnail generation failed: {result.stderr}")
            return f"Thumbnail generation failed: {result.stderr[:200]}"
        
        # Update episode with thumbnail URL
        thumbnail_url = f"{settings.MEDIA_URL}thumbnails/{episode.season.anime.id}/{thumbnail_filename}"
        episode.thumbnail = thumbnail_url
        episode.save(update_fields=['thumbnail'])
        
        logger.info(f"Generated thumbnail for {episode} at {timestamp:.1f}s")
        return f"Generated thumbnail for episode {episode_id}"
        
    except Episode.DoesNotExist:
        return f"Episode {episode_id} not found"
    except Exception as e:
        logger.exception(f"Thumbnail generation failed for episode {episode_id}")
        return f"Thumbnail generation failed: {str(e)}"


@shared_task
def generate_thumbnails_batch(anime_id):
    """Generate thumbnails for all episodes of an anime"""
    from content.models import Anime
    
    try:
        anime = Anime.objects.get(id=anime_id)
        episodes = Episode.objects.filter(
            season__anime=anime,
            thumbnail__isnull=True
        ).values_list('id', flat=True)
        
        for ep_id in episodes:
            generate_thumbnail.delay(ep_id)
        
        return f"Started thumbnail generation for {len(episodes)} episodes"
        
    except Anime.DoesNotExist:
        return f"Anime {anime_id} not found"


# ==================== Email Notification Tasks ====================

@shared_task
def send_new_episode_email_task(episode_id):
    """
    Sends email notifications to all subscribers of the anime.
    """
    try:
        episode = Episode.objects.select_related('season__anime').get(id=episode_id)
        anime = episode.season.anime
        subscribers = Subscription.objects.filter(anime=anime).select_related('user')

        messages = []
        subject = f"New Episode Available: {anime.title} - {episode.title or 'Episode ' + str(episode.number)}"
        from_email = settings.DEFAULT_FROM_EMAIL

        for sub in subscribers:
            if sub.user.email:
                message = f"Hello {sub.user.username},\n\nA new episode of {anime.title} is now available on AniScrap!\n\nWatch now: {settings.SITE_URL}/watch/{episode.id}\n\nEnjoy!\nThe AniScrap Team"
                messages.append((subject, message, from_email, [sub.user.email]))

        if messages:
            send_mass_mail(messages, fail_silently=False)

        logger.info(f"Sent {len(messages)} notification emails for episode {episode.id}")
        return f"Sent {len(messages)} emails for Episode {episode.id}"

    except Episode.DoesNotExist:
        return f"Episode {episode_id} not found."


# ==================== Jikan Sync Task ====================

@shared_task
def sync_anime_from_jikan(anime_id, mal_id):
    """
    Sync anime data from Jikan API (async task wrapper).
    """
    import asyncio
    from content.models import Anime
    from scraper_module.services.jikan import jikan
    
    try:
        anime = Anime.objects.get(id=anime_id)
        
        # Run async sync in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(jikan.sync_anime_to_db(anime, mal_id))
        finally:
            loop.close()
        
        logger.info(f"Synced anime {anime.title} from Jikan (MAL ID: {mal_id})")
        return f"Successfully synced anime {anime_id} from MAL"
        
    except Anime.DoesNotExist:
        return f"Anime {anime_id} not found"
    except Exception as e:
        logger.exception(f"Jikan sync failed for anime {anime_id}")
        return f"Jikan sync failed: {str(e)}"

