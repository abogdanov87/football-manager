"""HTTP fetch helpers for Transfermarkt (rate-limited, polite User-Agent)."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

DEFAULT_BASE_URL = "https://www.transfermarkt.world"
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


def _request(url: str, *, timeout: float = 45.0) -> urllib.request.Request:
    return urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "en-GB,en;q=0.9",
        },
    )


def fetch_url(url: str, *, timeout: float = 45.0) -> str:
    _throttle()
    req = _request(url, timeout=timeout)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            body = resp.read().decode(charset, errors="replace")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} for {url}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error for {url}: {exc}") from exc
    if _looks_like_waf_challenge(body):
        raise RuntimeError(f"blocked by WAF for {url}")
    return body


def _looks_like_waf_challenge(body: str) -> bool:
    if len(body) < 800:
        return "awsWafCookieDomainList" in body or "challenge-container" in body
    return False


def fetch_json(
    url: str, *, referer: str = "", timeout: float = 45.0
) -> dict:
    _throttle()
    req = _request(url, timeout=timeout)
    req.add_header("Accept", "application/json, text/plain, */*")
    if referer:
        req.add_header("Referer", referer)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            raw = resp.read().decode(charset, errors="replace")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} for {url}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error for {url}: {exc}") from exc
    if not raw.strip():
        raise RuntimeError(f"empty response for {url}")
    if _looks_like_waf_challenge(raw):
        raise RuntimeError(f"blocked by WAF for {url}")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON from {url}") from exc


def fetch_bytes(url: str, *, timeout: float = 45.0) -> bytes:
    _throttle()
    req = _request(url, timeout=timeout)
    req.add_header("Accept", "image/avif,image/webp,image/apng,image/*,*/*;q=0.8")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} for {url}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error for {url}: {exc}") from exc


def fetch_portrait_bytes(url: str, *, timeout: float = 45.0) -> bytes:
    """TM CDN serves tiny WebP placeholders unless Referer + JPEG-friendly Accept."""
    _throttle()
    req = _request(url, timeout=timeout)
    req.add_header("Accept", "image/jpeg,image/png,image/*;q=0.9,*/*;q=0.5")
    req.add_header("Referer", f"{DEFAULT_BASE_URL}/")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
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


def club_start_url(club_slug: str, verein_id: int, base: str = DEFAULT_BASE_URL) -> str:
    return f"{base}/{club_slug}/startseite/verein/{verein_id}"


def final_formation_url(verein_id: int, base: str = DEFAULT_BASE_URL) -> str:
    return f"{base}/ceapi/FinalFormation/ClubId/{verein_id}"


def player_profile_url(
    slug: str, transfermarkt_id: int, base: str = DEFAULT_BASE_URL
) -> str:
    return f"{base}/{slug}/profil/spieler/{transfermarkt_id}"
