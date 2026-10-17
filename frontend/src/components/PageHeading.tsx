import { Space, Typography } from 'antd'
import type { ReactNode } from 'react'

const { Title, Text } = Typography

type Props = {
  eyebrow?: string
  title: string
  subtitle?: string
  extra?: ReactNode
  leading?: ReactNode
}

export function PageHeading({ eyebrow, title, subtitle, extra, leading }: Props) {
  return (
    <div className="fm-page-heading">
      <Space align="start" size={14}>
        {leading}
        <div>
          {eyebrow && <Text className="fm-eyebrow">{eyebrow}</Text>}
          <Title level={2} style={{ margin: 0, fontSize: 28, letterSpacing: '-0.02em' }}>
            {title}
          </Title>
          {subtitle && (
            <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
              {subtitle}
            </Text>
          )}
        </div>
      </Space>
      {extra}
    </div>
  )
}
