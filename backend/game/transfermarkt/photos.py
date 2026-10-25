"""Download Transfermarkt player portraits into frontend static assets."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path

from django.conf import settings

from .client import fetch_portrait_bytes

PLAYERS_SUBDIR = "players"
_MIN_PORTRAIT_BYTES = 1500
_MAX_FETCH_ATTEMPTS = 3


def players_media_dir() -> Path:
    return settings.BASE_DIR.parent / "frontend" / "public" / PLAYERS_SUBDIR


def public_photo_path(transfermarkt_id: int) -> str:
    return f"/{PLAYERS_SUBDIR}/{transfermarkt_id}.jpg"


def portrait_url_matches_player(transfermarkt_id: int, portrait_url: str) -> bool:
    if transfermarkt_id <= 0 or not portrait_url:
        return False
    return f"/{transfermarkt_id}-" in portrait_url


def _looks_like_image(data: bytes) -> bool:
    if len(data) < _MIN_PORTRAIT_BYTES:
        return False
    if data[:3] == b"\xff\xd8\xff":
        return True
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return True
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return True
    return False


def _same_bytes_as_other_player(dest: Path, transfermarkt_id: int, data: bytes) -> bool:
    """Detect CDN/WAF glitches that store one player's image under another id."""
    digest = hashlib.md5(data).hexdigest()
    folder = dest.parent
    if not folder.is_dir():
        return False
    for other in folder.glob("*.jpg"):
        if other == dest:
            continue
        try:
            other_id = int(other.stem)
        except ValueError:
            continue
        if other_id == transfermarkt_id:
            continue
        if hashlib.md5(other.read_bytes()).hexdigest() == digest:
            return True
    return False


def save_portrait(
    transfermarkt_id: int,
    portrait_url: str,
    *,
    force: bool = False,
) -> str | None:
    """Fetch portrait to public/players/{id}.jpg; return web path or None on failure."""
    if not portrait_url_matches_player(transfermarkt_id, portrait_url):
        return None
    dest = players_media_dir() / f"{transfermarkt_id}.jpg"
    if dest.is_file() and not force:
        existing = dest.read_bytes()
        if _looks_like_image(existing) and not _same_bytes_as_other_player(
            dest, transfermarkt_id, existing
        ):
            return public_photo_path(transfermarkt_id)
        force = True

    last_error: RuntimeError | None = None
    for attempt in range(_MAX_FETCH_ATTEMPTS):
        try:
            data = fetch_portrait_bytes(portrait_url)
        except RuntimeError as exc:
            last_error = exc
            time.sleep(0.8 * (attempt + 1))
            continue
        if not _looks_like_image(data):
            time.sleep(0.8 * (attempt + 1))
            continue
        if _same_bytes_as_other_player(dest, transfermarkt_id, data):
            time.sleep(1.2 * (attempt + 1))
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return public_photo_path(transfermarkt_id)

    if last_error:
        return None
    return None
