"""HTTP helpers for sports.ru (polite, stdlib)."""

from __future__ import annotations

import time
import urllib.error
import urllib.request

BASE_URL = "https://www.sports.ru"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 "
    "(FootballManager/1.0)"
)
MIN_INTERVAL_SEC = 0.8

_last_fetch_at: float = 0.0


def _throttle() -> None:
    global _last_fetch_at
    now = time.monotonic()
    wait = MIN_INTERVAL_SEC - (now - _last_fetch_at)
    if wait > 0:
        time.sleep(wait)
    _last_fetch_at = time.monotonic()


def club_squad_url(club_slug: str) -> str:
    return f"{BASE_URL}/football/club/{club_slug}/squad/"


def fetch_url(url: str, *, timeout: float = 45.0) -> str:
    _throttle()
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept-Language": "ru-RU,ru;q=0.9"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="replace")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} for {url}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error for {url}: {exc}") from exc
