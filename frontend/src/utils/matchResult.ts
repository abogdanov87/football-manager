import type { MatchResult } from '../api/client'
import type { Club } from '../api/client'

export type MatchOutcome = 'win' | 'draw' | 'loss'

export function outcomeFromGoals(us: number, them: number): MatchOutcome {
  if (us > them) return 'win'
  if (us < them) return 'loss'
  return 'draw'
}

/** Исход матча для клуба игрока; null если матч не его. */
export function playerMatchOutcome(
  match: Pick<MatchResult, 'home_club' | 'away_club' | 'home_short' | 'away_short' | 'home_score' | 'away_score'>,
  playerClubId: number | null,
  clubMap: Map<string, Club>,
): MatchOutcome | null {
  if (playerClubId == null) return null
  const home = clubMap.get(match.home_club) ?? clubMap.get(match.home_short)
  const away = clubMap.get(match.away_club) ?? clubMap.get(match.away_short)
  const isHome = home?.id === playerClubId
  const isAway = away?.id === playerClubId
  if (!isHome && !isAway) return null
  const us = isHome ? match.home_score : match.away_score
  const them = isHome ? match.away_score : match.home_score
  return outcomeFromGoals(us, them)
}
