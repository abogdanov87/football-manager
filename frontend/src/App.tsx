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
import { Avatar, Layout, Menu, Spin, Statistic, Typography } from 'antd'
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
    <div className="fm-app-shell">
      <div className="fm-stadium-backdrop" aria-hidden="true" />
      <Layout className="fm-layout" style={{ minHeight: '100vh' }}>
      <Sider
        className="fm-sider"
        breakpoint="lg"
        collapsedWidth={68}
        width={250}
        theme="dark"
      >
        <div className="fm-sider-inner">
          <div className="fm-sider-head">
            <div className="fm-brand">
              <span className="fm-sports-word">sports</span>
              <span className="fm-brand-divider" />
              <span className="fm-manager-label">Football Manager</span>
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
      <Layout style={{ background: 'transparent' }}>
        <Header
          className="fm-topbar"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 25,
          }}
        >
          <MenuOutlined style={{ display: 'none' }} />
          <Text className="fm-topbar-crumb">{breadcrumb}</Text>
          {countdownDeadline && (
            <div className="fm-topbar-matchday">
              <span className="fm-pulse" />
              ДО МАТЧ-ДНЯ
              <Statistic.Countdown
                value={countdownDeadline}
                format="HH:mm:ss"
                valueStyle={{ fontSize: 12, color: '#fff', fontWeight: 700 }}
              />
            </div>
          )}
          <Text className="fm-topbar-season">
            {season?.name ?? 'Сезон'} <span style={{ color: '#6e7d86' }}>⌄</span>
          </Text>
          <Avatar className="fm-profile-avatar" size={32}>
            {playerClub?.short_name?.slice(0, 2) ?? 'АМ'}
          </Avatar>
        </Header>
        <Content style={{ background: 'transparent' }}>
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
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Shell />
    </BrowserRouter>
  )
}
