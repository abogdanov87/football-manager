import { Alert, Button, Card, Col, Row, Switch, Tag, Typography } from 'antd'
import dayjs from 'dayjs'
import { useCallback, useEffect, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import { api, type PlayerDetail } from '../api/client'
import { PageHeading } from '../components/PageHeading'
import { PlayerAvatar } from '../components/PlayerAvatar'
import { ClubCrest } from '../components/ClubCrest'
import { formatMarketValueUsd } from '../components/PlayerFifaStats'
import { formatPlayerBirthDate, PlayerNationality } from '../components/PlayerNationality'
import { PlayerProfileSkills } from '../components/PlayerProfileSkills'
import { PlayerSeasonStatsTable } from '../components/PlayerSeasonStatsTable'
import { formatTmPositionRu } from '../utils/playerLabels'

const { Text, Title } = Typography

const RENEWAL_LABELS: Record<string, string> = {
  secure: 'Стабильно',
  monitor: 'Наблюдение',
  urgent: 'Срочно',
}

function ageFromDob(dob: string | null | undefined, fallbackAge: number): number {
  if (!dob) return fallbackAge
  const d = dayjs(dob)
  if (!d.isValid()) return fallbackAge
  return dayjs().diff(d, 'year')
}

function formatWage(n: number): string {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`
  if (n >= 1_000) return `$${Math.round(n / 1_000)}K`
  return `$${n}`
}

export function PlayerProfile({ playerClubId }: { playerClubId: number | null }) {
  const { playerId } = useParams<{ playerId: string }>()
  const navigate = useNavigate()
  const location = useLocation()
  const from =
    (location.state as { from?: string } | null)?.from ?? '/squad'

  const [player, setPlayer] = useState<PlayerDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    const id = Number(playerId)
    if (!Number.isFinite(id)) return
    setLoading(true)
    setError(null)
    try {
      const data = await api.getPlayerDetail(id)
      setPlayer(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка загрузки')
      setPlayer(null)
    } finally {
      setLoading(false)
    }
  }, [playerId])

  useEffect(() => {
    load()
  }, [load])

  const updateRole = async (
    field: 'captain_player_id' | 'penalty_taker_player_id' | 'free_kick_taker_player_id',
    checked: boolean,
  ) => {
    if (!player || !playerClubId) return
    const body: Record<string, number | null> = {
      [field]: checked ? player.id : null,
    }
    await api.updateClubPlayerRoles(playerClubId, body)
    await load()
  }

  if (loading && !player) {
    return <Alert type="info" message="Загрузка профиля…" showIcon />
  }
  if (error || !player) {
    return (
      <>
        <Button type="link" onClick={() => navigate(from)} style={{ marginBottom: 8 }}>
          ← Назад
        </Button>
        <Alert type="error" message={error ?? 'Игрок не найден'} showIcon />
      </>
    )
  }

  const age = ageFromDob(player.date_of_birth, player.age)
  const contract = player.contract

  return (
    <div className="fm-player-profile">
      <Button type="link" onClick={() => navigate(from)} className="fm-player-profile__back">
        ← Назад
      </Button>
      <PageHeading title="Профиль игрока" />

      <Card className="fm-card fm-player-profile__hero">
        <div className="fm-player-profile__hero-row">
          <div className="fm-player-profile__hero-main">
            <PlayerAvatar name={player.name} photoUrl={player.photo_url} size={112} />
            <div className="fm-player-profile__hero-text">
              <Title level={3} className="fm-player-profile__name">
                {player.name}
              </Title>
              <div className="fm-player-profile__meta">
                <PlayerNationality countries={player.nationality_countries} size={18} />
                <Text className="fm-player-profile__position-line">
                  {formatTmPositionRu(player.tm_position, player.position)} · {age} лет
                  {player.date_of_birth
                    ? ` (${formatPlayerBirthDate(player.date_of_birth)})`
                    : ''}
                </Text>
              </div>
              <Text className="fm-player-profile__mv-inline">
                <span className="fm-player-profile__mv-label">Стоимость: </span>
                <strong>{formatMarketValueUsd(player.market_value_usd)}</strong>
              </Text>
            </div>
          </div>
          <div
            className="fm-player-profile__club-badge"
            title={player.club?.name ?? undefined}
          >
            <ClubCrest src={player.club?.crest_url} alt={player.club?.name ?? ''} size="large" />
          </div>
        </div>
      </Card>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} md={12}>
          <Card className="fm-card" title="Контракт">
            {contract ? (
              <dl className="fm-player-profile__dl">
                <div>
                  <dt>До</dt>
                  <dd>
                    {contract.contract_end_date
                      ? dayjs(contract.contract_end_date).format('DD.MM.YYYY')
                      : '—'}
                  </dd>
                </div>
                <div>
                  <dt>Осталось</dt>
                  <dd>
                    {contract.years_remaining} г. {contract.months_remaining} мес.
                  </dd>
                </div>
                <div>
                  <dt>Переподписание</dt>
                  <dd>
                    <Tag color={contract.renewal_status === 'urgent' ? 'red' : 'default'}>
                      {RENEWAL_LABELS[contract.renewal_status] ?? contract.renewal_status}
                    </Tag>
                  </dd>
                </div>
                <div>
                  <dt>Зарплата</dt>
                  <dd>
                    {formatWage(contract.weekly_wage_usd)} / нед ·{' '}
                    {formatWage(contract.yearly_wage_usd)} / год
                  </dd>
                </div>
              </dl>
            ) : (
              '—'
            )}
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card className="fm-card" title="Любимые позиции (9000 мин)">
            <ul className="fm-player-profile__positions">
              {player.favorite_positions?.length
                ? player.favorite_positions.map((p) => (
                    <li key={p.position_code}>
                      <strong>{formatTmPositionRu(p.position_code)}</strong>
                      <span> — {p.percent}% игрового времени</span>
                    </li>
                  ))
                : <li>Нет данных</li>}
            </ul>
          </Card>
        </Col>
      </Row>

      {player.can_edit_roles && (
        <Card className="fm-card" title="Роли в команде" style={{ marginTop: 16 }}>
          <div className="fm-player-profile__roles">
            <div className="fm-player-profile__role-row">
              <span>Капитан</span>
              <Switch
                checked={player.roles?.is_captain}
                onChange={(c) => updateRole('captain_player_id', c)}
              />
            </div>
            <div className="fm-player-profile__role-row">
              <span>Пенальти</span>
              <Switch
                checked={player.roles?.is_penalty_taker}
                onChange={(c) => updateRole('penalty_taker_player_id', c)}
              />
            </div>
            <div className="fm-player-profile__role-row">
              <span>Штрафные</span>
              <Switch
                checked={player.roles?.is_free_kick_taker}
                onChange={(c) => updateRole('free_kick_taker_player_id', c)}
              />
            </div>
          </div>
        </Card>
      )}

      <Card className="fm-card" title="Навыки" style={{ marginTop: 16 }}>
        <PlayerProfileSkills player={player} />
      </Card>

      <Card className="fm-card" title="Сезоны" style={{ marginTop: 16 }}>
        <PlayerSeasonStatsTable rows={player.season_stats ?? []} />
      </Card>

      <Card className="fm-card" title="Карьера" style={{ marginTop: 16, marginBottom: 24 }}>
        <ul className="fm-player-profile__career">
          {(player.career ?? []).map((c, i) => (
            <li key={`${c.club_name}-${i}`}>
              <strong>{c.club_name}</strong>
              <span>
                {' '}
                — {c.from_date ? dayjs(c.from_date).format('MM.YYYY') : '?'} —{' '}
                {c.to_date ? dayjs(c.to_date).format('MM.YYYY') : 'н.в.'}
              </span>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  )
}
