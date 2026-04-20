import { useEffect } from 'react'
import { X, Wind, Fan, Trash2, DoorOpen } from 'lucide-react'
import type { SiloConfig, SensorReading, MotorStatus, GateStatus, Thresholds, QualityStatus } from '../types'
import { SensorTile } from './SensorTile'
import { MotorControl } from './MotorControl'
import { GateControl } from './GateControl'
import { LevelIndicator } from './LevelIndicator'
import { QualityBadge } from './QualityBadge'

interface Props {
  silo: SiloConfig
  siloIndex: number
  sensors: SensorReading[]
  motors: MotorStatus[]
  gates: GateStatus[]
  thresholds: Thresholds | null
  quality: QualityStatus
  motorRuntime: Record<string, number>
  onClose: () => void
}

export function SiloDetail({
  silo, siloIndex, sensors, motors, gates, thresholds, quality, motorRuntime, onClose,
}: Props) {
  const sensorMap = new Map(sensors.map((s) => [s.index, s]))
  const motorMap  = new Map(motors.map((m) => [m.index, m]))
  const gateMap   = new Map(gates.map((g) => [g.index, g]))

  const isCuarentena = quality === 'cuarentena'

  const siloFans   = silo.motors.filter((m) => m.motor_type === 'silo_fan')
  const rfans      = silo.motors.filter((m) => m.motor_type === 'rfan')
  const barredoras = silo.motors.filter((m) => m.motor_type === 'barredora')

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  // Prevent body scroll while open
  useEffect(() => {
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = '' }
  }, [])

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/40 z-50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Sheet — slides up from bottom */}
      <div className="fixed inset-x-0 bottom-0 z-50 max-h-[90dvh] flex flex-col rounded-t-2xl bg-slate-100 shadow-2xl animate-slide-up">

        {/* Header */}
        <div className={`flex items-center justify-between px-4 py-3 rounded-t-2xl ${
          isCuarentena ? 'bg-red-700' : quality === 'ok' ? 'bg-emerald-700' : 'bg-accent'
        }`}>
          <h2 className="text-white font-bold text-base">{silo.name}</h2>
          <div className="flex items-center gap-3">
            <QualityBadge siloIndex={siloIndex} quality={quality} />
            <button onClick={onClose} className="text-white/80 hover:text-white transition-colors">
              <X size={20} />
            </button>
          </div>
        </div>

        {isCuarentena && (
          <div className="bg-red-50 border-b border-red-200 px-4 py-1.5 text-xs font-bold text-red-700 text-center">
            CUARENTENA — SILO BLOQUEADO
          </div>
        )}

        {/* Scrollable content */}
        <div className={`overflow-y-auto flex-1 p-4 space-y-4 pb-24 ${
          isCuarentena ? 'opacity-50 pointer-events-none' : ''
        }`}>

          {/* Level sensors */}
          {silo.level_sensors.length > 0 && (
            <section>
              <SectionTitle label="Nivel" />
              <div className="flex gap-2">
                {silo.level_sensors.map((ls) => (
                  <LevelIndicator key={ls.label} config={ls} />
                ))}
              </div>
            </section>
          )}

          {/* Sensors */}
          {silo.sensors.length > 0 && (
            <section>
              <SectionTitle label="Sensores" />
              <div className="flex gap-2 flex-wrap">
                {silo.sensors.map((sc) => (
                  <SensorTile
                    key={sc.index}
                    config={sc}
                    reading={sensorMap.get(sc.index)}
                    thresholds={thresholds}
                  />
                ))}
              </div>
            </section>
          )}

          {/* Silo Fans */}
          {siloFans.length > 0 && (
            <section>
              <SectionTitle label="Ventiladores" icon={<Fan size={13} />} />
              <div className="space-y-2">
                {siloFans.map((mc) => (
                  <MotorControl
                    key={mc.index}
                    config={mc}
                    status={motorMap.get(mc.index)}
                    runtimeHours={motorRuntime[String(mc.index)]}
                  />
                ))}
              </div>
            </section>
          )}

          {/* RFANs */}
          {rfans.length > 0 && (
            <section>
              <SectionTitle label="Extractores" icon={<Wind size={13} />} />
              <div className="space-y-2">
                {rfans.map((mc) => (
                  <MotorControl
                    key={mc.index}
                    config={mc}
                    status={motorMap.get(mc.index)}
                    runtimeHours={motorRuntime[String(mc.index)]}
                  />
                ))}
              </div>
            </section>
          )}

          {/* Barredoras */}
          {barredoras.length > 0 && (
            <section>
              <SectionTitle label="Barredora" icon={<Trash2 size={13} />} />
              <div className="space-y-2">
                {barredoras.map((mc) => (
                  <MotorControl
                    key={mc.index}
                    config={mc}
                    status={motorMap.get(mc.index)}
                    runtimeHours={motorRuntime[String(mc.index)]}
                  />
                ))}
              </div>
            </section>
          )}

          {/* Gates */}
          {silo.gates.length > 0 && (
            <section>
              <SectionTitle label="Compuertas" icon={<DoorOpen size={13} />} />
              <div className="space-y-2">
                {silo.gates.map((gc) => (
                  <GateControl
                    key={gc.index}
                    config={gc}
                    status={gateMap.get(gc.index)}
                  />
                ))}
              </div>
            </section>
          )}
        </div>
      </div>
    </>
  )
}

function SectionTitle({ label, icon }: { label: string; icon?: React.ReactNode }) {
  return (
    <div className="flex items-center gap-1.5 text-[11px] font-bold text-slate-400 uppercase mb-2">
      {icon}
      {label}
    </div>
  )
}
