#!/bin/bash
# Run on Reg.ru hosting after the repo exists at $SITE_ROOT/football-manager
set -euo pipefail

SITE_ROOT="/var/www/u2662691/data/www/qolibri.ru"
REPO="$SITE_ROOT/football-manager"
PY="/opt/python/python-3.12/bin/python3"
VENV="$SITE_ROOT/venv"

cd "$REPO"
git fetch origin main
git reset --hard origin/main

if [[ ! -x "$VENV/bin/python" ]] || ! "$VENV/bin/python" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)' 2>/dev/null; then
  rm -rf "$VENV"
  "$PY" -m venv "$VENV"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"
pip install -q --upgrade pip
pip install -q -r backend/requirements.txt

cd "$SITE_ROOT/football-manager/backend"
set -a
# shellcheck disable=SC1090
source "$SITE_ROOT/qolibri.env"
set +a
python manage.py migrate --noinput
python manage.py collectstatic --noinput

mkdir -p "$SITE_ROOT/tmp"
touch "$SITE_ROOT/tmp/restart.txt"

echo "Backend updated at $(date -Iseconds)"
