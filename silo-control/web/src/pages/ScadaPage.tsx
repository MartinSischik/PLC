import { useEffect, useState } from 'react'
import type { SiloConfig } from '../types'
import { fetchConfig } from '../api'
import { useScada } from '../hooks/useScada'
import { AlarmBanner, computeAlarmLevel } from '../components/AlarmBanner'
import { GlobalControls } from '../components/GlobalControls'
import { SiloCard } from '../components/SiloCard'

export function ScadaPage() {
  const [silos, setSilos] = useState<SiloConfig[]>([])
  const { sensors, motors, thresholds } = useScada()

  useEffect(() => {
    fetchConfig().then(setSilos).catch(console.error)
  }, [])

  const alarmLevel = computeAlarmLevel(sensors, thresholds)

  return (
    <div className="space-y-3 pb-20">
      <AlarmBanner level={alarmLevel} />
      <GlobalControls />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 px-4">
        {silos.map((silo) => (
          <SiloCard
            key={silo.name}
            silo={silo}
            sensors={sensors}
            motors={motors}
            thresholds={thresholds}
          />
        ))}
      </div>

      {silos.length === 0 && (
        <div className="text-center text-slate-400 py-12 text-sm">
          Cargando configuración...
        </div>
      )}
    </div>
  )
}
