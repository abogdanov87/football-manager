import { Avatar } from 'antd'

type Size = 'small' | 'medium' | 'large'

const SIZE_MAP: Record<Size, number> = {
  small: 22,
  medium: 32,
  large: 54,
}

type Props = {
  src?: string | null
  alt: string
  size?: Size
}

export function ClubCrest({ src, alt, size = 'medium' }: Props) {
  const px = SIZE_MAP[size]
  return (
    <Avatar
      shape="square"
      src={src ?? undefined}
      alt={alt}
      size={px}
      style={{
        borderRadius: size === 'large' ? 10 : 6,
        background: '#1b272f',
        flexShrink: 0,
      }}
    >
      {alt.slice(0, 1)}
    </Avatar>
  )
}
