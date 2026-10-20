import {
  FORMATION_PITCH_SLOTS,
  formationSlotCount,
  formationSlotRoles,
  slotLayoutFromPitch,
  type FormationPitchSlot,
  type PitchRole,
} from './formationLayouts'

export {
  FORMATION_PITCH_SLOTS,
  formationSlotCount,
  formationSlotRoles,
  type FormationPitchSlot,
  type PitchRole,
}

/** Tactical schemes from https://t-j.ru/football-tactics/ — GK/DEF/MID/FWD slot counts. */
export const FORMATIONS = [
  { value: '4-3-3', label: '4-3-3' },
  { value: '4-5-1', label: '4-5-1' },
  { value: '4-4-2', label: '4-4-2' },
  { value: '4-4-2-d', label: '4-4-2 с ромбом' },
  { value: '4-2-3-1', label: '4-2-3-1' },
  { value: '3-4-3', label: '3-4-3' },
  { value: '3-5-2', label: '3-5-2' },
  { value: '2-3-5', label: '2-3-5 (устаревшая)' },
  { value: '4-2-4', label: '4-2-4 (устаревшая)' },
  { value: '3-6-1', label: '3-6-1' },
  { value: '2-4-3-1', label: '2-4-3-1' },
  { value: '4-1-4-1', label: '4-1-4-1' },
  { value: '4-3-2-1', label: '4-3-2-1 (ёлочка)' },
  { value: '3-2-4-1', label: '3-2-4-1' },
  { value: '4-2-2-2', label: '4-2-2-2' },
  { value: '4-4-1-1', label: '4-4-1-1' },
  { value: '3-1-3-3', label: '3-1-3-3' },
  { value: '3-1-4-2', label: '3-1-4-2' },
  { value: '5-4-1', label: '5-4-1' },
  { value: '4-1-3-2', label: '4-1-3-2' },
] as const

/** @deprecated Prefer FORMATION_PITCH_SLOTS; kept for tests and row-count checks. */
export const SLOT_LAYOUTS: Record<string, number[]> = Object.fromEntries(
  FORMATIONS.map((f) => [f.value, slotLayoutFromPitch(f.value)]),
)
