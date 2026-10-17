# Club and competition crests (PNG)

Static assets served from `/crests/…` by the Vite dev server and production build. **Do not commit copyrighted Premier League or club logos** unless you have rights; add the PNG files locally or in your deployment pipeline.

## Folder layout

```
crests/
  clubs/<slug>.png          — 20 EPL clubs (see table below)
  competitions/premier-league.png — Premier League competition logo
```

Recommended size: **256×256 px** (UI scales to 24–64 px). Transparent background preferred.

## Required files

### Competition

| File | Slug |
|------|------|
| `competitions/premier-league.png` | `premier-league` |

### Clubs (Premier League 2026/27 seed)

| Slug (файл PNG) | Отображаемое имя (`Club.name`, RU) |
|-----------------|-------------------------------------|
| `arsenal` | Арсенал |
| `aston-villa` | Астон Вилла |
| `afc-bournemouth` | Борнмут |
| `brentford` | Брентфорд |
| `brighton` | Брайтон |
| `chelsea` | Челси |
| `crystal-palace` | Кристал Пэлас |
| `everton` | Эвертон |
| `fulham` | Фулхэм |
| `ipswich-town` | Ипсвич |
| `leicester-city` | Лестер |
| `liverpool` | Ливерпуль |
| `manchester-city` | Манчестер Сити |
| `manchester-united` | Манчестер Юнайтед |
| `newcastle-united` | Ньюкасл Юнайтед |
| `nottingham-forest` | Ноттингем Форест |
| `southampton` | Саутгемптон |
| `tottenham-hotspur` | Тоттенхэм |
| `west-ham-united` | Вест Хэм |
| `wolverhampton-wanderers` | Вулверхэмптон |

The Django `seed_league` command sets `Club.name` to the Russian display name, `Club.crest_url` to `/crests/clubs/<slug>.png` (English slug), and `Competition.logo_url` to `/crests/competitions/premier-league.png`.
