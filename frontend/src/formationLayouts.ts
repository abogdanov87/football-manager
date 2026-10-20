/** Absolute pitch coordinates: x/y in %, y=0 attack line, y=100 own goal. Slot order: GK → DEF → MID → FWD (matches API lineup). */

export type PitchRole = 'GK' | 'DEF' | 'MID' | 'FWD'

export type FormationPitchSlot = {
  id: string
  x: number
  y: number
  role: PitchRole
}

const gk = (): FormationPitchSlot => ({ id: 'gk', x: 50, y: 91, role: 'GK' })

const defLine = (y: number, xs: number[]): FormationPitchSlot[] =>
  xs.map((x, i) => ({ id: `def-${i}`, x, y, role: 'DEF' as PitchRole }))

const midLine = (y: number, xs: number[]): FormationPitchSlot[] =>
  xs.map((x, i) => ({ id: `mid-${i}`, x, y, role: 'MID' as PitchRole }))

const fwdLine = (y: number, xs: number[]): FormationPitchSlot[] =>
  xs.map((x, i) => ({ id: `fwd-${i}`, x, y, role: 'FWD' as PitchRole }))

const flat4 = () => [12, 37, 63, 88]

export const FORMATION_PITCH_SLOTS: Record<string, FormationPitchSlot[]> = {
  '4-3-3': [
    gk(),
    ...defLine(78, flat4()),
    ...midLine(52, [25, 50, 75]),
    ...fwdLine(22, [18, 50, 82]),
  ],
  '4-5-1': [
    gk(),
    ...defLine(78, flat4()),
    ...midLine(50, [10, 30, 50, 70, 90]),
    ...fwdLine(20, [50]),
  ],
  '4-4-2': [
    gk(),
    ...defLine(78, flat4()),
    ...midLine(52, [12, 37, 63, 88]),
    ...fwdLine(24, [38, 62]),
  ],
  '4-4-2-d': [
    gk(),
    ...defLine(78, flat4()),
    { id: 'mid-dm', x: 50, y: 62, role: 'MID' },
    ...midLine(48, [15, 85]),
    { id: 'mid-am', x: 50, y: 38, role: 'MID' },
    ...fwdLine(22, [38, 62]),
  ],
  '4-2-3-1': [
    gk(),
    ...defLine(78, flat4()),
    ...midLine(62, [35, 65]),
    ...midLine(42, [18, 50, 82]),
    ...fwdLine(20, [50]),
  ],
  '3-4-3': [
    gk(),
    ...defLine(78, [25, 50, 75]),
    ...midLine(52, [12, 37, 63, 88]),
    ...fwdLine(22, [18, 50, 82]),
  ],
  '3-5-2': [
    gk(),
    ...defLine(78, [25, 50, 75]),
    { id: 'mid-lwb', x: 8, y: 58, role: 'MID' },
    ...midLine(52, [32, 50, 68]),
    { id: 'mid-rwb', x: 92, y: 58, role: 'MID' },
    ...fwdLine(24, [38, 62]),
  ],
  '2-3-5': [
    gk(),
    ...defLine(80, [38, 62]),
    ...midLine(58, [25, 50, 75]),
    ...fwdLine(28, [10, 30, 50, 70, 90]),
  ],
  '4-2-4': [
    gk(),
    ...defLine(78, flat4()),
    ...midLine(58, [38, 62]),
    ...fwdLine(26, [12, 37, 63, 88]),
  ],
  '3-6-1': [
    gk(),
    ...defLine(78, [25, 50, 75]),
    ...midLine(48, [8, 26, 42, 58, 74, 92]),
    ...fwdLine(20, [50]),
  ],
  '2-4-3-1': [
    gk(),
    ...defLine(80, [38, 62]),
    ...midLine(55, [12, 37, 63, 88]),
    ...midLine(38, [18, 50, 82]),
    ...fwdLine(20, [50]),
  ],
  '4-1-4-1': [
    gk(),
    ...defLine(78, flat4()),
    { id: 'mid-dm', x: 50, y: 64, role: 'MID' },
    ...midLine(48, [12, 37, 63, 88]),
    ...fwdLine(20, [50]),
  ],
  '4-3-2-1': [
    gk(),
    ...defLine(78, flat4()),
    ...midLine(58, [25, 50, 75]),
    ...midLine(40, [35, 65]),
    ...fwdLine(18, [50]),
  ],
  '3-2-4-1': [
    gk(),
    ...defLine(78, [25, 50, 75]),
    ...midLine(62, [38, 62]),
    ...midLine(42, [12, 37, 63, 88]),
    ...fwdLine(20, [50]),
  ],
  '4-2-2-2': [
    gk(),
    ...defLine(78, flat4()),
    ...midLine(58, [35, 65]),
    ...midLine(42, [20, 80]),
    ...fwdLine(24, [38, 62]),
  ],
  '4-4-1-1': [
    gk(),
    ...defLine(78, flat4()),
    ...midLine(52, [12, 37, 63, 88]),
    { id: 'mid-ss', x: 50, y: 34, role: 'MID' },
    ...fwdLine(20, [50]),
  ],
  '3-1-3-3': [
    gk(),
    ...defLine(78, [25, 50, 75]),
    { id: 'mid-dm', x: 50, y: 62, role: 'MID' },
    ...midLine(48, [25, 50, 75]),
    ...fwdLine(22, [18, 50, 82]),
  ],
  '3-1-4-2': [
    gk(),
    ...defLine(78, [25, 50, 75]),
    { id: 'mid-dm', x: 50, y: 64, role: 'MID' },
    ...midLine(50, [12, 37, 63, 88]),
    ...fwdLine(24, [38, 62]),
  ],
  '5-4-1': [
    gk(),
    { id: 'def-lwb', x: 8, y: 72, role: 'DEF' },
    ...defLine(78, [28, 50, 72]),
    { id: 'def-rwb', x: 92, y: 72, role: 'DEF' },
    ...midLine(50, [18, 40, 60, 82]),
    ...fwdLine(20, [50]),
  ],
  '4-1-3-2': [
    gk(),
    ...defLine(78, flat4()),
    { id: 'mid-dm', x: 50, y: 62, role: 'MID' },
    ...midLine(46, [22, 50, 78]),
    ...fwdLine(24, [38, 62]),
  ],
}

export function formationSlotRoles(formation: string): PitchRole[] {
  const slots = FORMATION_PITCH_SLOTS[formation] ?? FORMATION_PITCH_SLOTS['4-4-2']
  return slots.map((s) => s.role)
}

export function formationSlotCount(formation: string): number {
  return (FORMATION_PITCH_SLOTS[formation] ?? FORMATION_PITCH_SLOTS['4-4-2']).length
}

/** Legacy row counts derived from pitch slots (GK/DEF/MID/FWD lines). */
export function slotLayoutFromPitch(formation: string): number[] {
  const slots = FORMATION_PITCH_SLOTS[formation] ?? FORMATION_PITCH_SLOTS['4-4-2']
  const counts: Record<PitchRole, number> = { GK: 0, DEF: 0, MID: 0, FWD: 0 }
  for (const s of slots) counts[s.role] += 1
  return [counts.GK, counts.DEF, counts.MID, counts.FWD]
}
