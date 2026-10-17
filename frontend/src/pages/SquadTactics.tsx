import { Alert, Button, Card, Select, Space, Table, Typography, message } from 'antd'
import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import type { Club, Player } from '../api/client'

const { Title } = Typography

const FORMATIONS = [
  { value: '4-4-2', label: '4-4-2' },
  { value: '4-3-3', label: '4-3-3' },
]

type Props = { clubId: number | null }

export function SquadTactics({ clubId }: Props) {
  const [club, setClub] = useState<Club | null>(null)
  const [players, setPlayers] = useState<Player[]>([])
  const [formation, setFormation] = useState('4-4-2')
  const [selected, setSelected] = useState<number[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!clubId) return
    setLoading(true)
    api
      .getSquad(clubId)
      .then((data) => {
        setClub(data.club)
        setPlayers(data.players)
        setFormation(data.club.formation)
        setSelected(data.club.lineup_player_ids)
      })
      .finally(() => setLoading(false))
  }, [clubId])

  const save = async () => {
    if (!clubId) return
    if (selected.length !== 11) {
      message.warning('Выберите ровно 11 игроков в стартовом составе')
      return
    }
    try {
      const updated = await api.updateTactics(clubId, {
        formation,
        lineup_player_ids: selected,
      })
      setClub(updated)
      message.success('Тактика сохранена')
    } catch (e) {
      message.error(e instanceof Error ? e.message : 'Ошибка сохранения')
    }
  }

  const columns = useMemo(
    () => [
      { title: 'Игрок', dataIndex: 'name', key: 'name' },
      { title: 'Поз.', dataIndex: 'position', key: 'position', width: 70 },
      { title: 'ОВР', dataIndex: 'overall', key: 'overall', width: 70 },
      { title: 'Возр.', dataIndex: 'age', key: 'age', width: 70 },
    ],
    [],
  )

  if (!clubId) {
    return <Alert type="info" message="Клуб игрока не найден" />
  }

  return (
    <div>
      <Title level={3}>Состав и тактика</Title>
      <Card loading={loading}>
        <Space style={{ marginBottom: 16 }}>
          <span>Схема:</span>
          <Select value={formation} options={FORMATIONS} onChange={setFormation} style={{ width: 120 }} />
          <Button type="primary" onClick={save}>Сохранить</Button>
        </Space>
        <Table
          rowKey="id"
          size="small"
          pagination={false}
          dataSource={players}
          columns={columns}
          rowSelection={{
            type: 'checkbox',
            selectedRowKeys: selected,
            onChange: (keys) => setSelected(keys as number[]),
          }}
        />
        <Alert
          style={{ marginTop: 12 }}
          type="info"
          showIcon
          message={`Стартовый состав: ${selected.length}/11 · ${club?.name ?? ''}`}
        />
      </Card>
    </div>
  )
}
