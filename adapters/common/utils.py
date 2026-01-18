import os
import shutil
import subprocess
from typing import Optional, Dict, Any
from yt_dlp import YoutubeDL

BIN_PATH = os.path.join(os.getcwd(), "bin")

def get_ydl_opts() -> Dict[str, Any]:
    return {
        'quiet': True,
        'no_warnings': True,
        # We don't want flat extraction if we want formats, but for initial check maybe?
        # The adapter code calls download_with_info_file later, so it expects full info eventually.
        # But extract_video_info is used to populate _info.
        # Let's use default safe options.
        'format': 'best',
        'skip_download': True,
    }

def extract_video_info(url: str, opts: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    if opts is None:
        opts = get_ydl_opts()
    try:
        with YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)
    except Exception as e:
        print(f"[utils] Error extracting video info for {url}: {e}")
        return None

def get_video_resolution_mpv(url: str) -> int:
    """
    Try to get video resolution using MPV (if available).
    Returns height as int (e.g. 1080), or 0 if failed.
    """
    mpv_path = shutil.which("mpv")
    if not mpv_path:
        return 0

    # Using mpv to get properties is tricky without playing.
    # For a web server context, we probably shouldn't spawn mpv.
    # Returing 0 will force the adapter to look at other metadata or default.
    return 0
