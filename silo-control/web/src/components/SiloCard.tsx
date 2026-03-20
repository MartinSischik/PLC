import type { SiloConfig, SensorReading, MotorStatus, Thresholds } from '../types'
import { SensorTile } from './SensorTile'
import { MotorControl } from './MotorControl'

interface Props {
  silo: SiloConfig
  sensors: SensorReading[]
  motors: MotorStatus[]
  thresholds: Thresholds | null
}

export function SiloCard({ silo, sensors, motors, thresholds }: Props) {
  const sensorMap = new Map(sensors.map((s) => [s.index, s]))
  const motorMap = new Map(motors.map((m) => [m.index, m]))

  return (
    <div className="bg-surface rounded-2xl overflow-hidden shadow-sm border border-slate-200">
      {/* Header */}
      <div className="bg-accent px-4 py-2.5">
        <h2 className="text-white font-bold text-sm">{silo.name}</h2>
      </div>

      <div className="p-3 space-y-3">
        {/* Sensors */}
        {silo.sensors.length > 0 && (
          <div className="flex gap-2">
            {silo.sensors.map((sc) => (
              <SensorTile
                key={sc.index}
                config={sc}
                reading={sensorMap.get(sc.index)}
                thresholds={thresholds}
              />
            ))}
          </div>
        )}

        {/* Motors */}
        {silo.motors.map((mc) => (
          <MotorControl
            key={mc.index}
            config={mc}
            status={motorMap.get(mc.index)}
          />
        ))}
      </div>
    </div>
  )
}
