import { Popover } from 'antd'
import type { ReactNode } from 'react'
import type { Player } from '../api/client'
import { fifaStatsForPlayer } from '../utils/playerStats'
import {
  formatContractEnd,
  formatPlayerBirthDate,
  PlayerNationality,
} from './PlayerNationality'

export { fifaStatsForPlayer as FIFA_STAT_KEYS_FOR_PLAYER }

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
      <dl className="fm-player-stats-popover__bio">
        <div>
          <dt>Дата рождения</dt>
          <dd>{formatPlayerBirthDate(player.date_of_birth)}</dd>
        </div>
        <div>
          <dt>Гражданство</dt>
          <dd>
            <PlayerNationality countries={player.nationality_countries} size={16} />
            {!player.nationality_countries?.length ? '—' : null}
          </dd>
        </div>
        <div>
          <dt>Контракт до</dt>
          <dd>{formatContractEnd(player.contract_end_date)}</dd>
        </div>
      </dl>
      <ul className="fm-player-stats-popover__list">
        {fifaStatsForPlayer(player).map((stat) => (
          <li key={stat.key}>
            <span className="fm-player-stats-popover__abbr">{stat.abbr}</span>
            <span className="fm-player-stats-popover__label">{stat.label}</span>
            <span className="fm-player-stats-popover__val">{statVal(player, stat.key) ?? '—'}</span>
          </li>
        ))}
      </ul>
    </div>
  )

  return (
    <Popover content={content} trigger={['hover', 'focus']} placement="top" mouseEnterDelay={0.2}>
      <span className="fm-player-stats-trigger fm-player-stats-trigger--inline">{children}</span>
    </Popover>
  )
}

export function PlayerOverallWithStats({
  player,
  className,
}: {
  player: Player
  className?: string
}) {
  return (
    <PlayerStatsPopover player={player}>
      <span className={className} tabIndex={0} role="button" aria-label={`Рейтинг ${player.overall}, полная статистика`}>
        {player.overall}
      </span>
    </PlayerStatsPopover>
  )
}

export function PlayerMiniStatStrip({ player, compact }: { player: Player; compact?: boolean }) {
  const all = fifaStatsForPlayer(player)
  const keys = compact ? all.slice(0, 6) : all
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
