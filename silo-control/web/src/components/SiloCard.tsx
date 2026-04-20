import { useState } from 'react'
import { ChevronRight, Thermometer, Droplets } from 'lucide-react'
import type { SiloConfig, SensorReading, MotorStatus, GateStatus, Thresholds, QualityStatus } from '../types'
import { QualityBadge } from './QualityBadge'
import { LevelIndicator } from './LevelIndicator'
import { SiloDetail } from './SiloDetail'

interface Props {
  silo: SiloConfig
  siloIndex: number
  sensors: SensorReading[]
  motors: MotorStatus[]
  gates: GateStatus[]
  thresholds: Thresholds | null
  quality: QualityStatus
  motorRuntime: Record<string, number>
}

export function SiloCard({ silo, siloIndex, sensors, motors, gates, thresholds, quality, motorRuntime }: Props) {
  const [detailOpen, setDetailOpen] = useState(false)

  const isCuarentena = quality === 'cuarentena'

  // Compute averages from this silo's sensors
  const siloReadings = silo.sensors.map((sc) => sensors.find((s) => s.index === sc.index))

  const tempReadings = silo.sensors
    .filter((sc) => sc.show_temp)
    .map((sc) => siloReadings.find((r) => r?.index === sc.index))
    .filter((r) => r?.active && (r?.temperature ?? 0) > 0)
    .map((r) => r!.temperature)

  const humReadings = silo.sensors
    .filter((sc) => sc.show_humidity)
    .map((sc) => siloReadings.find((r) => r?.index === sc.index))
    .filter((r) => r?.active && (r?.humidity ?? 0) > 0)
    .map((r) => r!.humidity)

  const avgTemp = tempReadings.length
    ? tempReadings.reduce((a, b) => a + b, 0) / tempReadings.length
    : null

  const avgHumid = humReadings.length
    ? humReadings.reduce((a, b) => a + b, 0) / humReadings.length
    : null

  // Alarm coloring for temperature
  const tempColor = avgTemp == null
    ? 'text-slate-400'
    : thresholds && avgTemp >= thresholds.temp_max
    ? 'text-red-600'
    : thresholds && avgTemp >= thresholds.temp_max - 5
    ? 'text-amber-500'
    : 'text-slate-800'

  const humColor = avgHumid == null
    ? 'text-slate-400'
    : thresholds && avgHumid >= thresholds.humid_max
    ? 'text-red-600'
    : thresholds && avgHumid >= thresholds.humid_max - 10
    ? 'text-amber-500'
    : 'text-slate-800'

  const headerColor = isCuarentena
    ? 'bg-red-700'
    : quality === 'ok'
    ? 'bg-emerald-700'
    : 'bg-accent'

  // Count running motors for this silo
  const runningCount = silo.motors.filter((mc) =>
    motors.find((m) => m.index === mc.index)?.is_running
  ).length
  const totalMotors = silo.motors.length

  return (
    <>
      <div
        className={`bg-surface rounded-2xl overflow-hidden shadow-sm border cursor-pointer hover:shadow-md transition-shadow ${
          isCuarentena ? 'border-red-300' : 'border-slate-200'
        }`}
        onClick={() => setDetailOpen(true)}
      >
        {/* Header */}
        <div className={`${headerColor} px-4 py-2.5 flex items-center justify-between`}>
          <h2 className="text-white font-bold text-sm">{silo.name}</h2>
          <QualityBadge siloIndex={siloIndex} quality={quality} />
        </div>

        {isCuarentena && (
          <div className="bg-red-50 border-b border-red-200 px-3 py-1 text-[10px] font-bold text-red-700 text-center">
            SILO BLOQUEADO
          </div>
        )}

        <div className="p-4 space-y-3">
          {/* Temp + Humidity */}
          <div className="flex gap-3">
            <div className="flex-1 flex items-center gap-2">
              <Thermometer size={18} className={avgTemp != null ? tempColor : 'text-slate-300'} />
              <div>
                <div className={`text-xl font-bold leading-none ${tempColor}`}>
                  {avgTemp != null ? `${avgTemp.toFixed(1)}°` : '---'}
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5">Temperatura</div>
              </div>
            </div>

            <div className="w-px bg-slate-200" />

            <div className="flex-1 flex items-center gap-2">
              <Droplets size={18} className={avgHumid != null ? humColor : 'text-slate-300'} />
              <div>
                <div className={`text-xl font-bold leading-none ${humColor}`}>
                  {avgHumid != null ? `${avgHumid.toFixed(1)}%` : '---'}
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5">Humedad</div>
              </div>
            </div>
          </div>

          {/* Level sensors */}
          {silo.level_sensors.length > 0 && (
            <div className="flex gap-2">
              {silo.level_sensors.map((ls) => (
                <LevelIndicator key={ls.label} config={ls} />
              ))}
            </div>
          )}

          {/* Motor status + More info */}
          <div className="flex items-center justify-between pt-1">
            <div className="text-xs text-slate-400">
              {runningCount > 0
                ? <span className="text-emerald-600 font-medium">{runningCount}/{totalMotors} motores ON</span>
                : <span>{totalMotors} motores OFF</span>
              }
            </div>
            <button
              onClick={(e) => { e.stopPropagation(); setDetailOpen(true) }}
              className="flex items-center gap-1 text-xs font-bold text-accent hover:text-accent/80 transition-colors"
            >
              Más info <ChevronRight size={14} />
            </button>
          </div>
        </div>
      </div>

      {detailOpen && (
        <SiloDetail
          silo={silo}
          siloIndex={siloIndex}
          sensors={sensors}
          motors={motors}
          gates={gates}
          thresholds={thresholds}
          quality={quality}
          motorRuntime={motorRuntime}
          onClose={() => setDetailOpen(false)}
        />
      )}
    </>
  )
}
