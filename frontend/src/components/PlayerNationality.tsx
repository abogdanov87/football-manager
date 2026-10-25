import type { NationalityCountry, Player } from '../api/client'
import { formatCountryNameRu } from '../utils/playerLabels'

type Props = {
  countries?: NationalityCountry[] | null
  size?: number
  showNames?: boolean
}

export function PlayerNationality({ countries, size = 18, showNames = true }: Props) {
  const list = countries?.filter((c) => c.flag_url || c.name) ?? []
  if (!list.length) return null

  return (
    <span className="fm-player-nationality">
      {list.map((c) => (
        <span
          key={`${c.name}-${c.flag_url}`}
          className="fm-player-nationality__item"
          title={formatCountryNameRu(c.name)}
        >
          {c.flag_url ? (
            <img
              src={c.flag_url}
              alt=""
              width={size}
              height={Math.round(size * 0.75)}
              className="fm-player-nationality__flag"
              loading="lazy"
            />
          ) : null}
          {showNames ? (
            <span className="fm-player-nationality__name">{formatCountryNameRu(c.name)}</span>
          ) : null}
        </span>
      ))}
    </span>
  )
}

export function formatPlayerBirthDate(iso?: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return '—'
  return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

export function formatContractEnd(iso?: string | null): string {
  return formatPlayerBirthDate(iso)
}

export function playerMetaLine(player: Player): string {
  const parts: string[] = []
  if (player.date_of_birth) {
    parts.push(formatPlayerBirthDate(player.date_of_birth))
  }
  const nat = player.nationality_countries
    ?.map((c) => formatCountryNameRu(c.name))
    .filter(Boolean)
    .join(', ')
  if (nat) parts.push(nat)
  if (player.contract_end_date) {
    parts.push(`до ${formatContractEnd(player.contract_end_date)}`)
  }
  return parts.join(' · ')
}
