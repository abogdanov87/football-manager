import {
  CalendarOutlined,
  LineChartOutlined,
  StarOutlined,
  TrophyOutlined,
} from '@ant-design/icons'
import { Alert, Button, Card, Col, Row, Space, Statistic, Table, Tag, Typography } from 'antd'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/ru'
import { useCallback, useEffect, useMemo, useState } from 'react'
import type { NavigateFunction } from 'react-router-dom'
import { api } from '../api/client'
import type { Club, MatchResult, SeasonOverview, StandingRow } from '../api/client'
import { ClubCrest } from '../components/ClubCrest'
import { MatchReportModal } from '../components/MatchReportModal'
import { PageHeading } from '../components/PageHeading'
import { clubMapFromStandings, playerStanding, resolveCrestUrl } from '../utils/clubs'

dayjs.extend(relativeTime)
dayjs.locale('ru')

const { Text, Link: TextLink } = Typography

type Props = {
  season: SeasonOverview | null
  standings: StandingRow[]
  playerClub: Club | null
  loading: boolean
  onRefresh: () => void
  onNavigate: NavigateFunction
}

export function Dashboard({ season, standings, playerClub, loading, onRefresh, onNavigate }: Props) {
  const [simulating, setSimulating] = useState(false)
  const [simMessage, setSimMessage] = useState<string | null>(null)
  const [reportMatch, setReportMatch] = useState<MatchResult | null>(null)

  const clubMap = useMemo(() => clubMapFromStandings(standings), [standings])
  const playerRow = playerStanding(standings, season?.player_club_id ?? null)

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

  const nextFixture = season?.upcoming_fixtures?.find(
    (f) =>
      f.home_club.id === season.player_club_id || f.away_club.id === season.player_club_id,
  )
  const lastMatch = season?.recent_matches?.find(
    (m) =>
      m.home_club === playerClub?.name ||
      m.away_club === playerClub?.name ||
      m.home_short === playerClub?.short_name ||
      m.away_short === playerClub?.short_name,
  )

  const lastResultTag = () => {
    if (!lastMatch || !playerClub) return null
    const isHome = lastMatch.home_club === playerClub.name || lastMatch.home_short === playerClub.short_name
    const us = isHome ? lastMatch.home_score : lastMatch.away_score
    const them = isHome ? lastMatch.away_score : lastMatch.home_score
    if (us > them) return <Tag color="success">ПОБЕДА</Tag>
    if (us < them) return <Tag color="error">ПОРАЖЕНИЕ</Tag>
    return <Tag>НИЧЬЯ</Tag>
  }

  const topFive = standings.slice(0, 5)

  return (
    <div>
      <PageHeading
        eyebrow="ДОБРО ПОЖАЛОВАТЬ ОБРАТНО"
        title="Добрый вечер, менеджер"
        subtitle="Ваш клуб готов к следующему матчу."
      />

      <Row gutter={[14, 14]} className="fm-dashboard-stats" style={{ marginBottom: 18 }} align="stretch">
        <Col xs={24} sm={12} xl={6} className="fm-stat-col">
          <Card loading={loading} className="fm-stat-card">
            <Statistic
              title={<Text type="secondary" style={{ fontSize: 10, letterSpacing: 0.6 }}>ТЕКУЩИЙ ТУР</Text>}
              value={season?.current_matchday ?? '—'}
              suffix={<Text type="secondary">/ {season?.total_matchdays ?? '—'}</Text>}
              prefix={<CalendarOutlined className="fm-stat-icon" />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} xl={6} className="fm-stat-col">
          <Card loading={loading} className="fm-stat-card">
            <Statistic
              title={<Text type="secondary" style={{ fontSize: 10, letterSpacing: 0.6 }}>СЛЕДУЮЩАЯ СИМУЛЯЦИЯ</Text>}
              value={
                season?.next_simulation_at
                  ? dayjs(season.next_simulation_at).format('DD.MM HH:mm')
                  : '—'
              }
              prefix={<TrophyOutlined className="fm-stat-icon" />}
            />
            {season?.next_simulation_at && (
              <Text type="secondary" style={{ fontSize: 11 }}>
                {dayjs(season.next_simulation_at).fromNow()}
              </Text>
            )}
          </Card>
        </Col>
        <Col xs={24} sm={12} xl={6} className="fm-stat-col">
          <Card loading={loading} className="fm-stat-card">
            <Statistic
              title={<Text type="secondary" style={{ fontSize: 10, letterSpacing: 0.6 }}>МЕСТО В ЛИГЕ</Text>}
              value={playerRow ? standings.indexOf(playerRow) + 1 : '—'}
              suffix={
                playerRow ? (
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {playerRow.points} очков
                  </Text>
                ) : undefined
              }
              prefix={<StarOutlined className="fm-stat-icon" />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} xl={6} className="fm-stat-col">
          <Card loading={loading} className="fm-stat-card">
            <Statistic
              title={<Text type="secondary" style={{ fontSize: 10, letterSpacing: 0.6 }}>РАЗНИЦА МЯЧЕЙ</Text>}
              value={playerRow?.goal_difference ?? '—'}
              prefix={<LineChartOutlined className="fm-stat-icon" />}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[18, 18]}>
        <Col xs={24} xl={16}>
          <Space direction="vertical" size={18} style={{ width: '100%' }}>
            <Card
              title={
                <Space>
                  <Text style={{ fontSize: 10, letterSpacing: 0.8, fontWeight: 700 }}>БЛИЖАЙШИЙ МАТЧ</Text>
                  <Text type="secondary" style={{ fontSize: 10 }}>
                    {season?.competition?.name} · Тур {season?.current_matchday}
                  </Text>
                </Space>
              }
              loading={loading}
              className="fm-next-match"
            >
              {nextFixture ? (
                <>
                  <div className="fm-match-teams">
                    <div className="fm-match-team fm-match-team--home">
                      <ClubCrest src={nextFixture.home_club.crest_url} alt={nextFixture.home_club.name} size="large" />
                      <Text strong className="fm-match-club-name">{nextFixture.home_club.name}</Text>
                      <Text type="secondary" className="fm-match-side-label">
                        {nextFixture.home_club.id === season?.player_club_id ? 'Ваш клуб' : 'Дома'}
                      </Text>
                    </div>
                    <div className="fm-versus">
                      <Text strong className="fm-versus-label">VS</Text>
                      <Text type="secondary" className="fm-versus-time">
                        {season?.next_simulation_at
                          ? dayjs(season.next_simulation_at).format('DD.MM, HH:mm')
                          : 'По расписанию'}
                      </Text>
                    </div>
                    <div className="fm-match-team fm-match-team--away">
                      <ClubCrest src={nextFixture.away_club.crest_url} alt={nextFixture.away_club.name} size="large" />
                      <Text strong className="fm-match-club-name">{nextFixture.away_club.name}</Text>
                      <Text type="secondary" className="fm-match-side-label">
                        {nextFixture.away_club.id === season?.player_club_id ? 'Ваш клуб' : 'В гостях'}
                      </Text>
                    </div>
                  </div>
                  <div className="fm-match-footer">
                    <Text type="secondary" style={{ fontSize: 11 }}>Матч тура лиги</Text>
                    <Button type="primary" onClick={() => onNavigate('/squad')}>
                      Настроить состав →
                    </Button>
                  </div>
                </>
              ) : (
                <Alert type="info" message="Нет предстоящих матчей в текущем туре." />
              )}
            </Card>

            <Card
              title={
                <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                  <Text style={{ fontSize: 10, letterSpacing: 0.8, fontWeight: 700 }}>ПОСЛЕДНИЙ РЕЗУЛЬТАТ</Text>
                  {lastMatch && (
                    <Button type="link" size="small" onClick={() => setReportMatch(lastMatch)}>
                      Отчёт матча →
                    </Button>
                  )}
                </Space>
              }
              loading={loading}
            >
              {lastMatch ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
                  <Space>
                    <ClubCrest
                      src={resolveCrestUrl(lastMatch.home_club, clubMap)}
                      alt={lastMatch.home_club}
                    />
                    <Text>{lastMatch.home_club}</Text>
                  </Space>
                  <Text style={{ fontSize: 24, fontWeight: 700 }}>
                    {lastMatch.home_score} : {lastMatch.away_score}
                  </Text>
                  <Space>
                    <ClubCrest
                      src={resolveCrestUrl(lastMatch.away_club, clubMap)}
                      alt={lastMatch.away_club}
                    />
                    <Text>{lastMatch.away_club}</Text>
                  </Space>
                  <span className="fm-win-tag">{lastResultTag()}</span>
                </div>
              ) : (
                <Alert type="info" message="Результатов пока нет — дождитесь первого матч-дня." />
              )}
            </Card>
          </Space>
        </Col>
        <Col xs={24} xl={8}>
          <Card
            className="fm-mini-table"
            title={
              <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                <Text style={{ fontSize: 10, letterSpacing: 0.8, fontWeight: 700 }}>ТУРНИРНАЯ ТАБЛИЦА</Text>
                <TextLink onClick={() => onNavigate('/table')}>Вся таблица →</TextLink>
              </Space>
            }
            loading={loading}
          >
            <Table
              size="small"
              pagination={false}
              rowKey={(r) => r.club.id}
              dataSource={topFive}
              rowClassName={(r) =>
                r.club.id === season?.player_club_id ? 'fm-row-highlight' : ''
              }
              columns={[
                {
                  title: '#',
                  width: 28,
                  render: (_, __, i) => i + 1,
                },
                {
                  title: 'КЛУБ',
                  render: (_, row) => (
                    <Space size={8}>
                      <ClubCrest src={row.club.crest_url} alt={row.club.name} size="small" />
                      {row.club.name}
                    </Space>
                  ),
                },
                { title: 'И', dataIndex: 'played', width: 28 },
                { title: 'О', dataIndex: 'points', width: 28 },
              ]}
            />
          </Card>
        </Col>
      </Row>

      <Space style={{ marginTop: 24 }} wrap>
        <Button type="primary" onClick={() => onNavigate('/squad')}>Настроить состав</Button>
        <Button onClick={() => onNavigate('/table')}>Таблица</Button>
        <Button onClick={() => onNavigate('/matches')}>История</Button>
      </Space>

      {season?.manual_simulation_allowed && (
        <Card style={{ marginTop: 16 }} title="Разработка" size="small">
          <Button loading={simulating} onClick={runDevSim}>
            Принудительно сыграть тур (dev)
          </Button>
          {simMessage && <Text style={{ display: 'block', marginTop: 8 }}>{simMessage}</Text>}
        </Card>
      )}

      <MatchReportModal
        open={!!reportMatch}
        match={reportMatch}
        homeCrest={reportMatch ? resolveCrestUrl(reportMatch.home_club, clubMap) : undefined}
        awayCrest={reportMatch ? resolveCrestUrl(reportMatch.away_club, clubMap) : undefined}
        onClose={() => setReportMatch(null)}
        onGoTable={() => {
          setReportMatch(null)
          onNavigate('/table')
        }}
        competitionLabel={season?.competition?.name}
      />
    </div>
  )
}
