import os
import sys
from pathlib import Path

SITE_ROOT = Path(__file__).resolve().parent
BACKEND = SITE_ROOT / "football-manager" / "backend"
ENV_FILE = SITE_ROOT / "site.env"

sys.path.insert(0, str(BACKEND))

if ENV_FILE.is_file():
    for raw in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
