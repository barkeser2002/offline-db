from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Any, Dict, Callable
import json
from tempfile import NamedTemporaryFile
from os.path import join
import subprocess as sp
import re
import unicodedata

from yt_dlp import YoutubeDL

from .animecix import _video_streams
# Removed internal project-specific imports that don't exist here

def _slugify(text: str) -> str:
    """Basit ve güvenli bir slug üretici: ASCII'ye indirger,
    boşlukları '-' yapar, gereksizleri temizler."""
    if not text:
        return ""
    # Unicode -> ASCII transliterasyon
    t = unicodedata.normalize("NFKD", str(text))
    t = t.encode("ascii", "ignore").decode("ascii")
    t = t.lower()
    t = re.sub(r"\s+", "-", t)
    t = re.sub(r"[^a-z0-9\-]", "-", t)
    t = re.sub(r"-+", "-", t).strip("-")
    return t[:80]


@dataclass
class AdapterAnime:
    slug: str
    title: str

    def __post_init__(self):
        # Eğer slug sayı/ID ise ya da boşsa, başlıktan güvenli bir slug üret.
        raw = (self.slug or "").strip()
        if not raw or raw.isdigit() or not re.search(r"[a-zA-Z]", raw):
            self.slug = _slugify(self.title)


class AdapterVideo:
    """TürkAnime Video arayüzüne minimum uyumlu basit video nesnesi."""

    def __init__(
        self,
        bolum: 'AdapterBolum',
        url: Optional[str],
        label: Optional[str] = None,
        player: str = "ANIMECIX",
    ):
        self.bolum = bolum
        self._url = url or ""
        self.label = label
        self.player = player or "ANIMECIX"
        self._info: Optional[Dict[str, Any]] = None
        self.is_supported = True
        self._is_working: Optional[bool] = None
        self._resolution: Optional[int] = None
        self.ydl_opts = {} # Simplified

    @property
    def url(self) -> str:
        return self._url

    @property
    def info(self) -> Optional[Dict[str, Any]]:
        # Simplified for local project
        return {}

    @property
    def is_working(self) -> bool:
        return True # Simplified

    def indir(self, callback=None, output=""):
        pass # Simplified

    def get(self, key, default=None):
        """Dictionary-like get method for compatibility."""
        if key == 'url':
            return self.url
        elif key == 'label':
            return self.label
        elif key == 'player':
            return self.player
        return default


class AdapterBolum:
    def __init__(
        self,
        url: Optional[str],
        title: str,
        anime: AdapterAnime,
        stream_provider: Optional[Callable[[str], List[Dict[str, str]]]] = None,
        player_name: str = "ANIMECIX",
    ):
        self.url = url
        self._title = title
        self.anime = anime
        self._stream_provider = stream_provider
        self._player_name = player_name or "ANIMECIX"
        self.slug = _slugify(f"{anime.title}-{title}" if anime else title)

    @property
    def title(self):
        return self._title

    @property
    def fansubs(self):
        return []

    def best_video(
        self,
        by_res=True,
        by_fansub=None,
        default_res=600,
        callback=lambda x: None,
        early_subset: int = 8
    ):
        # Simplified for local project
        return None
