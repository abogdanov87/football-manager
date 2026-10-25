import { Typography } from 'antd'
import type { ReactNode } from 'react'

const { Text } = Typography

/** Bold scorer name in goal lines from match engine (⚽ … ГОЛ! Имя (клуб)…). */
export function renderMatchEventLine(event: string): ReactNode {
  const marker = 'ГОЛ!'
  const idx = event.indexOf(marker)
  if (idx === -1) return event

  const afterGoal = event.slice(idx + marker.length)
  const m = afterGoal.match(/^\s+(.+?)\s+(\(.+?\))(.*)$/)
  if (!m) return event

  const prefix = event.slice(0, idx + marker.length)
  const [, playerName, clubPart, tail] = m

  return (
    <>
      {prefix}
      {' '}
      <Text strong>{playerName}</Text>
      {' '}
      {clubPart}
      {tail}
    </>
  )
}
