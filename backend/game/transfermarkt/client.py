"""HTTP fetch helpers for Transfermarkt (rate-limited, polite User-Agent)."""

from __future__ import annotations

import time
import urllib.error
import urllib.request

DEFAULT_BASE_URL = "https://www.transfermarkt.co.uk"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 "
    "(FootballManagerEPL/1.0; +https://github.com/smicersiu/football-manager)"
)
MIN_INTERVAL_SEC = 1.2

_last_fetch_at: float = 0.0


def _throttle() -> None:
    global _last_fetch_at
    now = time.monotonic()
    wait = MIN_INTERVAL_SEC - (now - _last_fetch_at)
    if wait > 0:
        time.sleep(wait)
    _last_fetch_at = time.monotonic()


def fetch_url(url: str, *, timeout: float = 45.0) -> str:
    _throttle()
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "en-GB,en;q=0.9",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="replace")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} for {url}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error for {url}: {exc}") from exc


def competition_url(competition_code: str = "GB1", base: str = DEFAULT_BASE_URL) -> str:
    return f"{base}/premier-league/startseite/wettbewerb/{competition_code}"


def squad_url(club_slug: str, verein_id: int, season_id: int, base: str = DEFAULT_BASE_URL) -> str:
    return (
        f"{base}/{club_slug}/kader/verein/{verein_id}/saison_id/{season_id}/plus/1"
    )
