const API_BASE = import.meta.env.VITE_API_URL ?? ''

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    ...init,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? res.statusText)
  }
  return res.json() as Promise<T>
}

export type Club = {
  id: number
  name: string
  short_name: string
  crest_url: string
  formation: string
  lineup_player_ids: number[]
  budget: number
}

export type Competition = {
  id: number
  name: string
  slug: string
  logo_url: string
}

export type Player = {
  id: number
  name: string
  position: string
  age: number
  overall: number
}

export type StandingRow = {
  club: Club
  played: number
  won: number
  drawn: number
  lost: number
  goals_for: number
  goals_against: number
  goal_difference: number
  points: number
}

export type MatchResult = {
  id: number
  matchday: number
  home_club: string
  away_club: string
  home_short: string
  away_short: string
  home_score: number
  away_score: number
  events: string[]
}

export type SeasonOverview = {
  id: number
  name: string
  competition: Competition | null
  current_matchday: number
  total_matchdays: number
  next_simulation_at: string | null
  last_simulation_at: string | null
  is_complete: boolean
  standings: StandingRow[]
  player_club_id: number | null
  recent_matches: MatchResult[]
  upcoming_fixtures: Array<{
    id: number
    matchday: number
    home_club: Club
    away_club: Club
    is_played: boolean
  }>
  manual_simulation_allowed: boolean
}

export const api = {
  getSeason: () => request<SeasonOverview>('/api/season/current/'),
  getStandings: () => request<StandingRow[]>('/api/standings/'),
  getSquad: (clubId: number) =>
    request<{ club: Club; players: Player[] }>(`/api/clubs/${clubId}/squad/`),
  updateTactics: (clubId: number, body: { formation: string; lineup_player_ids: number[] }) =>
    request<Club>(`/api/clubs/${clubId}/tactics/`, {
      method: 'PUT',
      body: JSON.stringify(body),
    }),
  simulateMatchdayDev: (force = false) =>
    request<{ status: string; message: string; season: SeasonOverview }>(
      `/api/matchday/simulate/${force ? '?force=1' : ''}`,
      { method: 'POST', body: '{}' },
    ),
}
