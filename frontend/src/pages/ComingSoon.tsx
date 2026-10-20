import { Button, Typography } from 'antd'
import { useNavigate } from 'react-router-dom'

const { Text, Title } = Typography

type Props = { title: string }

export function ComingSoon({ title }: Props) {
  const navigate = useNavigate()
  return (
    <div className="fm-coming-soon">
      <div className="fm-coming-icon" aria-hidden>◌</div>
      <Text className="fm-eyebrow">ОБНОВЛЕНИЕ 0.2</Text>
      <Title level={1} style={{ fontSize: 28, margin: '0 0 8px' }}>{title}</Title>
      <Text type="secondary" style={{ display: 'block', marginBottom: 22 }}>
        Этот раздел уже в разработке и появится в одном из ближайших обновлений.
      </Text>
      <Button type="primary" onClick={() => navigate('/')}>
        На главную
      </Button>
    </div>
  )
}
