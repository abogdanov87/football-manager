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
import { Alert, Button, Card, Col, Row, Select, Space, Tag, Typography, message } from 'antd'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import type { Player } from '../api/client'
import { PageHeading } from '../components/PageHeading'
import { PlayerAvatar } from '../components/PlayerAvatar'
import { PlayerOverallWithStats } from '../components/PlayerFifaStats'
import { PlayerProfileLink } from '../components/PlayerProfileLink'
import {
  FORMATIONS,
  FORMATION_PITCH_SLOTS,
  formationSlotCount,
  formationSlotRoles,
  pitchSlotDisplayY,
  POSITION_FILTER_OPTIONS,
  type GamePosition,
} from '../formations'

const { Text } = Typography

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

function surnameOnly(name: string): string {
  const parts = name.trim().split(/\s+/)
  return parts.length > 1 ? (parts[parts.length - 1] ?? name) : name
}

function remapLineupToFormation(players: Player[], lineupIds: number[], formation: string): number[] {
  const roles = formationSlotRoles(formation)
  const inLineup = lineupIds.filter(Boolean)
  const byPos: Record<GamePosition, Player[]> = { GK: [], DEF: [], MID: [], FWD: [] }

  for (const id of inLineup) {
    const p = players.find((pl) => pl.id === id)
    if (p && p.position in byPos) {
      byPos[p.position as GamePosition].push(p)
    }
  }
  for (const pos of Object.keys(byPos) as GamePosition[]) {
    byPos[pos].sort((a, b) => b.overall - a.overall)
  }

  const used = new Set<number>()
  const remaining = [...inLineup]

  return roles.map((role) => {
    const pool = byPos[role as GamePosition]
    const fromRole = pool.find((p) => !used.has(p.id))
    if (fromRole) {
      used.add(fromRole.id)
      return fromRole.id
    }
    const fallback = remaining.find((id) => id && !used.has(id))
    if (fallback) {
      used.add(fallback)
      return fallback
    }
    return 0
  })
}

type Props = { clubId: number | null; currentMatchday: number }

function PitchSlot({
  index,
  x,
  y,
  player,
  isOver,
  captainPlayerId,
}: {
  index: number
  x: number
  y: number
  player: Player | null
  isOver: boolean
  captainPlayerId: number | null
}) {
  const { setNodeRef, isOver: dropOver } = useDroppable({ id: slotDndId(index) })
  const highlighted = isOver || dropOver

  return (
    <div
      className={`fm-field-slot${highlighted ? ' fm-field-slot--over' : ''}`}
      ref={setNodeRef}
      style={{ left: `${x}%`, top: `${y}%` }}
    >
      {player ? (
        <PitchPlayerChip
          player={player}
          slotIndex={index}
          isCaptain={captainPlayerId === player.id}
        />
      ) : (
        <div className="fm-slot-empty">
          <span className="fm-slot-empty-icon">+</span>
          <span>Слот</span>
        </div>
      )}
    </div>
  )
}

function PitchPlayerChip({
  player,
  slotIndex,
  isCaptain,
}: {
  player: Player
  slotIndex: number
  isCaptain: boolean
}) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: playerDndId(player.id),
    data: { type: 'pitch', slotIndex, playerId: player.id },
  })
  const style = {
    transform: CSS.Translate.toString(transform),
    opacity: isDragging ? 0 : 1,
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="fm-pitch-player"
      {...listeners}
      {...attributes}
    >
      <div className="fm-pitch-avatar-wrap">
        <PlayerOverallWithStats player={player} className="fm-slot-ovr" />
        <PlayerAvatar name={player.name} photoUrl={player.photo_url} size={44} />
      </div>
      <PlayerProfileLink
        playerId={player.id}
        className="fm-slot-name fm-player-profile-link"
        title={`${player.name} (${player.position})`}
      >
        {isCaptain ? <span className="fm-captain-badge">C</span> : null}
        {surnameOnly(player.name)}
        <span className="fm-slot-pos-inline">{player.position}</span>
      </PlayerProfileLink>
    </div>
  )
}

function BenchRow({ player, isCaptain }: { player: Player; isCaptain: boolean }) {
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
      <PlayerAvatar name={player.name} photoUrl={player.photo_url} size={32} />
      <div className="fm-bench-meta">
        <Text className="fm-bench-name" ellipsis title={`${player.name} (${player.position})`}>
          <PlayerProfileLink playerId={player.id} className="fm-player-profile-link fm-bench-name-link">
            {isCaptain ? <span className="fm-captain-badge">C</span> : null}
            <Text strong>{player.name}</Text>
          </PlayerProfileLink>
          <Text type="secondary" className="fm-bench-sub">{player.position}</Text>
        </Text>
      </div>
      <PlayerOverallWithStats player={player} className="fm-bench-ovr" />
      <Tag className="fm-bench-ready">Готов</Tag>
    </div>
  )
}

