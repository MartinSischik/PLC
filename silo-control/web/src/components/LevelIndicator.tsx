import { ArrowUp, ArrowDown } from 'lucide-react'
import type { LevelSensorConfig } from '../types'

interface Props {
  config: LevelSensorConfig
  active?: boolean // In simulation, always show as inactive/unknown
}

export function LevelIndicator({ config, active }: Props) {
  const isHigh = config.sensor_type === 'hl'
  const Icon = isHigh ? ArrowUp : ArrowDown

  return (
    <div className={`flex-1 rounded-lg px-3 py-2 text-center border ${
      active
        ? isHigh
          ? 'bg-red-50 border-red-200 text-red-700'
          : 'bg-amber-50 border-amber-200 text-amber-700'
        : 'bg-slate-50 border-slate-200 text-slate-400'
    }`}>
      <div className="flex items-center justify-center gap-1">
        <Icon size={14} />
        <span className="text-[10px] font-bold">{config.label}</span>
      </div>
      <div className="text-[10px] mt-0.5">
        {active ? (isHigh ? 'ALTO' : 'BAJO') : '---'}
      </div>
    </div>
  )
}
