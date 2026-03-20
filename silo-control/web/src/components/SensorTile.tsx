import type { SensorConfig, SensorReading, Thresholds } from '../types'

const WARN_MARGIN = 5.0

interface Props {
  config: SensorConfig
  reading?: SensorReading
  thresholds: Thresholds | null
}

export function SensorTile({ config, reading, thresholds }: Props) {
  if (!reading || !reading.active) {
    return (
      <div className="bg-slate-100 rounded-xl p-3 text-center flex-1 min-w-[120px]">
        <div className="text-xs text-slate-400 mb-1">{config.label}</div>
        <div className="text-2xl font-bold text-slate-300">---</div>
        <div className="text-[10px] text-slate-400">INACTIVO</div>
      </div>
    )
  }

  const isHum = config.show_humidity
  const value = isHum ? reading.humidity : reading.temperature
  const unit = isHum ? '%' : '°C'
  const label = isHum ? 'humedad' : 'temperatura'

  let bg = 'bg-ok'
  if (thresholds) {
    if (isHum) {
      if (value >= thresholds.humid_max) bg = 'bg-alarm'
      else if (value >= thresholds.humid_max - WARN_MARGIN) bg = 'bg-warn'
    } else {
      if (value >= thresholds.temp_max || value <= thresholds.temp_min) bg = 'bg-alarm'
      else if (
        value >= thresholds.temp_max - WARN_MARGIN ||
        value <= thresholds.temp_min + WARN_MARGIN
      )
        bg = 'bg-warn'
    }
  }

  return (
    <div className={`${bg} rounded-xl p-3 text-center flex-1 min-w-[120px]`}>
      <div className="flex items-center justify-center gap-1.5 mb-1">
        <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
        <span className="text-xs text-slate-500">{config.label}</span>
      </div>
      <div className="text-2xl font-bold text-slate-800">
        {value.toFixed(1)}{unit}
      </div>
      <div className="text-[10px] text-slate-500">{label}</div>
    </div>
  )
}
