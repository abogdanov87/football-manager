# Football Manager Online (v0.1)

Браузерная менеджерская игра: **Django REST API** + **React (Vite) + Ant Design**.

## Стек

| Часть | Технологии |
|-------|------------|
| Backend | Django 6, DRF, SQLite (dev) / MySQL (prod) |
| Frontend | Vite, React, TypeScript, Ant Design 6 (тёмная тема FM26) |
| Симуляция тура | **Cron** → `python manage.py simulate_matchday` (раз в день) |

Игрок между турами настраивает состав и схему; матчи лиги считаются автоматически по расписанию.

## Быстрый старт

### Backend (порт 8001)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_league
python manage.py import_transfermarkt_epl   # реальные составы АПЛ (Transfermarkt)
python manage.py runserver 8001
```

Составы и статы: см. [docs/transfermarkt-import.md](docs/transfermarkt-import.md). Если live-скрапинг недоступен на хостинге, используйте `--fixture-dir game/fixtures/transfermarkt` (нужны HTML-файлы по клубам).

### Frontend (порт 43123)

```bash
cd frontend
npm install
npm run dev
```

Откройте http://127.0.0.1:43123 — прокси `/api` → backend.

### Cron (production)

```cron
0 12 * * * cd /path/to/backend && .venv/bin/python manage.py simulate_matchday >> /var/log/fm-sim.log 2>&1
```

Время настраивается через `LEAGUE_SIMULATION_HOUR` / `LEAGUE_SIMULATION_MINUTE` и `DJANGO_TIME_ZONE` (см. `backend/README.md`).

## API (кратко)

- `GET /api/season/current/` — сезон, таблица, следующий матч-день, последние результаты
- `GET /api/standings/`
- `GET /api/clubs/:id/squad/`, `PUT /api/clubs/:id/tactics/`
- `POST /api/matchday/simulate/` — только dev (`ALLOW_MANUAL_MATCHDAY_SIMULATION`)
