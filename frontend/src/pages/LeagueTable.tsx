import { Button, Card, Space, Table, Tag, Typography } from 'antd'
import type { Competition, StandingRow } from '../api/client'
import { ClubCrest } from '../components/ClubCrest'
import { PageHeading } from '../components/PageHeading'

const { Text } = Typography

type Props = {
  standings: StandingRow[]
  loading: boolean
  playerClubId: number | null
  competition: Competition | null | undefined
  currentMatchday: number
}

export function LeagueTable({
  standings,
  loading,
  playerClubId,
  competition,
  currentMatchday,
}: Props) {
  return (
    <div>
      <PageHeading
        leading={
          <ClubCrest
            src={competition?.logo_url ?? '/crests/competitions/premier-league.png'}
            alt={competition?.name ?? 'Премьер-лига'}
            size="large"
          />
        }
        eyebrow="АНГЛИЯ · 2026/27"
        title={competition?.name ?? 'Премьер-лига'}
        extra={
          <Button>
            Тур {currentMatchday} <span style={{ marginLeft: 4 }}>⌄</span>
          </Button>
        }
      />

      <Card
        styles={{ body: { padding: 0 } }}
        loading={loading}
      >
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #29353d' }}>
          <Text>Таблица после {Math.max(0, currentMatchday - 1)}-го тура</Text>
          <Text type="secondary" style={{ marginLeft: 12, fontSize: 10 }}>
            Обновляется после каждой симуляции
          </Text>
        </div>
        <Table
          rowKey={(r) => r.club.id}
          size="small"
          pagination={false}
          dataSource={standings}
          rowClassName={(r) => (r.club.id === playerClubId ? 'fm-row-your-club' : '')}
          columns={[
            {
              title: '№',
              width: 48,
              render: (_, __, i) => (
                <Text type={i < 4 ? undefined : 'secondary'} style={{ fontWeight: i < 4 ? 700 : 400 }}>
                  {i + 1}
                </Text>
              ),
            },
            {
              title: 'КЛУБ',
              render: (_, row) => (
                <Space>
                  <ClubCrest src={row.club.crest_url} alt={row.club.name} size="small" />
                  <Text>{row.club.name}</Text>
                  {row.club.id === playerClubId && <Tag color="success">ВАШ КЛУБ</Tag>}
                </Space>
              ),
            },
            { title: 'И', dataIndex: 'played', width: 48, align: 'center' },
            { title: 'В', dataIndex: 'won', width: 48, align: 'center' },
            { title: 'Н', dataIndex: 'drawn', width: 48, align: 'center' },
            { title: 'П', dataIndex: 'lost', width: 48, align: 'center' },
            {
              title: 'ЗМ',
              dataIndex: 'goals_for',
              width: 48,
              align: 'center',
              className: 'fm-wide-col',
            },
            {
              title: 'ПМ',
              dataIndex: 'goals_against',
              width: 48,
              align: 'center',
              className: 'fm-wide-col',
            },
            {
              title: 'РМ',
              dataIndex: 'goal_difference',
              width: 48,
              align: 'center',
              className: 'fm-wide-col',
              render: (v: number) => (v > 0 ? `+${v}` : v),
            },
            {
              title: 'О',
              dataIndex: 'points',
              width: 50,
              align: 'center',
              render: (v: number) => <Text strong>{v}</Text>,
            },
          ]}
        />
        <div
          style={{
            borderTop: '1px solid #29353d',
            padding: '14px 20px',
            display: 'flex',
            gap: 20,
            fontSize: 10,
            color: '#788891',
          }}
        >
          <span><Tag color="green" /> Лига чемпионов</span>
          <span><Tag color="gold" /> Лига Европы</span>
          <span><Tag color="red" /> Зона вылета</span>
        </div>
      </Card>
    </div>
  )
}
