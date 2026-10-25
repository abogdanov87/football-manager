import {
  ClockCircleOutlined,
  MedicineBoxOutlined,
  ShareAltOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { Table } from 'antd'
import type { ReactNode } from 'react'
import type { PlayerSeasonStatRow } from '../api/client'

function StatColumnTitle({
  label,
  title,
  icon,
}: {
  label: string
  title: string
  icon: ReactNode
}) {
  return (
    <span className="fm-season-stat-th" title={title}>
      <span className="fm-season-stat-th__icon" aria-hidden>{icon}</span>
      <span className="fm-season-stat-th__label">{label}</span>
    </span>
  )
}

function CardIcon({ variant }: { variant: 'yellow' | 'red' }) {
  return <span className={`fm-card-icon fm-card-icon--${variant}`} aria-hidden />
}

const columns = [
  {
    title: 'Сезон',
    dataIndex: 'season_name',
    key: 'season_name',
  },
  {
    title: <StatColumnTitle label="И" title="Игры" icon={<UserOutlined />} />,
    dataIndex: 'appearances',
    key: 'appearances',
    align: 'center' as const,
    width: 56,
  },
  {
    title: <StatColumnTitle label="Мин" title="Минуты" icon={<ClockCircleOutlined />} />,
    dataIndex: 'minutes',
    key: 'minutes',
    align: 'center' as const,
    width: 72,
  },
  {
    title: <StatColumnTitle label="Г" title="Голы" icon={<span className="fm-stat-icon-goal">⚽</span>} />,
    dataIndex: 'goals',
    key: 'goals',
    align: 'center' as const,
    width: 56,
  },
  {
    title: <StatColumnTitle label="А" title="Голевые передачи" icon={<ShareAltOutlined />} />,
    dataIndex: 'assists',
    key: 'assists',
    align: 'center' as const,
    width: 56,
  },
  {
    title: (
      <StatColumnTitle label="ЖК" title="Жёлтые карточки" icon={<CardIcon variant="yellow" />} />
    ),
    dataIndex: 'yellow_cards',
    key: 'yellow_cards',
    align: 'center' as const,
    width: 56,
  },
  {
    title: (
      <StatColumnTitle label="КК" title="Красные карточки" icon={<CardIcon variant="red" />} />
    ),
    dataIndex: 'red_cards',
    key: 'red_cards',
    align: 'center' as const,
    width: 56,
  },
  {
    title: (
      <StatColumnTitle
        label="Дни"
        title="Дни на лечении"
        icon={<MedicineBoxOutlined />}
      />
    ),
    dataIndex: 'injury_days',
    key: 'injury_days',
    align: 'center' as const,
    width: 64,
  },
]

export function PlayerSeasonStatsTable({ rows }: { rows: PlayerSeasonStatRow[] }) {
  return (
    <Table
      className="fm-player-profile__season-table"
      size="small"
      pagination={false}
      rowKey="season_name"
      dataSource={rows}
      columns={columns}
    />
  )
}
