import { Alert, Button, Card, Col, Row, Statistic, Typography } from 'antd'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/ru'
import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'
import type { SeasonOverview } from '../api/client'

dayjs.extend(relativeTime)
dayjs.locale('ru')

const { Title, Paragraph, Text } = Typography

type Props = {
  season: SeasonOverview | null
  loading: boolean
  onRefresh: () => void
}

export function Dashboard({ season, loading, onRefresh }: Props) {
  const [simulating, setSimulating] = useState(false)
  const [simMessage, setSimMessage] = useState<string | null>(null)

  const runDevSim = useCallback(async () => {
    if (!season?.manual_simulation_allowed) return
    setSimulating(true)
    setSimMessage(null)
    try {
      const res = await api.simulateMatchdayDev(true)
      setSimMessage(`${res.status}: ${res.message}`)
      onRefresh()
    } catch (e) {
      setSimMessage(e instanceof Error ? e.message : 'Ошибка')
    } finally {
      setSimulating(false)
    }
  }, [onRefresh, season?.manual_simulation_allowed])

  useEffect(() => {
    const id = window.setInterval(onRefresh, 60_000)
    return () => window.clearInterval(id)
  }, [onRefresh])

  if (!season && !loading) {
    return <Alert type="warning" message="Нет данных сезона. Запустите seed_league на backend." />
  }

  const next = season?.next_simulation_at ? dayjs(season.next_simulation_at) : null

  return (
    <div>
      <Title level={3}>Главная</Title>
      <Paragraph type="secondary">
        Туры лиги симулируются автоматически раз в день. Между турами настройте состав и тактику.
      </Paragraph>

      <Row gutter={[16, 16]}>
        <Col xs={24} md={8}>
          <Card loading={loading}>
            <Statistic title="Текущий тур" value={season?.current_matchday ?? '—'} suffix={`/ ${season?.total_matchdays ?? '—'}`} />
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card loading={loading}>
            <Statistic
              title="Следующий матч-день"
              value={next ? next.format('DD.MM HH:mm') : '—'}
            />
            {next && (
              <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
                {next.fromNow()}
              </Text>
            )}
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card loading={loading}>
            <Statistic
              title="Последняя симуляция"
              value={
                season?.last_simulation_at
                  ? dayjs(season.last_simulation_at).format('DD.MM HH:mm')
                  : 'ещё не было'
              }
            />
          </Card>
        </Col>
      </Row>

      {season?.manual_simulation_allowed && (
        <Card style={{ marginTop: 16 }} title="Разработка" size="small">
          <Button loading={simulating} onClick={runDevSim}>
            Принудительно сыграть тур (dev)
          </Button>
          {simMessage && <Paragraph style={{ marginTop: 8 }}>{simMessage}</Paragraph>}
        </Card>
      )}

      <Title level={4} style={{ marginTop: 24 }}>Последние результаты</Title>
      {!season?.recent_matches?.length ? (
        <Alert type="info" message="Результатов пока нет — дождитесь первого матч-дня." />
      ) : (
        season.recent_matches.slice(0, 6).map((m) => (
          <Card key={m.id} size="small" style={{ marginBottom: 8 }}>
            <Text strong>Тур {m.matchday}:</Text> {m.home_short} {m.home_score}:{m.away_score} {m.away_short}
          </Card>
        ))
      )}
    </div>
  )
}
