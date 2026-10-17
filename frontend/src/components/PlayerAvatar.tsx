import { Avatar } from 'antd'

type Props = {
  name: string
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

export function PlayerAvatar({ name, size = 36, className }: Props) {
  return (
    <Avatar
      className={className}
      size={size}
      style={{
        background: 'linear-gradient(145deg, #3d8f6a 0%, #2a5c46 100%)',
        border: '2px solid #5ce29c',
        fontSize: Math.max(9, Math.round(size * 0.3)),
        fontWeight: 700,
        flexShrink: 0,
      }}
    >
      {initialsFromName(name)}
    </Avatar>
  )
}
