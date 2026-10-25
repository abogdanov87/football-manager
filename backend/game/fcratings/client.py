"""HTTP helpers for fcratings.com (polite, rate-limited)."""

from __future__ import annotations

import subprocess
import time
import urllib.error
import urllib.request

BASE_URL = "https://www.fcratings.com"
SEARCH_INDEX_URL = (
    f"{BASE_URL}/wp-content/plugins/fc-instant-search/assets/search-index.json?v=1"
)
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
MIN_INTERVAL_SEC = 1.0

_last_fetch_at: float = 0.0


def _throttle() -> None:
    global _last_fetch_at
    now = time.monotonic()
    wait = MIN_INTERVAL_SEC - (now - _last_fetch_at)
    if wait > 0:
        time.sleep(wait)
    _last_fetch_at = time.monotonic()


def _fetch_via_curl(url: str, *, timeout: float) -> str:
    result = subprocess.run(
        [
            "curl",
            "-fsSL",
            "--max-time",
            str(int(timeout)),
            "-A",
            USER_AGENT,
            "-H",
            f"Referer: {BASE_URL}/",
            "-H",
            "Accept-Language: en-GB,en;q=0.9",
            url,
        ],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        err = (result.stderr or b"").decode("utf-8", errors="replace").strip()
        raise urllib.error.URLError(err or f"curl failed ({result.returncode})")
    return result.stdout.decode("utf-8", errors="replace")


def fetch_url(url: str, *, timeout: float = 45.0) -> str:
    _throttle()
    return _fetch_via_curl(url, timeout=timeout)
