import { Alert, Collapse, Typography } from 'antd'
import type { MatchResult } from '../api/client'

const { Title, Text } = Typography

type Props = {
  matches: MatchResult[]
  upcomingCount: number
  currentMatchday: number
}

export function MatchResults({ matches, upcomingCount, currentMatchday }: Props) {
  return (
    <div>
      <Title level={3}>Матчи тура {currentMatchday}</Title>
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        message={`Ожидается ${upcomingCount} матч(ей) в текущем туре. Симуляция запускается по расписанию.`}
      />
      {!matches.length ? (
        <Alert message="Нет завершённых матчей в ленте" />
      ) : (
        <Collapse
          items={matches.map((m) => ({
            key: String(m.id),
            label: `Тур ${m.matchday}: ${m.home_club} ${m.home_score}:${m.away_score} ${m.away_club}`,
            children: (
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                {m.events.map((e, i) => (
                  <li key={i}><Text>{e}</Text></li>
                ))}
              </ul>
            ),
          }))}
        />
      )}
    </div>
  )
}
