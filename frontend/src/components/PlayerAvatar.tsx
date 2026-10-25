import { Avatar } from 'antd'

type Props = {
  name: string
  photoUrl?: string | null
  size?: number
  className?: string
}

export function initialsFromName(name: string): string {
  return name
    .split(' ')
    .filter(Boolean)
    .map((n) => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
}

export function PlayerAvatar({ name, photoUrl, size = 36, className }: Props) {
  const src = photoUrl?.trim() || undefined
  return (
    <Avatar
      className={className}
      size={size}
      src={src}
      alt={name}
      style={{
        background: src
          ? undefined
          : 'linear-gradient(145deg, #3d8f6a 0%, #2a5c46 100%)',
        border: '2px solid #5ce29c',
        fontSize: Math.max(9, Math.round(size * 0.3)),
        fontWeight: 700,
        flexShrink: 0,
      }}
    >
      {src ? null : initialsFromName(name)}
    </Avatar>
  )
}
