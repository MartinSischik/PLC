import type { SensorReading, Thresholds } from '../types'

const WARN_MARGIN = 5.0

export function computeAlarmLevel(
  sensors: SensorReading[],
  thresholds: Thresholds | null,
): 'green' | 'yellow' | 'red' {
  if (!thresholds) return 'green'

  for (const s of sensors) {
    if (!s.active) continue
    const hasTemp = s.temperature > 0
    const hasHumid = s.humidity > 0
    if (hasTemp && (s.temperature >= thresholds.temp_max || s.temperature <= thresholds.temp_min)) return 'red'
    if (hasHumid && s.humidity >= thresholds.humid_max) return 'red'
    if (hasTemp && (s.temperature >= thresholds.temp_max - WARN_MARGIN || s.temperature <= thresholds.temp_min + WARN_MARGIN)) return 'yellow'
    if (hasHumid && s.humidity >= thresholds.humid_max - WARN_MARGIN) return 'yellow'
  }
  return 'green'
}

const styles = {
  green: 'bg-emerald-500 text-white',
  yellow: 'bg-amber-500 text-white',
  red: 'bg-red-500 text-white animate-pulse',
}

const labels = {
  green: 'SIN ALARMA',
  yellow: 'ADVERTENCIA',
  red: 'ALARMA ACTIVA',
}

export function AlarmBanner({ level }: { level: 'green' | 'yellow' | 'red' }) {
  return (
    <div className={`px-4 py-2 text-center text-sm font-bold ${styles[level]}`}>
      {labels[level]}
    </div>
  )
}
