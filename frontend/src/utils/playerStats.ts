import type { Player } from '../api/client'

export type FifaStatKey = {
  key: keyof Player
  abbr: string
  label: string
}

const OUTFIELD_FIFA_STATS: FifaStatKey[] = [
  { key: 'pac', abbr: 'PAC', label: 'Скорость' },
  { key: 'sho', abbr: 'SHO', label: 'Удары' },
  { key: 'pas', abbr: 'PAS', label: 'Пасы' },
  { key: 'dri', abbr: 'DRI', label: 'Дриблинг' },
  { key: 'defending', abbr: 'DEF', label: 'Защита' },
  { key: 'phy', abbr: 'PHY', label: 'Физика' },
  { key: 'aerial', abbr: 'AER', label: 'Верховая борьба' },
  { key: 'mentality', abbr: 'MEN', label: 'Ментальность' },
  { key: 'injury_resistance', abbr: 'INJ', label: 'Стойкость к травмам' },
]

export type SkillRatingTier = 'low' | 'mid' | 'high'

/** 0–59 красный, 60–79 жёлтый, 80–100 зелёный */
export function skillRatingTier(value: number): SkillRatingTier {
  if (value <= 59) return 'low'
  if (value <= 79) return 'mid'
  return 'high'
}

/** FIFA GK face stats (stored in shared Player fields on the API). */
const GK_FIFA_STATS: FifaStatKey[] = [
  { key: 'defending', abbr: 'DIV', label: 'Игра на выходах' },
  { key: 'phy', abbr: 'HAN', label: 'Игра руками' },
  { key: 'pas', abbr: 'KIC', label: 'Удар с руки' },
  { key: 'dri', abbr: 'REF', label: 'Реакция' },
  { key: 'pac', abbr: 'SPE', label: 'Скорость' },
  { key: 'aerial', abbr: 'POS', label: 'Выбор позиции' },
  { key: 'mentality', abbr: 'MEN', label: 'Ментальность' },
  { key: 'injury_resistance', abbr: 'INJ', label: 'Устойчивость к травмам' },
]

export function isGoalkeeper(player: Player): boolean {
  return player.position === 'GK'
}

export function fifaStatsForPlayer(player: Player): FifaStatKey[] {
  return isGoalkeeper(player) ? GK_FIFA_STATS : OUTFIELD_FIFA_STATS
}
