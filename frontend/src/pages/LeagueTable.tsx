import { Table, Typography } from 'antd'
import type { StandingRow } from '../api/client'

const { Title } = Typography

type Props = { standings: StandingRow[]; loading: boolean }

export function LeagueTable({ standings, loading }: Props) {
  return (
    <div>
      <Title level={3}>Турнирная таблица</Title>
      <Table
        rowKey={(r) => r.club.id}
        loading={loading}
        size="small"
        pagination={false}
        dataSource={standings}
        columns={[
          { title: '#', width: 48, render: (_, __, i) => i + 1 },
          { title: 'Клуб', dataIndex: ['club', 'name'] },
          { title: 'И', dataIndex: 'played', width: 48 },
          { title: 'В', dataIndex: 'won', width: 48 },
          { title: 'Н', dataIndex: 'drawn', width: 48 },
          { title: 'П', dataIndex: 'lost', width: 48 },
          { title: 'З', dataIndex: 'goals_for', width: 48 },
          { title: 'П', dataIndex: 'goals_against', width: 48 },
          { title: '±', dataIndex: 'goal_difference', width: 48 },
          { title: 'О', dataIndex: 'points', width: 56 },
        ]}
      />
    </div>
  )
}
