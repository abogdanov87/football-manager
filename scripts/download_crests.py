#!/usr/bin/env python3
"""Download EPL club crests from Wikipedia/Wikimedia Commons as ~256px PNG."""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLUBS_DIR = ROOT / "frontend/public/crests/clubs"
COMP_DIR = ROOT / "frontend/public/crests/competitions"
SOURCES = ROOT / "frontend/public/crests/SOURCES.md"
WIDTH = 256

# slug -> (wiki host prefix, candidate File: names without "File:" prefix)
CLUBS: dict[str, list[tuple[str, str]]] = {
    "arsenal": [("en", "Arsenal_FC.svg")],
    "aston-villa": [
        ("en", "Aston_Villa_FC_new_crest.svg"),
        ("en", "Aston_Villa_FC_crest.svg"),
    ],
    "afc-bournemouth": [
        ("en", "AFC_Bournemouth_(2013).svg"),
        ("en", "AFC_Bournemouth.svg"),
    ],
    "brentford": [("en", "Brentford_FC_crest.svg")],
    "brighton": [
        ("en", "Brighton_and_Hove_Albion_FC_crest.svg"),
        ("en", "Brighton_&_Hove_Albion_FC_crest.svg"),
    ],
    "chelsea": [("en", "Chelsea_FC.svg")],
    "crystal-palace": [
        ("en", "Crystal Palace FC logo (2022).svg"),
        ("en", "Crystal_Palace_FC_crest.svg"),
    ],
    "everton": [("en", "Everton_FC_logo.svg")],
    "fulham": [("en", "Fulham_FC_(shield).svg"), ("en", "Fulham_FC_crest.svg")],
    "ipswich-town": [("en", "Ipswich_Town.svg"), ("commons", "Ipswich_Town_FC.svg")],
    "leicester-city": [("en", "Leicester_City_crest.svg")],
    "liverpool": [("en", "Liverpool_FC.svg")],
    "manchester-city": [("en", "Manchester_City_FC_badge.svg")],
    "manchester-united": [("en", "Manchester_United_FC_crest.svg")],
    "newcastle-united": [("en", "Newcastle_United_Logo.svg")],
    "nottingham-forest": [("en", "Nottingham_Forest_F.C._logo.svg")],
    "southampton": [
        ("en", "FC_Southampton.svg"),
        ("en", "Southampton_FC_logo.svg"),
        ("en", "Saints_logo_2010.PNG"),
    ],
    "tottenham-hotspur": [("en", "Tottenham_Hotspur.svg")],
    "west-ham-united": [("en", "West_Ham_United_FC_logo.svg")],
    "wolverhampton-wanderers": [("en", "Wolverhampton_Wanderers.svg")],
    "sunderland": [
        ("en", "Logo Sunderland.svg"),
        ("en", "SAFC1972-97crest.svg"),
        ("en", "Sunderland AFC cat badge.jpg"),
    ],
    "leeds-united": [("en", "Leeds_United_F.C._logo.svg")],
    "coventry-city": [
        ("en", "Coventry_City_FC_crest.svg"),
        ("en", "Covcfclogo.png"),
    ],
    "hull-city": [("en", "Hull_City_A.F.C._logo.svg")],
}

COMPETITIONS: dict[str, list[tuple[str, str]]] = {
    "premier-league": [
        ("en", "Premier_League_Logo.svg"),
        ("commons", "Premier League Logo.svg"),
        ("commons", "Premier_League_Logo.svg"),
    ],
}


def wiki_api_base(wiki: str) -> str:
    if wiki == "commons":
        return "https://commons.wikimedia.org/w/api.php"
    return f"https://{wiki}.wikipedia.org/w/api.php"


def file_page_url(wiki: str, filename: str) -> str:
    if wiki == "commons":
        return f"https://commons.wikimedia.org/wiki/File:{urllib.parse.quote(filename.replace(' ', '_'))}"
    return f"https://en.wikipedia.org/wiki/File:{urllib.parse.quote(filename.replace(' ', '_'))}"


def fetch_thumb(wiki: str, filename: str, width: int) -> tuple[str, str] | None:
    """Return (thumb_download_url, file_page_url) or None."""
    params = urllib.parse.urlencode(
        {
            "action": "query",
            "titles": f"File:{filename}",
            "prop": "imageinfo",
            "iiprop": "url",
            "iiurlwidth": str(width),
            "format": "json",
        }
    )
    url = f"{wiki_api_base(wiki)}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "FootballManagerCrestBot/1.0 (educational project)"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError):
        return None

    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        if "missing" in page:
            continue
        infos = page.get("imageinfo") or []
        if not infos:
            continue
        info = infos[0]
        thumb = info.get("thumburl") or info.get("url")
        if thumb:
            return thumb, file_page_url(wiki, filename)
    return None


def download_url(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "FootballManagerCrestBot/1.0 (educational project)"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        dest.write_bytes(resp.read())


def resolve_and_download(
    slug: str,
    candidates: list[tuple[str, str]],
    dest: Path,
) -> tuple[bool, str]:
    for wiki, filename in candidates:
        time.sleep(0.4)
        resolved = fetch_thumb(wiki, filename, WIDTH)
        if not resolved:
            continue
        thumb_url, page_url = resolved
        try:
            download_url(thumb_url, dest)
            if dest.stat().st_size < 500:
                continue
            return True, page_url
        except urllib.error.URLError:
            continue
    return False, f"FAILED — tried: {', '.join(f'{w}:{f}' for w, f in candidates)}"


def main() -> int:
    CLUBS_DIR.mkdir(parents=True, exist_ok=True)
    COMP_DIR.mkdir(parents=True, exist_ok=True)

    lines: list[str] = [
        "# Crest image sources (Wikipedia / Wikimedia Commons)",
        "",
        "One line per file. Thumbnails ~256px wide from Wikimedia API.",
        "",
    ]

    ok = 0
    failed: list[str] = []

    for slug, candidates in CLUBS.items():
        dest = CLUBS_DIR / f"{slug}.png"
        success, source = resolve_and_download(slug, candidates, dest)
        rel = f"clubs/{slug}.png"
        lines.append(f"- `{rel}` — {source}")
        if success:
            ok += 1
            print(f"OK {rel} ({dest.stat().st_size} bytes)")
        else:
            failed.append(slug)
            print(f"FAIL {rel}: {source}", file=sys.stderr)

    for slug, candidates in COMPETITIONS.items():
        dest = COMP_DIR / f"{slug}.png"
        success, source = resolve_and_download(slug, candidates, dest)
        rel = f"competitions/{slug}.png"
        lines.append(f"- `{rel}` — {source}")
        if success:
            ok += 1
            print(f"OK {rel} ({dest.stat().st_size} bytes)")
        else:
            failed.append(slug)
            print(f"FAIL {rel}: {source}", file=sys.stderr)

    SOURCES.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nDownloaded {ok}/{len(CLUBS) + len(COMPETITIONS)}")
    if failed:
        print("Missing:", ", ".join(failed), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
