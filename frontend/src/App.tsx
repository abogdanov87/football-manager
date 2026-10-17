import {
  HistoryOutlined,
  HomeOutlined,
  MenuOutlined,
  SettingOutlined,
  SwapOutlined,
  TableOutlined,
  TeamOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import { Avatar, Layout, Menu, Spin, Statistic, Typography, theme } from 'antd'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { BrowserRouter, Link, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { api } from './api/client'
import type { Club, SeasonOverview, StandingRow } from './api/client'
import { ClubCrest } from './components/ClubCrest'
import { ComingSoon } from './pages/ComingSoon'
import { Dashboard } from './pages/Dashboard'
import { LeagueTable } from './pages/LeagueTable'
import { MatchResults } from './pages/MatchResults'
import { SquadTactics } from './pages/SquadTactics'
import dayjs from 'dayjs'

const { Header, Content, Sider } = Layout
const { Text } = Typography

function Shell() {
  const location = useLocation()
  const navigate = useNavigate()
  const [season, setSeason] = useState<SeasonOverview | null>(null)
  const [standings, setStandings] = useState<StandingRow[]>([])
  const [playerClub, setPlayerClub] = useState<Club | null>(null)
  const [loading, setLoading] = useState(true)
  const { token } = theme.useToken()

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const [s, st] = await Promise.all([api.getSeason(), api.getStandings()])
      setSeason(s)
      setStandings(st)
      if (s.player_club_id) {
        const squad = await api.getSquad(s.player_club_id)
        setPlayerClub(squad.club)
      }
    } catch {
      setSeason(null)
      setStandings([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const menuKey = location.pathname === '/' ? '/' : location.pathname.split('/')[1] ? `/${location.pathname.split('/')[1]}` : '/'

  const siderMenuItems = useMemo(
    () => [
      {
        type: 'group' as const,
        label: 'КОМАНДА',
        children: [
          { key: '/', icon: <HomeOutlined />, label: <Link to="/">Главная</Link> },
          {
            key: '/squad',
            icon: <TeamOutlined />,
            label: <Link to="/squad">Состав и тактика</Link>,
          },
          {
            key: '/table',
            icon: <TableOutlined />,
            label: <Link to="/table">Таблица лиги</Link>,
          },
          {
            key: '/matches',
            icon: <HistoryOutlined />,
            label: <Link to="/matches">История матчей</Link>,
          },
        ],
      },
      {
        type: 'group' as const,
        label: 'РАЗВИТИЕ',
        children: [
          {
            key: '/transfers',
            icon: <SwapOutlined />,
            label: (
              <Link to="/transfers" className="fm-menu-link">
                <span>Трансферы</span>
                <span className="fm-soon-tag">СКОРО</span>
              </Link>
            ),
          },
          {
            key: '/training',
            icon: <ThunderboltOutlined />,
            label: (
              <Link to="/training" className="fm-menu-link">
                <span>Тренировки</span>
                <span className="fm-soon-tag">СКОРО</span>
              </Link>
            ),
          },
        ],
      },
    ],
    [],
  )

  const breadcrumb = useMemo(() => {
    switch (menuKey) {
      case '/':
        return 'Обзор клуба'
      case '/squad':
        return 'Команда / Состав и тактика'
      case '/table':
        return 'Соревнования / Премьер-лига'
      case '/matches':
        return 'Соревнования / История матчей'
      case '/transfers':
        return 'Развитие / Трансферы'
      case '/training':
        return 'Развитие / Тренировки'
      default:
        return 'Football Manager'
    }
  }, [menuKey])

  const countdownDeadline = season?.next_simulation_at
    ? dayjs(season.next_simulation_at).valueOf()
    : undefined

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        className="fm-sider"
        breakpoint="lg"
        collapsedWidth={72}
        width={268}
        theme="dark"
      >
        <div className="fm-sider-inner">
          <div className="fm-sider-head">
            <div className="fm-brand">
              <span className="fm-brand-mark">FM</span>
              <span>
                <b>Football</b>
                <em>Manager</em>
              </span>
            </div>
            {playerClub && (
              <div className="fm-club-chip">
                <ClubCrest src={playerClub.crest_url} alt={playerClub.name} size="medium" />
                <div className="fm-club-chip-text">
                  <strong>{playerClub.name}</strong>
                  <small>{season?.competition?.name ?? 'Премьер-лига'}</small>
                </div>
              </div>
            )}
          </div>
          <div className="fm-sider-nav">
            <Menu
              theme="dark"
              mode="inline"
              selectedKeys={[menuKey]}
              items={siderMenuItems}
            />
          </div>
          <div className="fm-sidebar-footer">
            <Menu
              theme="dark"
              mode="inline"
              selectable={false}
              items={[{ key: 'settings', icon: <SettingOutlined />, label: 'Настройки', disabled: true }]}
            />
            <small>v0.1.0 · Альфа</small>
          </div>
        </div>
      </Sider>
      <Layout>
        <Header
          style={{
            background: token.colorBgContainer,
            borderBottom: `1px solid ${token.colorBorder}`,
            paddingInline: 32,
            display: 'flex',
            alignItems: 'center',
            gap: 20,
            height: 66,
          }}
        >
          <MenuOutlined style={{ display: 'none' }} />
          <Text style={{ flex: 1, fontSize: 13, color: 'rgba(255,255,255,0.75)' }}>{breadcrumb}</Text>
          {countdownDeadline && (
            <div className="fm-topbar-matchday">
              <span className="fm-pulse" />
              ДО МАТЧ-ДНЯ
              <Statistic.Countdown
                value={countdownDeadline}
                format="HH:mm:ss"
                valueStyle={{ fontSize: 12, color: '#e0f7e9', fontWeight: 700 }}
              />
            </div>
          )}
          <Text type="secondary" style={{ fontSize: 12 }}>
            {season?.name ?? 'Сезон'}
          </Text>
          <Avatar style={{ background: '#224f3b', border: '1px solid #4ba879' }} size={32}>
            {playerClub?.short_name?.slice(0, 2) ?? 'FM'}
          </Avatar>
        </Header>
        <Content style={{ background: token.colorBgLayout }}>
          <div className="fm-content-wrap">
            {loading && !season ? (
              <Spin size="large" />
            ) : (
              <Routes>
                <Route
                  path="/"
                  element={
                    <Dashboard
                      season={season}
                      standings={standings}
                      playerClub={playerClub}
                      loading={loading}
                      onRefresh={refresh}
                      onNavigate={navigate}
                    />
                  }
                />
                <Route
                  path="/squad"
                  element={
                    <SquadTactics
                      clubId={season?.player_club_id ?? null}
                      currentMatchday={season?.current_matchday ?? 1}
                    />
                  }
                />
                <Route
                  path="/table"
                  element={
                    <LeagueTable
                      standings={standings}
                      loading={loading}
                      playerClubId={season?.player_club_id ?? null}
                      competition={season?.competition}
                      currentMatchday={season?.current_matchday ?? 1}
                    />
                  }
                />
                <Route
                  path="/matches"
                  element={
                    <MatchResults
                      matches={season?.recent_matches ?? []}
                      upcomingFixtures={season?.upcoming_fixtures ?? []}
                      currentMatchday={season?.current_matchday ?? 1}
                      playerClubId={season?.player_club_id ?? null}
                      standings={standings}
                      competitionName={season?.competition?.name}
                      onGoTable={() => navigate('/table')}
                    />
                  }
                />
                <Route path="/transfers" element={<ComingSoon title="Трансферный рынок" />} />
                <Route path="/training" element={<ComingSoon title="План тренировок" />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            )}
          </div>
        </Content>
      </Layout>
    </Layout>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Shell />
    </BrowserRouter>
  )
}
