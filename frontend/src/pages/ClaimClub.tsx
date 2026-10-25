import { Alert, Button, Card, Spin, Typography } from 'antd'
import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, type Club } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { ClubCrest } from '../components/ClubCrest'
import { PageHeading } from '../components/PageHeading'

const { Text } = Typography

export function ClaimClub() {
  const { refresh } = useAuth()
  const navigate = useNavigate()
  const [clubs, setClubs] = useState<Club[]>([])
  const [loading, setLoading] = useState(true)
  const [claiming, setClaiming] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const list = await api.getAvailableClubs()
      setClubs(list)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось загрузить клубы')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const claim = async (clubId: number) => {
    setClaiming(clubId)
    setError(null)
    try {
      await api.claimClub(clubId)
      await refresh()
      navigate('/', { replace: true })
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Клуб уже занят')
      await load()
    } finally {
      setClaiming(null)
    }
  }

  return (
    <div className="fm-auth-page">
      <Card className="fm-card fm-auth-card fm-claim-card">
        <PageHeading
          title="Выберите клуб"
          subtitle="Общая лига АПЛ — один клуб на менеджера"
        />
        {error && <Alert type="error" message={error} showIcon style={{ marginBottom: 16 }} />}
        {loading ? (
          <Spin />
        ) : clubs.length === 0 ? (
          <Text type="secondary">Нет свободных клубов. Лига заполнена.</Text>
        ) : (
          <ul className="fm-claim-list">
            {clubs.map((c) => (
              <li key={c.id}>
                <ClubCrest src={c.crest_url} alt={c.name} size="medium" />
                <div className="fm-claim-list__meta">
                  <strong>{c.name}</strong>
                  <Text type="secondary">{c.short_name}</Text>
                </div>
                <Button
                  type="primary"
                  size="small"
                  loading={claiming === c.id}
                  onClick={() => claim(c.id)}
                >
                  Выбрать
                </Button>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  )
}
