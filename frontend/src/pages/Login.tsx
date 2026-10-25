import { Alert, Button, Card, Input, Space, Typography } from 'antd'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { PageHeading } from '../components/PageHeading'

const { Text } = Typography

export function Login() {
  const { setSession } = useAuth()
  const navigate = useNavigate()
  const [step, setStep] = useState<'email' | 'code'>('email')
  const [email, setEmail] = useState('')
  const [code, setCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [info, setInfo] = useState<string | null>(null)

  const requestCode = async () => {
    setLoading(true)
    setError(null)
    try {
      await api.requestOtp(email.trim())
      setInfo('Если адрес корректен, код отправлен на почту.')
      setStep('code')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка отправки')
    } finally {
      setLoading(false)
    }
  }

  const verify = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.verifyOtp(email.trim(), code.trim())
      setSession(res.token, {
        id: res.user.id,
        email: res.user.email,
        club_id: res.club_id,
      })
      navigate(res.club_id ? '/' : '/claim-club', { replace: true })
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Неверный код')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fm-auth-page">
      <Card className="fm-card fm-auth-card">
        <PageHeading title="Вход" subtitle="Без пароля — код на email" />
        {error && <Alert type="error" message={error} showIcon style={{ marginBottom: 16 }} />}
        {info && step === 'code' && (
          <Alert type="info" message={info} showIcon style={{ marginBottom: 16 }} />
        )}
        {step === 'email' ? (
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <div>
              <Text type="secondary">Email</Text>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                onPressEnter={requestCode}
              />
            </div>
            <Button type="primary" block loading={loading} onClick={requestCode}>
              Получить код
            </Button>
          </Space>
        ) : (
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Text type="secondary">Код из письма для {email}</Text>
            <Input
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
              placeholder="000000"
              maxLength={6}
              onPressEnter={verify}
            />
            <Button type="primary" block loading={loading} onClick={verify}>
              Войти
            </Button>
            <Button type="link" onClick={() => setStep('email')}>
              Другой email
            </Button>
          </Space>
        )}
      </Card>
    </div>
  )
}
