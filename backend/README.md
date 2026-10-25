# Football Manager — backend (Django)

## Локальный запуск

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_league
python manage.py import_transfermarkt_epl   # Премьер-лига 2026/27, 20 клубов (русские `name`, slug в crest — см. seed_league.py)
python manage.py runserver 8001
```

API: `http://127.0.0.1:8001/api/`

После `seed_league` войдите через фронтенд: запросите OTP на email (в dev код печатается в консоль `runserver`), выберите свободный клуб.

## Авторизация (email OTP)

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `EMAIL_BACKEND` | `django.core.mail.backends.console.EmailBackend` | В dev письма в консоль; для SMTP укажите `django.core.mail.backends.smtp.EmailBackend` |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | — | Параметры SMTP (на Reg.ru: `mail.hosting.reg.ru:587`) |
| `DEFAULT_FROM_EMAIL` | `noreply@footballmanager.local` | Отправитель OTP |
| `DJANGO_SECRET_KEY` | (dev placeholder) | Обязательно сменить в production |

Для локальной отладки почты удобен [Mailpit](https://github.com/axllent/mailpit): SMTP на `1025`, веб-интерфейс на `8025`, тогда `EMAIL_BACKEND=smtp` и `EMAIL_HOST=localhost`.

Сессионный токен после входа действует **7 дней**; OTP в письме — **10 минут**.

## Рейтинги FC 27 (fcratings.com)

Обновить PAC/SHO/PAS/DRI/DEF/PHY и OVR всех игроков по [FC Ratings](https://www.fcratings.com/):

```bash
# PAC/SHO/PAS/DRI/DEF/PHY + OVR с карточки игрока (~10 мин, ~1 запрос/с)
python manage.py sync_fcratings_stats

# Только OVR из индекса fcratings (быстро; лица — оценка по позиции)
python manage.py sync_fcratings_stats --index-only
```

Сопоставление по `transfermarkt_slug` (slug в URL fcratings). Кэш индекса: `game/fixtures/fcratings/search-index.json` (скачивается при первом запуске).

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
