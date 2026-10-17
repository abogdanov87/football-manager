# Football Manager — backend (Django)

## Локальный запуск

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_league   # Премьер-лига 2026/27, 20 клубов (русские `name`, slug в crest — см. seed_league.py)
python manage.py runserver 8001
```

API: `http://127.0.0.1:8001/api/`

## Ежедневная симуляция тура (cron)

Тур лиги симулируется **по расписанию**, не кнопкой игрока. Игрок меняет тактику между турами.

Настройки в `config/settings.py` / переменных окружения:

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `LEAGUE_SIMULATION_HOUR` | `12` | Час запуска (в `DJANGO_TIME_ZONE`) |
| `LEAGUE_SIMULATION_MINUTE` | `0` | Минута |
| `DJANGO_TIME_ZONE` | `Europe/Moscow` | Часовой пояс слота |

Пример cron (каждый день в 12:00 по времени сервера в той же зоне, что Django):

```cron
0 12 * * * cd /path/to/backend && .venv/bin/python manage.py simulate_matchday >> /var/log/fm-sim.log 2>&1
```

Команда **идемпотентна**: повторный запуск в тот же календарный день завершится со статусом `skipped`, пока не передан `--force` (для отладки).

Ручной запуск в dev (если `ALLOW_MANUAL_MATCHDAY_SIMULATION=true`):

```bash
python manage.py simulate_matchday
python manage.py simulate_matchday --force
```

Или `POST /api/matchday/simulate/` (в production — staff или отключено).

## MySQL (production)

```bash
export DB_ENGINE=mysql
export DB_NAME=football_manager
export DB_USER=...
export DB_PASSWORD=...
export DB_HOST=localhost
python manage.py migrate
```
