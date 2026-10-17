import { Layout, Menu, Spin, theme } from 'antd'
import { useCallback, useEffect, useState } from 'react'
import { BrowserRouter, Link, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { api } from './api/client'
import type { SeasonOverview, StandingRow } from './api/client'
import { Dashboard } from './pages/Dashboard'
import { LeagueTable } from './pages/LeagueTable'
import { MatchResults } from './pages/MatchResults'
import { SquadTactics } from './pages/SquadTactics'
import './App.css'

const { Header, Content, Sider } = Layout

function Shell() {
  const location = useLocation()
  const [season, setSeason] = useState<SeasonOverview | null>(null)
  const [standings, setStandings] = useState<StandingRow[]>([])
  const [loading, setLoading] = useState(true)
  const {
    token: { colorBgContainer },
  } = theme.useToken()

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const [s, st] = await Promise.all([api.getSeason(), api.getStandings()])
      setSeason(s)
      setStandings(st)
    } catch {
      setSeason(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const menuKey = location.pathname === '/' ? '/' : location.pathname

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider breakpoint="lg" collapsedWidth={0}>
        <div style={{ color: '#fff', padding: 16, fontWeight: 600 }}>FM Online</div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[menuKey]}
          items={[
            { key: '/', label: <Link to="/">Главная</Link> },
            { key: '/squad', label: <Link to="/squad">Состав</Link> },
            { key: '/table', label: <Link to="/table">Таблица</Link> },
            { key: '/matches', label: <Link to="/matches">Матчи</Link> },
          ]}
        />
      </Sider>
      <Layout>
        <Header style={{ background: colorBgContainer, paddingInline: 24 }}>
          {season?.name ?? 'Football Manager'}
        </Header>
        <Content style={{ margin: 24 }}>
          {loading && !season ? (
            <Spin size="large" />
          ) : (
            <Routes>
              <Route path="/" element={<Dashboard season={season} loading={loading} onRefresh={refresh} />} />
              <Route path="/squad" element={<SquadTactics clubId={season?.player_club_id ?? null} />} />
              <Route path="/table" element={<LeagueTable standings={standings} loading={loading} />} />
              <Route
                path="/matches"
                element={
                  <MatchResults
                    matches={season?.recent_matches ?? []}
                    upcomingCount={season?.upcoming_fixtures?.length ?? 0}
                    currentMatchday={season?.current_matchday ?? 1}
                  />
                }
              />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          )}
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
