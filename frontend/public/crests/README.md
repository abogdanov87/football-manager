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

| Slug | Club name (official) |
|------|----------------------|
| `arsenal` | Arsenal |
| `aston-villa` | Aston Villa |
| `afc-bournemouth` | AFC Bournemouth |
| `brentford` | Brentford |
| `brighton` | Brighton & Hove Albion |
| `chelsea` | Chelsea |
| `crystal-palace` | Crystal Palace |
| `everton` | Everton |
| `fulham` | Fulham |
| `ipswich-town` | Ipswich Town |
| `leicester-city` | Leicester City |
| `liverpool` | Liverpool |
| `manchester-city` | Manchester City |
| `manchester-united` | Manchester United |
| `newcastle-united` | Newcastle United |
| `nottingham-forest` | Nottingham Forest |
| `southampton` | Southampton |
| `tottenham-hotspur` | Tottenham Hotspur |
| `west-ham-united` | West Ham United |
| `wolverhampton-wanderers` | Wolverhampton Wanderers |

The Django `seed_league` command sets `Club.crest_url` to `/crests/clubs/<slug>.png` and `Competition.logo_url` to `/crests/competitions/premier-league.png`.
