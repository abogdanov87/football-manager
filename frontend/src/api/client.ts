import { getAuthToken, setAuthToken } from '../auth/token'

const API_BASE = import.meta.env.VITE_API_URL ?? ''

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getAuthToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init?.headers as Record<string, string> | undefined),
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
  })
  if (res.status === 401 && token) {
    setAuthToken(null)
    if (!window.location.pathname.startsWith('/login')) {
      window.location.assign('/login')
    }
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? res.statusText)
  }
  if (res.status === 204) {
    return undefined as T
  }
  return res.json() as Promise<T>
}

export type AuthMe = {
  id: number
  email: string
  club_id: number | null
}

export type OtpVerifyResponse = {
  token: string
  expires_at: string
  user: { id: number; email: string }
  club_id: number | null
}

export type Club = {
  id: number
  name: string
  short_name: string
  crest_url: string
  formation: string
  lineup_player_ids: number[]
  budget: number
  captain_player_id?: number | null
  penalty_taker_player_id?: number | null
  free_kick_taker_player_id?: number | null
}

export type Competition = {
  id: number
  name: string
  slug: string
  logo_url: string
}

export type NationalityCountry = {
  name: string
  flag_url: string
}

export type FavoritePosition = {
  position_code: string
  minutes: number
  percent: number
}

export type PlayerContractInfo = {
  contract_end_date: string | null
  years_remaining: number
  months_remaining: number
  renewal_status: string
  weekly_wage_usd: number
  yearly_wage_usd: number
}

export type PlayerCareerRow = {
  club_name: string
  from_date: string | null
  to_date: string | null
  source: string
}

export type PlayerSeasonStatRow = {
  season_name: string
  appearances: number
  minutes: number
  goals: number
  assists: number
  yellow_cards: number
  red_cards: number
  injury_days: number
}

export type PlayerRoles = {
  is_captain: boolean
  is_penalty_taker: boolean
  is_free_kick_taker: boolean
}

export type PlayerDetail = Player & {
  club: Club
  favorite_positions: FavoritePosition[]
  contract: PlayerContractInfo
  career: PlayerCareerRow[]
  season_stats: PlayerSeasonStatRow[]
  roles: PlayerRoles
  can_edit_roles: boolean
}

export type Player = {
  id: number
  name: string
  position: string
  age: number
  date_of_birth?: string | null
  nationality_countries?: NationalityCountry[]
  contract_end_date?: string | null
  overall: number
  form?: number
  transfermarkt_id?: number | null
  transfermarkt_slug?: string
  photo_url?: string
  tm_position?: string
  market_value_usd?: number
  pac?: number
  sho?: number
  pas?: number
  dri?: number
  defending?: number
  phy?: number
  aerial?: number
  mentality?: number
  injury_resistance?: number
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
  requestOtp: (email: string) =>
    request<{ detail: string }>('/api/auth/otp/request/', {
      method: 'POST',
      body: JSON.stringify({ email }),
    }),
  verifyOtp: (email: string, code: string) =>
    request<OtpVerifyResponse>('/api/auth/otp/verify/', {
      method: 'POST',
      body: JSON.stringify({ email, code }),
    }),
  getAuthMe: () => request<AuthMe>('/api/auth/me/'),
  logout: () => request<void>('/api/auth/logout/', { method: 'POST', body: '{}' }),
  logoutAll: () => request<void>('/api/auth/logout-all/', { method: 'POST', body: '{}' }),
  getAvailableClubs: () => request<Club[]>('/api/clubs/available/'),
  claimClub: (clubId: number) =>
    request<Club>('/api/clubs/claim/', {
      method: 'POST',
      body: JSON.stringify({ club_id: clubId }),
    }),
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
  getPlayerDetail: (playerId: number) => request<PlayerDetail>(`/api/players/${playerId}/`),
  updateClubPlayerRoles: (
    clubId: number,
    body: Partial<{
      captain_player_id: number | null
      penalty_taker_player_id: number | null
      free_kick_taker_player_id: number | null
    }>,
  ) =>
    request<Club>(`/api/clubs/${clubId}/player-roles/`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),
}
