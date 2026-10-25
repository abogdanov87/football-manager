import { Avatar } from 'antd'

type Size = 'small' | 'medium' | 'large' | 'match'

const SIZE_MAP: Record<Exclude<Size, 'match'>, number> = {
  small: 22,
  medium: 32,
  large: 54,
}

type Props = {
  src?: string | null
  alt: string
  size?: Size
}

/** Фиксированный квадрат: эмблема вписана object-fit contain (блок матча). */
export function ClubCrest({ src, alt, size = 'medium' }: Props) {
  if (size === 'match') {
    return (
      <div className="fm-crest-box fm-crest-box--match fm-crest-glow" title={alt}>
        {src ? (
          <img src={src} alt={alt} className="fm-crest-box__img" />
        ) : (
          <span className="fm-crest-box__fallback">{alt.slice(0, 1)}</span>
        )}
      </div>
    )
  }

  const px = SIZE_MAP[size]
  return (
    <span className={`fm-crest-wrap fm-crest-wrap--${size}`}>
      <Avatar
        shape="square"
        className="fm-crest-glow"
        src={src ?? undefined}
        alt={alt}
        size={px}
        style={{
          borderRadius: size === 'large' ? 10 : 6,
          background: '#2a3540',
          flexShrink: 0,
        }}
      >
        {alt.slice(0, 1)}
      </Avatar>
    </span>
  )
}
