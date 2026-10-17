import { Button, Card, Segmented, Space, Typography } from 'antd'
import { useMemo, useState } from 'react'
import type { MatchResult, StandingRow } from '../api/client'
import type { SeasonOverview } from '../api/client'
import { ClubCrest } from '../components/ClubCrest'
import { MatchReportModal } from '../components/MatchReportModal'
import { PageHeading } from '../components/PageHeading'
import { clubMapFromStandings, resolveCrestUrl } from '../utils/clubs'

const { Text } = Typography

type Fixture = SeasonOverview['upcoming_fixtures'][number]

type Props = {
  matches: MatchResult[]
  upcomingFixtures: Fixture[]
  currentMatchday: number
  playerClubId: number | null
  standings: StandingRow[]
  competitionName?: string
  onGoTable: () => void
}

export function MatchResults({
  matches,
  upcomingFixtures,
  currentMatchday,
  playerClubId,
  standings,
  competitionName,
  onGoTable,
}: Props) {
  const clubMap = useMemo(() => clubMapFromStandings(standings), [standings])
  const matchdays = useMemo(() => {
    const set = new Set(matches.map((m) => m.matchday))
    set.add(currentMatchday)
    return Array.from(set).sort((a, b) => b - a)
  }, [matches, currentMatchday])

  const [selectedDay, setSelectedDay] = useState<number>(matchdays[0] ?? currentMatchday)
  const [report, setReport] = useState<MatchResult | null>(null)

  const dayMatches = matches.filter((m) => m.matchday === selectedDay)

  const isPlayerMatch = (m: MatchResult) => {
    const home = clubMap.get(m.home_club) ?? clubMap.get(m.home_short)
    const away = clubMap.get(m.away_club) ?? clubMap.get(m.away_short)
    return home?.id === playerClubId || away?.id === playerClubId
  }

  return (
    <div>
      <PageHeading
        eyebrow="СОРЕВНОВАНИЯ"
        title="История матчей"
        subtitle="Результаты и отчёты прошедших туров."
        extra={<Button>{competitionName ?? 'Премьер-лига'} ⌄</Button>}
      />

      <Space style={{ marginBottom: 18, width: '100%', justifyContent: 'space-between' }} wrap>
        <Segmented
          options={matchdays.map((d) => ({ label: `Тур ${d}`, value: d }))}
          value={selectedDay}
          onChange={(v) => setSelectedDay(v as number)}
        />
      </Space>

      <Card styles={{ body: { padding: '0 20px 8px' } }}>
        <div style={{ padding: '16px 0', borderBottom: '1px solid #29353d' }}>
          <Text strong>Тур {selectedDay}</Text>
          {selectedDay === currentMatchday && upcomingFixtures.length > 0 && (
            <Text type="secondary" style={{ marginLeft: 12, fontSize: 11 }}>
              + {upcomingFixtures.length} матч(ей) ещё не сыграно
            </Text>
          )}
        </div>

        {!dayMatches.length ? (
          <Text type="secondary" style={{ display: 'block', padding: '24px 0' }}>
            Матчи этого тура ещё не в ленте. Сыграйте тур или выберите другой.
          </Text>
        ) : (
          dayMatches.map((m) => (
            <div
              key={m.id}
              className={`fm-fixture-row ${isPlayerMatch(m) ? 'club-match' : ''}`}
            >
              <div className="fm-fixture-home">
                <Text>{m.home_club}</Text>
                <ClubCrest src={resolveCrestUrl(m.home_club, clubMap)} alt={m.home_club} size="small" />
              </div>
              <Text strong style={{ textAlign: 'center', fontSize: 15 }}>
                {m.home_score} : {m.away_score}
              </Text>
              <div className="fm-fixture-away">
                <ClubCrest src={resolveCrestUrl(m.away_club, clubMap)} alt={m.away_club} size="small" />
                <Text>{m.away_club}</Text>
              </div>
              <Button type="link" onClick={() => setReport(m)}>Отчёт →</Button>
            </div>
          ))
        )}
      </Card>

      <MatchReportModal
        open={!!report}
        match={report}
        homeCrest={report ? resolveCrestUrl(report.home_club, clubMap) : undefined}
        awayCrest={report ? resolveCrestUrl(report.away_club, clubMap) : undefined}
        onClose={() => setReport(null)}
        onGoTable={() => {
          setReport(null)
          onGoTable()
        }}
        competitionLabel={competitionName}
      />
    </div>
  )
}
