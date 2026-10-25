import { Tag } from 'antd'
import type { MatchOutcome } from '../utils/matchResult'

const LABELS: Record<MatchOutcome, string> = {
  win: 'ПОБЕДА',
  draw: 'НИЧЬЯ',
  loss: 'ПОРАЖЕНИЕ',
}

type Props = { outcome: MatchOutcome }

export function MatchResultTag({ outcome }: Props) {
  return <Tag className={`fm-result-tag fm-result-tag--${outcome}`}>{LABELS[outcome]}</Tag>
}
