import type { ReactNode } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

type Props = {
  playerId: number
  children: ReactNode
  className?: string
  title?: string
}

/** Opens player profile; stops pointer events from bubbling (e.g. DnD). */
export function PlayerProfileLink({ playerId, children, className, title }: Props) {
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <button
      type="button"
      className={className ?? 'fm-player-profile-link'}
      title={title}
      onPointerDown={(e) => e.stopPropagation()}
      onClick={(e) => {
        e.stopPropagation()
        const from = location.pathname + location.search
        navigate(`/players/${playerId}`, { state: { from } })
      }}
    >
      {children}
    </button>
  )
}
