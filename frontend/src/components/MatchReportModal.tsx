import { Button, Modal, Space, Timeline, Typography } from 'antd'
import type { MatchResult } from '../api/client'
import { ClubCrest } from './ClubCrest'

const { Text } = Typography

type Props = {
  match: MatchResult | null
  homeCrest?: string
  awayCrest?: string
  open: boolean
  onClose: () => void
  onGoTable?: () => void
  competitionLabel?: string
}

export function MatchReportModal({
  match,
  homeCrest,
  awayCrest,
  open,
  onClose,
  onGoTable,
  competitionLabel = 'Премьер-лига',
}: Props) {
  if (!match) return null

  return (
    <Modal
      open={open}
      onCancel={onClose}
      footer={null}
      width={570}
      className="fm-report-modal"
      title={null}
      centered
    >
      <Text className="fm-eyebrow" style={{ display: 'block', textAlign: 'center' }}>
        {competitionLabel} · Тур {match.matchday}
      </Text>
      <div className="fm-report-score">
        <Space direction="vertical" align="center" size={8}>
          <ClubCrest src={homeCrest} alt={match.home_club} size="match" />
          <Text>{match.home_club}</Text>
        </Space>
        <TitleScore home={match.home_score} away={match.away_score} />
        <Space direction="vertical" align="center" size={8}>
          <ClubCrest src={awayCrest} alt={match.away_club} size="match" />
          <Text>{match.away_club}</Text>
        </Space>
      </div>
      <Timeline
        style={{ marginTop: 16 }}
        items={match.events.map((e) => ({
          children: <Text style={{ fontSize: 12 }}>{e}</Text>,
        }))}
      />
      <Space style={{ marginTop: 20, width: '100%', justifyContent: 'flex-end' }}>
        {onGoTable && (
          <Button onClick={onGoTable}>К таблице</Button>
        )}
        <Button type="primary" onClick={onClose}>
          Вернуться к истории
        </Button>
      </Space>
    </Modal>
  )
}

function TitleScore({ home, away }: { home: number; away: number }) {
  return (
    <span style={{ fontSize: 35, fontWeight: 700 }}>
      {home} <span style={{ color: '#6d7b83' }}>:</span> {away}
    </span>
  )
}
