import { Alert, Avatar, Button, Card, Col, Row, Select, Space, Table, Tag, Typography, message } from 'antd'
import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import type { Player } from '../api/client'
import { PageHeading } from '../components/PageHeading'

const { Text } = Typography

const FORMATIONS = [
  { value: '4-4-2', label: '4-4-2' },
  { value: '4-3-3', label: '4-3-3' },
]

const SLOT_LAYOUTS: Record<string, number[]> = {
  '4-4-2': [1, 4, 4, 2],
  '4-3-3': [1, 4, 3, 3],
}

type Props = { clubId: number | null; currentMatchday: number }

export function SquadTactics({ clubId, currentMatchday }: Props) {
  const [clubName, setClubName] = useState('')
  const [players, setPlayers] = useState<Player[]>([])
  const [formation, setFormation] = useState('4-4-2')
  const [slotIds, setSlotIds] = useState<number[]>([])
  const [loading, setLoading] = useState(false)
  const [savedFlash, setSavedFlash] = useState(false)

  useEffect(() => {
    if (!clubId) return
    setLoading(true)
    api
      .getSquad(clubId)
      .then((data) => {
        setClubName(data.club.name)
        setPlayers(data.players)
        setFormation(data.club.formation)
        const ids = data.club.lineup_player_ids
        const layout = SLOT_LAYOUTS[data.club.formation] ?? SLOT_LAYOUTS['4-4-2']
        const total = layout.reduce((a, b) => a + b, 0)
        setSlotIds(ids.length === total ? ids : ids.slice(0, total))
      })
      .finally(() => setLoading(false))
  }, [clubId])

  const layout = SLOT_LAYOUTS[formation] ?? SLOT_LAYOUTS['4-4-2']
  const slotCount = layout.reduce((a, b) => a + b, 0)

  const onFormationChange = (value: string) => {
    setFormation(value)
    const nextLayout = SLOT_LAYOUTS[value] ?? SLOT_LAYOUTS['4-4-2']
    const nextCount = nextLayout.reduce((a, b) => a + b, 0)
    setSlotIds((prev) => {
      const next = prev.slice(0, nextCount)
      while (next.length < nextCount) next.push(0)
      return next
    })
  }

  const setSlot = (index: number, playerId: number) => {
    setSlotIds((prev) => {
      const next = [...prev]
      next[index] = playerId
      return next
    })
  }

  const save = async () => {
    if (!clubId) return
    const lineup = slotIds.filter(Boolean)
    if (lineup.length !== 11 || new Set(lineup).size !== 11) {
      message.warning('Заполните все 11 слотов стартового состава')
      return
    }
    try {
      await api.updateTactics(clubId, { formation, lineup_player_ids: lineup })
      message.success('Тактика сохранена')
      setSavedFlash(true)
      window.setTimeout(() => setSavedFlash(false), 2500)
    } catch (e) {
      message.error(e instanceof Error ? e.message : 'Ошибка сохранения')
    }
  }

  const bench = useMemo(() => {
    const inLineup = new Set(slotIds.filter(Boolean))
    return players.filter((p) => !inLineup.has(p.id))
  }, [players, slotIds])

  const avgOverall = useMemo(() => {
    const picked = slotIds.map((id) => players.find((p) => p.id === id)?.overall).filter(Boolean) as number[]
    if (!picked.length) return '—'
    return Math.round(picked.reduce((a, b) => a + b, 0) / picked.length)
  }, [slotIds, players])

  let slotIndex = 0
  const lines = layout.map((count, lineIdx) => {
    const rowSlots = Array.from({ length: count }, () => {
      const idx = slotIndex++
      return (
        <div className="fm-field-slot" key={idx}>
          <Select
            size="small"
            placeholder="Игрок"
            value={slotIds[idx] || undefined}
            onChange={(v) => setSlot(idx, v)}
            options={players.map((p) => ({
              value: p.id,
              label: p.name.split(' ').pop() ?? p.name,
              disabled: slotIds.includes(p.id) && slotIds[idx] !== p.id,
            }))}
            popupMatchSelectWidth={false}
          />
          {slotIds[idx] && (
            <Text type="secondary" style={{ fontSize: 9 }}>
              {players.find((p) => p.id === slotIds[idx])?.overall}
            </Text>
          )}
        </div>
      )
    })
    return (
      <div className="fm-pitch-line" key={lineIdx}>
        {rowSlots}
      </div>
    )
  })

  if (!clubId) {
    return <Alert type="info" message="Клуб игрока не найден" />
  }

  return (
    <div>
      <PageHeading
        eyebrow="КОМАНДА"
        title="Состав и тактика"
        subtitle="Настройте стартовый состав перед матчем."
        extra={
          <Space>
            <Button onClick={() => onFormationChange(formation)}>Сбросить</Button>
            <Button type="primary" onClick={save}>
              {savedFlash ? '✓ Сохранено' : 'Сохранить'}
            </Button>
          </Space>
        }
      />

      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 18 }}
        message={`Изменения будут применены к матчу ${currentMatchday}-го тура. Состав можно менять до начала симуляции.`}
      />

      <Row gutter={[18, 18]}>
        <Col xs={24} lg={16}>
          <Card loading={loading} className="fm-pitch-card">
            <Space style={{ marginBottom: 16, width: '100%', justifyContent: 'space-between' }} wrap>
              <Space>
                <Text type="secondary" style={{ fontSize: 10, fontWeight: 700 }}>СХЕМА</Text>
                <Select value={formation} options={FORMATIONS} onChange={onFormationChange} style={{ width: 120 }} />
              </Space>
              <Text type="secondary" style={{ fontSize: 11 }}>
                Средний рейтинг <Text strong>{avgOverall}</Text>
              </Text>
            </Space>
            <div className="fm-pitch">{lines}</div>
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card
            title={
              <Space>
                <Text style={{ fontSize: 10, letterSpacing: 0.8, fontWeight: 700 }}>ЗАПАСНЫЕ</Text>
                <Text type="secondary" style={{ fontSize: 10 }}>{bench.length} игроков</Text>
              </Space>
            }
            loading={loading}
          >
            <Table
              size="small"
              pagination={false}
              rowKey="id"
              dataSource={bench}
              columns={[
                {
                  title: '',
                  width: 40,
                  render: (_, row) => (
                    <Avatar size={26} style={{ background: '#326a52', fontSize: 8 }}>
                      {row.name
                        .split(' ')
                        .map((n) => n[0])
                        .join('')
                        .slice(0, 2)}
                    </Avatar>
                  ),
                },
                { title: 'Игрок', dataIndex: 'name' },
                { title: 'Поз.', dataIndex: 'position', width: 48 },
                { title: 'ОВР', dataIndex: 'overall', width: 48 },
                {
                  title: '',
                  width: 64,
                  render: () => <Tag color="success" style={{ fontSize: 8 }}>Готов</Tag>,
                },
              ]}
            />
            <Text type="secondary" style={{ fontSize: 11, marginTop: 12, display: 'block' }}>
              {clubName} · слотов на поле: {slotCount}
            </Text>
          </Card>
        </Col>
      </Row>
    </div>
  )
}
