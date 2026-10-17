import type { Club, StandingRow } from '../api/client'

export function clubMapFromStandings(standings: StandingRow[]): Map<string, Club> {
  const map = new Map<string, Club>()
  for (const row of standings) {
    map.set(row.club.name, row.club)
    map.set(row.club.short_name, row.club)
  }
  return map
}

export function resolveCrestUrl(
  clubName: string,
  map: Map<string, Club>,
  fallback = '/crests/clubs/arsenal.png',
): string {
  const club = map.get(clubName)
  if (club?.crest_url) {
    return club.crest_url.startsWith('http') ? club.crest_url : club.crest_url
  }
  return fallback
}

export function playerStanding(
  standings: StandingRow[],
  playerClubId: number | null,
): StandingRow | undefined {
  if (!playerClubId) return undefined
  return standings.find((s) => s.club.id === playerClubId)
}
