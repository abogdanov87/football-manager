#!/bin/bash
SITE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SITE_DIR"
mkdir -p logs

if [ -f gunicorn.pid ] && kill -0 "$(cat gunicorn.pid)" 2>/dev/null; then
  exit 0
fi

rm -f gunicorn.pid

set -a
# shellcheck disable=SC1090
source "$SITE_DIR/site.env"
set +a

# shellcheck disable=SC1091
source "$SITE_DIR/venv/bin/activate"
cd "$SITE_DIR/football-manager/backend"

gunicorn config.wsgi:application \
  --bind 127.0.0.1:34568 \
  --daemon \
  --pid "$SITE_DIR/gunicorn.pid" \
  --access-logfile "$SITE_DIR/logs/gunicorn-access.log" \
  --error-logfile "$SITE_DIR/logs/gunicorn-error.log" \
  --workers 1 \
  --threads 2 \
  --timeout 120
