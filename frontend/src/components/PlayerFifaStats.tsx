import { Popover } from 'antd'
import type { ReactNode } from 'react'
import type { Player } from '../api/client'

export const FIFA_STAT_KEYS = [
  { key: 'pac' as const, abbr: 'PAC', label: 'Скорость' },
  { key: 'sho' as const, abbr: 'SHO', label: 'Удар' },
  { key: 'pas' as const, abbr: 'PAS', label: 'Пас' },
  { key: 'dri' as const, abbr: 'DRI', label: 'Дриблинг' },
  { key: 'defending' as const, abbr: 'DEF', label: 'Защита' },
  { key: 'phy' as const, abbr: 'PHY', label: 'Физика' },
  { key: 'aerial' as const, abbr: 'AER', label: 'Верховая борьба' },
  { key: 'mentality' as const, abbr: 'MEN', label: 'Ментальность' },
  { key: 'injury_resistance' as const, abbr: 'INJ', label: 'Устойчивость к травмам' },
]

export function formatMarketValueUsd(value?: number | null): string {
  if (value == null || value <= 0) return '—'
  if (value >= 1_000_000) {
    const m = value / 1_000_000
    const rounded = m >= 100 ? Math.round(m) : Math.round(m * 10) / 10
    return `$${rounded}M`
  }
  if (value >= 1_000) return `$${Math.round(value / 1_000)}K`
  return `$${value}`
}

function statVal(player: Player, key: keyof Player): number | null {
  const v = player[key]
  return typeof v === 'number' ? v : null
}

export function PlayerStatsPopover({
  player,
  children,
}: {
  player: Player
  children: ReactNode
}) {
  const content = (
    <div className="fm-player-stats-popover">
      <div className="fm-player-stats-popover__mv">
        Рыночная стоимость: <strong>{formatMarketValueUsd(player.market_value_usd)}</strong>
      </div>
      <ul className="fm-player-stats-popover__list">
        {FIFA_STAT_KEYS.map(({ key, abbr, label }) => (
          <li key={key}>
            <span className="fm-player-stats-popover__abbr">{abbr}</span>
            <span className="fm-player-stats-popover__label">{label}</span>
            <span className="fm-player-stats-popover__val">{statVal(player, key) ?? '—'}</span>
          </li>
        ))}
      </ul>
    </div>
  )

  return (
    <Popover content={content} trigger={['hover', 'focus']} placement="top" mouseEnterDelay={0.2}>
      <span className="fm-player-stats-trigger">{children}</span>
    </Popover>
  )
}

export function PlayerMiniStatStrip({ player, compact }: { player: Player; compact?: boolean }) {
  const keys = compact ? FIFA_STAT_KEYS.slice(0, 6) : FIFA_STAT_KEYS
  return (
    <div className={`fm-mini-stats${compact ? ' fm-mini-stats--compact' : ''}`} aria-hidden>
      {keys.map(({ key, abbr }) => (
        <span key={key} className="fm-mini-stats__cell" title={abbr}>
          <em>{abbr}</em>
          {statVal(player, key) ?? '—'}
        </span>
      ))}
    </div>
  )
}
