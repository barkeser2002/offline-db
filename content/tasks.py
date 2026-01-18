import os
import subprocess
import uuid
import shutil
from celery import shared_task
from django.conf import settings
from .models import Episode, VideoKey

@shared_task
def encode_episode(episode_id):
    try:
        episode = Episode.objects.get(id=episode_id)

        # Check if source exists
        if not episode.source_file:
            print(f"No source file for Episode {episode_id}")
            return

        source_path = episode.source_file.path

        # Create output directory
        # Structure: media/anime_{id}/ep_{number}/
        output_dir = os.path.join(settings.MEDIA_ROOT, f"anime_{episode.anime.id}", f"ep_{int(episode.number)}")
        os.makedirs(output_dir, exist_ok=True)

        # Generate Key
        key_content = os.urandom(16)
        key_uuid = uuid.uuid4()
        iv_hex = os.urandom(16).hex()

        # Save Key to DB
        video_key = VideoKey.objects.create(
            id=key_uuid,
            episode=episode,
            key_content=key_content,
            iv=bytes.fromhex(iv_hex)
        )

        # Prepare Key Info File for FFmpeg
        # Format:
        # Key URI (served by Django)
        # Path to key file (for FFmpeg encryption)
        # IV (Optional)

        key_file_path = os.path.join(output_dir, 'enc.key')
        with open(key_file_path, 'wb') as f:
            f.write(key_content)

        key_info_path = os.path.join(output_dir, 'key_info.txt')
        # Ensure this URI matches the view URL pattern
        key_uri = f"/api/key/{key_uuid}/"

        with open(key_info_path, 'w') as f:
            f.write(f"{key_uri}\n")
            f.write(f"{key_file_path}\n")
            f.write(f"{iv_hex}\n")

        # FFmpeg Command
        output_playlist = os.path.join(output_dir, 'master.m3u8')
        segment_filename = os.path.join(output_dir, 'segment_%03d.ts')

        cmd = [
            'ffmpeg',
            '-y', # Overwrite output
            '-i', source_path,
            '-c:v', 'libx265', # HEVC
            '-crf', '28',
            '-preset', 'medium',
            '-tag:v', 'hvc1', # Essential for Apple device compatibility
            '-c:a', 'aac',
            '-b:a', '128k',
            '-hls_time', '10',
            '-hls_key_info_file', key_info_path,
            '-hls_playlist_type', 'vod',
            '-hls_segment_filename', segment_filename,
            output_playlist
        ]

        print(f"Starting encoding for Episode {episode_id}...")
        subprocess.check_call(cmd)

        # Security Cleanup: Remove the key file from the public/static dir
        # The key is now in the DB and will be served via authenticated API
        if os.path.exists(key_file_path):
            os.remove(key_file_path)
        if os.path.exists(key_info_path):
            os.remove(key_info_path)

        # Update Episode
        # Store relative path for template usage
        rel_path = os.path.relpath(output_playlist, settings.MEDIA_ROOT)
        episode.hls_playlist = rel_path
        episode.is_processed = True
        episode.save()

        print(f"Encoding complete for Episode {episode_id}")

    except Episode.DoesNotExist:
        print(f"Episode {episode_id} not found")
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg failed: {e}")
    except Exception as e:
        print(f"Error in encode_episode: {e}")
