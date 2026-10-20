import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useDraggable,
  useDroppable,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from '@dnd-kit/core'
import {
  SortableContext,
  useSortable,
  verticalListSortingStrategy,
  arrayMove,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { Alert, Button, Card, Col, Row, Select, Space, Tag, Tooltip, Typography, message } from 'antd'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import type { Player } from '../api/client'
import { PageHeading } from '../components/PageHeading'
import { PlayerAvatar } from '../components/PlayerAvatar'

const { Text } = Typography

function playerStatTip(player: Player): string {
  const mv = player.market_value_usd
    ? `$${Math.round(player.market_value_usd / 1_000_000)}M`
    : '—'
  return [
    `PAC ${player.pac ?? '—'} · SHO ${player.sho ?? '—'} · PAS ${player.pas ?? '—'}`,
    `DRI ${player.dri ?? '—'} · DEF ${player.defending ?? '—'} · PHY ${player.phy ?? '—'}`,
    `Верх ${player.aerial ?? '—'} · Мент ${player.mentality ?? '—'} · Травмы ${player.injury_resistance ?? '—'}`,
    `Рынок: ${mv}`,
  ].join('\n')
}

const FORMATIONS = [
  { value: '4-4-2', label: '4-4-2' },
  { value: '4-3-3', label: '4-3-3' },
]

const SLOT_LAYOUTS: Record<string, number[]> = {
  '4-4-2': [1, 4, 4, 2],
  '4-3-3': [1, 4, 3, 3],
}

const playerDndId = (id: number) => `player-${id}`
const slotDndId = (index: number) => `slot-${index}`

function parsePlayerId(id: string): number | null {
  if (!id.startsWith('player-')) return null
  const n = Number(id.slice(7))
  return Number.isFinite(n) ? n : null
}

function parseSlotIndex(id: string): number | null {
  if (!id.startsWith('slot-')) return null
  const n = Number(id.slice(5))
  return Number.isFinite(n) ? n : null
}

function shortName(name: string): string {
  const parts = name.trim().split(/\s+/)
  return parts.length > 1 ? (parts[parts.length - 1] ?? name) : name
}

type Props = { clubId: number | null; currentMatchday: number }

function PitchSlot({
  index,
  player,
  isOver,
}: {
  index: number
  player: Player | null
  isOver: boolean
}) {
  const { setNodeRef, isOver: dropOver } = useDroppable({ id: slotDndId(index) })
  const highlighted = isOver || dropOver

  return (
    <div className={`fm-field-slot${highlighted ? ' fm-field-slot--over' : ''}`} ref={setNodeRef}>
      {player ? (
        <PitchPlayerChip player={player} slotIndex={index} />
      ) : (
        <div className="fm-slot-empty">
          <span className="fm-slot-empty-icon">+</span>
          <span>Слот</span>
        </div>
      )}
    </div>
  )
}

function PitchPlayerChip({ player, slotIndex }: { player: Player; slotIndex: number }) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: playerDndId(player.id),
    data: { type: 'pitch', slotIndex, playerId: player.id },
  })
  const style = {
    transform: CSS.Translate.toString(transform),
    opacity: isDragging ? 0.35 : 1,
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="fm-pitch-player"
      {...listeners}
      {...attributes}
    >
      <Tooltip title={<span style={{ whiteSpace: 'pre-line' }}>{playerStatTip(player)}</span>}>
        <span className="fm-slot-ovr">{player.overall}</span>
      </Tooltip>
      <PlayerAvatar name={player.name} size={44} />
      <Text className="fm-slot-name" ellipsis title={player.name}>
        {shortName(player.name)}
      </Text>
      <Text type="secondary" className="fm-slot-pos">{player.position}</Text>
    </div>
  )
}

function BenchRow({ player }: { player: Player }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: playerDndId(player.id),
    data: { type: 'bench', playerId: player.id },
  })

  return (
    <div
      ref={setNodeRef}
      className={`fm-bench-row${isDragging ? ' fm-bench-row--dragging' : ''}`}
      style={{
        transform: CSS.Transform.toString(transform),
        transition,
      }}
      {...listeners}
      {...attributes}
    >
      <span className="fm-bench-grip" aria-hidden>⋮⋮</span>
      <PlayerAvatar name={player.name} size={32} />
      <div className="fm-bench-meta">
        <Text strong className="fm-bench-name" ellipsis>
          {player.name}
        </Text>
        <Text type="secondary" className="fm-bench-sub">
          {player.position}
        </Text>
      </div>
      <Tooltip title={<span style={{ whiteSpace: 'pre-line' }}>{playerStatTip(player)}</span>}>
        <em className="fm-bench-ovr">{player.overall}</em>
      </Tooltip>
      <Tag className="fm-bench-ready">Готов</Tag>
    </div>
  )
}

