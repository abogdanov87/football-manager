#!/bin/bash
set -euo pipefail

SITE_ROOT="/var/www/u3540963/data/www/mr-manager.ru"
REPO="$SITE_ROOT/football-manager"
PY="/opt/python/python-3.12/bin/python3"
VENV="$SITE_ROOT/venv"

cd "$REPO"
git fetch origin main
git reset --hard origin/main

recreate_venv() {
  rm -rf "$VENV"
  "$PY" -m venv "$VENV"
}

if [[ ! -x "$VENV/bin/python" ]] || ! "$VENV/bin/python" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)' 2>/dev/null; then
  recreate_venv
elif ! "$VENV/bin/python" -c 'import django; raise SystemExit(0 if django.VERSION[:2]==(4,2) else 1)' 2>/dev/null; then
  recreate_venv
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"
pip install -q --upgrade pip
pip install -q -r backend/requirements-hosting.txt

cd "$SITE_ROOT/football-manager/backend"
set -a
# shellcheck disable=SC1090
source "$SITE_ROOT/site.env"
set +a
python manage.py migrate --noinput
python manage.py collectstatic --noinput

if ! python manage.py shell -c "from game.models import Season; import sys; sys.exit(0 if Season.objects.exists() else 1)"; then
  python manage.py seed_league
  python manage.py import_transfermarkt_epl --fixture-dir game/fixtures/transfermarkt || true
fi

bash "$SITE_ROOT/start_gunicorn.sh"

mkdir -p "$SITE_ROOT/tmp"
touch "$SITE_ROOT/tmp/restart.txt"

echo "Backend updated at $(date -Iseconds)"