function DragPreview({ player }: { player: Player }) {
  return (
    <div className="fm-pitch-player fm-pitch-player--overlay">
      <div className="fm-pitch-avatar-wrap">
        <span className="fm-slot-ovr">{player.overall}</span>
        <PlayerAvatar name={player.name} photoUrl={player.photo_url} size={44} />
      </div>
      <Text className="fm-slot-name">{surnameOnly(player.name)}</Text>
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
  const [benchPositionFilter, setBenchPositionFilter] = useState<'ALL' | GamePosition>('ALL')
  const [captainPlayerId, setCaptainPlayerId] = useState<number | null>(null)

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
        setCaptainPlayerId(data.club.captain_player_id ?? null)
        setPlayers(data.players)
        setFormation(data.club.formation)
        setInitialFormation(data.club.formation)
        const total = formationSlotCount(data.club.formation)
        const ids = data.club.lineup_player_ids
        const normalized =
          ids.length === total ? [...ids] : [...ids.slice(0, total), ...Array(Math.max(0, total - ids.length)).fill(0)]
        setSlotIds(normalized)
        setInitialSlotIds(normalized)
        syncBenchOrder(data.players, normalized)
      })
      .finally(() => setLoading(false))
  }, [clubId, syncBenchOrder])

  const pitchSlots = FORMATION_PITCH_SLOTS[formation] ?? FORMATION_PITCH_SLOTS['4-4-2']
  const slotCount = pitchSlots.length

  const onFormationChange = (value: string) => {
    setActiveDragId(null)
    setOverId(null)
    const remapped = remapLineupToFormation(players, slotIds, value)
    setFormation(value)
    setSlotIds(remapped)
    syncBenchOrder(players, remapped)
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

  const filteredBenchPlayers = useMemo(() => {
    if (benchPositionFilter === 'ALL') return benchPlayers
    return benchPlayers.filter((p) => p.position === benchPositionFilter)
  }, [benchPlayers, benchPositionFilter])

  const avgOverall = useMemo(() => {
    const picked = slotIds.map((id) => playerById.get(id)?.overall).filter(Boolean) as number[]
    if (!picked.length) return '—'
    return Math.round(picked.reduce((a, b) => a + b, 0) / picked.length)
  }, [slotIds, playerById])

  const activePlayer = activeDragId ? playerById.get(parsePlayerId(activeDragId) ?? -1) ?? null : null

  const pitchMarkers = pitchSlots.map((slot, idx) => {
    const pid = slotIds[idx]
    const player = pid ? playerById.get(pid) ?? null : null
    const slotOver = overId === slotDndId(idx)
    return (
      <PitchSlot
        key={`${formation}-${slot.id}`}
        index={idx}
        x={slot.x}
        y={pitchSlotDisplayY(slot)}
        player={player}
        isOver={slotOver}
        captainPlayerId={captainPlayerId}
      />
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
        <Row gutter={[18, 18]} className="fm-squad-row" align="stretch">
          <Col xs={24} lg={16} className="fm-squad-col">
            <Card loading={loading} className="fm-pitch-card">
              <Space style={{ marginBottom: 16, width: '100%', justifyContent: 'space-between' }} wrap>
                <Space>
                  <Text type="secondary" style={{ fontSize: 10, fontWeight: 700 }}>СХЕМА</Text>
                  <Select
                    value={formation}
                    options={[...FORMATIONS]}
                    onChange={onFormationChange}
                    style={{ width: 220 }}
                    listHeight={320}
                  />
                </Space>
                <Text type="secondary" style={{ fontSize: 11 }}>
                  Средний рейтинг <Text strong>{avgOverall}</Text>
                </Text>
              </Space>
              <div className="fm-pitch">
                <div className="fm-pitch-halfway" aria-hidden="true" />
                <div className="fm-pitch-circle" aria-hidden="true" />
                <div className="fm-pitch-slots" key={formation}>{pitchMarkers}</div>
              </div>
            </Card>
          </Col>
          <Col xs={24} lg={8} className="fm-squad-col">
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
              <Select
                size="small"
                value={benchPositionFilter}
                options={POSITION_FILTER_OPTIONS}
                onChange={setBenchPositionFilter}
                style={{ width: '100%', marginBottom: 10 }}
                disabled={benchPlayers.length === 0}
              />
              <SortableContext items={benchOrder.map(playerDndId)} strategy={verticalListSortingStrategy}>
                <div className="fm-bench-list">
                  {benchPlayers.length === 0 ? (
                    <Text type="secondary" style={{ fontSize: 12 }}>Все игроки в стартовом составе</Text>
                  ) : filteredBenchPlayers.length === 0 ? (
                    <Text type="secondary" style={{ fontSize: 12 }}>Нет игроков на этой позиции</Text>
                  ) : (
                    filteredBenchPlayers.map((p) => (
                      <BenchRow key={p.id} player={p} isCaptain={captainPlayerId === p.id} />
                    ))
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
