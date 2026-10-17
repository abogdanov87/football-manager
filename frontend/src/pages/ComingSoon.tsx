import { Button, Result } from 'antd'
import { useNavigate } from 'react-router-dom'

type Props = { title: string }

export function ComingSoon({ title }: Props) {
  const navigate = useNavigate()
  return (
    <Result
      icon={<span style={{ fontSize: 48, color: '#5ee09a' }}>◌</span>}
      title={title}
      subTitle="Этот раздел появится в обновлении 0.2."
      extra={
        <Button type="primary" onClick={() => navigate('/')}>
          На главную
        </Button>
      }
    />
  )
}
