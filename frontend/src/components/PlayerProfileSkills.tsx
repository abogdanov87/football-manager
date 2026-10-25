import type { Player } from '../api/client'
import { fifaStatsForPlayer, skillRatingTier } from '../utils/playerStats'

function statValue(player: Player, key: keyof Player): number {
  const v = player[key]
  return typeof v === 'number' ? v : 0
}

export function PlayerProfileSkills({ player }: { player: Player }) {
  const stats = fifaStatsForPlayer(player)

  return (
    <div className="fm-player-profile__skill-grid">
      {stats.map((stat) => {
        const value = statValue(player, stat.key)
        const tier = skillRatingTier(value)
        return (
          <div key={stat.key} className="fm-player-profile__skill-cell">
            <span className="fm-player-profile__skill-label">{stat.label}</span>
            <span className={`fm-player-profile__skill-value fm-player-profile__skill-value--${tier}`}>
              {value}
            </span>
          </div>
        )
      })}
    </div>
  )
}