function DragPreview({ player }: { player: Player }) {
  return (
    <div className="fm-pitch-player fm-pitch-player--overlay">
      <span className="fm-slot-ovr">{player.overall}</span>
      <PlayerAvatar name={player.name} size={44} />
      <Text className="fm-slot-name">{shortName(player.name)}</Text>
    </div>
  )
}

export function SquadTactics({ clubId, currentMatchday }: Props) {
  const [clubName, setClubName] = useState('')
  const [players, setPlayers] = useState<Player[]>([])
  const [formation, setFormation] = useState('4-4-2')
  const [slotIds, setSlotIds] = useState<number[]>([])
  const [benchOrder, setBenchOrder] = useState<number[]>([])
  const [initialFormation, setInitialFormation] = useState('4-4-2')
  const [initialSlotIds, setInitialSlotIds] = useState<number[]>([])
  const [loading, setLoading] = useState(false)
  const [savedFlash, setSavedFlash] = useState(false)
  const [activeDragId, setActiveDragId] = useState<string | null>(null)
  const [overId, setOverId] = useState<string | null>(null)

  const playerById = useMemo(() => new Map(players.map((p) => [p.id, p])), [players])

  const syncBenchOrder = useCallback((allPlayers: Player[], lineupIds: number[]) => {
    const inLineup = new Set(lineupIds.filter(Boolean))
    const benchIds = allPlayers.filter((p) => !inLineup.has(p.id)).map((p) => p.id)
    setBenchOrder(benchIds)
  }, [])

  useEffect(() => {
    if (!clubId) return
    setLoading(true)
    api
      .getSquad(clubId)
      .then((data) => {
        setClubName(data.club.name)
        setPlayers(data.players)
        setFormation(data.club.formation)
        setInitialFormation(data.club.formation)
        const layout = SLOT_LAYOUTS[data.club.formation] ?? SLOT_LAYOUTS['4-4-2']
        const total = layout.reduce((a, b) => a + b, 0)
        const ids = data.club.lineup_player_ids
        const normalized =
          ids.length === total ? [...ids] : [...ids.slice(0, total), ...Array(Math.max(0, total - ids.length)).fill(0)]
        setSlotIds(normalized)
        setInitialSlotIds(normalized)
        syncBenchOrder(data.players, normalized)
      })
      .finally(() => setLoading(false))
  }, [clubId, syncBenchOrder])

  const layout = SLOT_LAYOUTS[formation] ?? SLOT_LAYOUTS['4-4-2']
  const slotCount = layout.reduce((a, b) => a + b, 0)

  const onFormationChange = (value: string) => {
    setFormation(value)
    const nextLayout = SLOT_LAYOUTS[value] ?? SLOT_LAYOUTS['4-4-2']
    const nextCount = nextLayout.reduce((a, b) => a + b, 0)
    setSlotIds((prev) => {
      const next = prev.slice(0, nextCount)
      while (next.length < nextCount) next.push(0)
      syncBenchOrder(players, next)
      return next
    })
  }

  const resetLineup = () => {
    setFormation(initialFormation)
    setSlotIds([...initialSlotIds])
    syncBenchOrder(players, initialSlotIds)
  }

  const assignPlayerToSlot = useCallback((playerId: number, toSlot: number) => {
    setSlotIds((prev) => {
      const next = [...prev]
      const fromSlot = next.indexOf(playerId)
      const displaced = next[toSlot] || 0

      if (fromSlot >= 0) {
        next[fromSlot] = displaced
      }
      next[toSlot] = playerId

      setBenchOrder((bo) => {
        let order = bo.filter((id) => id !== playerId)
        if (displaced && displaced !== playerId && !next.includes(displaced)) {
          order = [...order, displaced]
        }
        const inLineup = new Set(next.filter(Boolean))
        const missing = players
          .filter((p) => !inLineup.has(p.id) && !order.includes(p.id))
          .map((p) => p.id)
        return [...order, ...missing]
      })
      return next
    })
  }, [players])

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
  )

  const onDragStart = (event: DragStartEvent) => {
    setActiveDragId(String(event.active.id))
  }

  const onDragEnd = (event: DragEndEvent) => {
    const { active, over } = event
    setActiveDragId(null)
    setOverId(null)
    if (!over) return

    const activePlayerId = parsePlayerId(String(active.id))
    if (!activePlayerId) return

    const overSlot = parseSlotIndex(String(over.id))
    if (overSlot !== null) {
      assignPlayerToSlot(activePlayerId, overSlot)
      return
    }

    const overPlayerId = parsePlayerId(String(over.id))
    if (overPlayerId && overPlayerId !== activePlayerId) {
      const activeOnBench = benchOrder.includes(activePlayerId)
      const overOnBench = benchOrder.includes(overPlayerId)
      if (activeOnBench && overOnBench) {
        setBenchOrder((items) => {
          const oldIndex = items.indexOf(activePlayerId)
          const newIndex = items.indexOf(overPlayerId)
          if (oldIndex < 0 || newIndex < 0) return items
          return arrayMove(items, oldIndex, newIndex)
        })
        return
      }

      const overSlotIdx = slotIds.indexOf(overPlayerId)
      if (overSlotIdx >= 0) {
        assignPlayerToSlot(activePlayerId, overSlotIdx)
      }
    }
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
      setInitialFormation(formation)
      setInitialSlotIds([...slotIds])
      setSavedFlash(true)
      window.setTimeout(() => setSavedFlash(false), 2500)
    } catch (e) {
      message.error(e instanceof Error ? e.message : 'Ошибка сохранения')
    }
  }

  const benchPlayers = useMemo(
    () =>
      benchOrder
        .map((id) => playerById.get(id))
        .filter((p): p is Player => Boolean(p)),
    [benchOrder, playerById],
  )

  const avgOverall = useMemo(() => {
    const picked = slotIds.map((id) => playerById.get(id)?.overall).filter(Boolean) as number[]
    if (!picked.length) return '—'
    return Math.round(picked.reduce((a, b) => a + b, 0) / picked.length)
  }, [slotIds, playerById])

  const activePlayer = activeDragId ? playerById.get(parsePlayerId(activeDragId) ?? -1) ?? null : null

  let slotIndex = 0
  const lines = layout.map((count, lineIdx) => {
    const rowSlots = Array.from({ length: count }, () => {
      const idx = slotIndex++
      const pid = slotIds[idx]
      const player = pid ? playerById.get(pid) ?? null : null
      const slotOver = overId === slotDndId(idx)
      return <PitchSlot key={idx} index={idx} player={player} isOver={slotOver} />
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
        subtitle="Перетащите игроков с запаса на поле или между слотами."
        extra={
          <Space>
            <Button onClick={resetLineup}>Сбросить</Button>
            <Button type="primary" onClick={save}>
              {savedFlash ? '✓ Сохранено' : 'Сохранить состав'}
            </Button>
          </Space>
        }
      />

      <div className="fm-notice" role="status">
        ⓘ &nbsp; Изменения будут применены к матчу <b>{currentMatchday}-го тура</b>. Перетаскивайте
        игроков на схему до начала симуляции.
      </div>

      <DndContext
        sensors={sensors}
        onDragStart={onDragStart}
        onDragOver={(e) => setOverId(e.over ? String(e.over.id) : null)}
        onDragEnd={onDragEnd}
        onDragCancel={() => {
          setActiveDragId(null)
          setOverId(null)
        }}
      >
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
              <div className="fm-pitch">
                <div className="fm-pitch-halfway" aria-hidden="true" />
                <div className="fm-pitch-circle" aria-hidden="true" />
                {lines}
              </div>
            </Card>
          </Col>
          <Col xs={24} lg={8}>
            <Card
              className="fm-bench-card"
              title={
                <Space>
                  <Text style={{ fontSize: 10, letterSpacing: 0.8, fontWeight: 700 }}>ЗАПАС И СОСТАВ</Text>
                  <Text type="secondary" style={{ fontSize: 10 }}>{benchPlayers.length} игроков</Text>
                </Space>
              }
              loading={loading}
            >
              <Text type="secondary" className="fm-bench-hint">
                Перетащите на поле или меняйте порядок в списке
              </Text>
              <SortableContext items={benchOrder.map(playerDndId)} strategy={verticalListSortingStrategy}>
                <div className="fm-bench-list">
                  {benchPlayers.length === 0 ? (
                    <Text type="secondary" style={{ fontSize: 12 }}>Все игроки в стартовом составе</Text>
                  ) : (
                    benchPlayers.map((p) => <BenchRow key={p.id} player={p} />)
                  )}
                </div>
              </SortableContext>
              <Text type="secondary" style={{ fontSize: 11, marginTop: 12, display: 'block' }}>
                {clubName} · слотов на поле: {slotCount}
              </Text>
            </Card>
          </Col>
        </Row>
        <DragOverlay dropAnimation={null}>
          {activePlayer ? <DragPreview player={activePlayer} /> : null}
        </DragOverlay>
      </DndContext>
    </div>
  )
}
