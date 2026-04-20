import { useEffect, useState } from 'react'
import { Thermometer, Droplets } from 'lucide-react'
import type { SiloConfig, QualityStatus } from '../types'
import { fetchConfig } from '../api'
import { useScada } from '../hooks/useScada'
import { AlarmBanner, computeAlarmLevel } from '../components/AlarmBanner'
import { GlobalControls } from '../components/GlobalControls'
import { SiloCard } from '../components/SiloCard'

export function ScadaPage() {
  const [silos, setSilos] = useState<SiloConfig[]>([])
  const { sensors, motors, gates, thresholds, quality, motorRuntime, currentWeather } = useScada()

  useEffect(() => {
    fetchConfig().then(setSilos).catch(console.error)
  }, [])

  const alarmLevel = computeAlarmLevel(sensors, thresholds)

  return (
    <div className="space-y-3 pb-20">
      <AlarmBanner level={alarmLevel} />

      <GlobalControls />

      {/* Ambient weather card */}
      <div className="mx-4 bg-white rounded-xl border border-slate-200 shadow-sm px-4 py-2.5 flex items-center gap-4">
        <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wide flex-shrink-0">
          Exterior Limón
        </span>
        <div className="flex items-center gap-1.5">
          <Thermometer size={15} className="text-orange-400 flex-shrink-0" />
          <span className="text-sm font-bold text-slate-700">
            {currentWeather?.temperature != null ? `${currentWeather.temperature.toFixed(1)}°C` : '---'}
          </span>
        </div>
        <div className="w-px h-4 bg-slate-200" />
        <div className="flex items-center gap-1.5">
          <Droplets size={15} className="text-blue-400 flex-shrink-0" />
          <span className="text-sm font-bold text-slate-700">
            {currentWeather?.humidity != null ? `${currentWeather.humidity}%` : '---'}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 px-4">
        {silos.map((silo, idx) => (
          <SiloCard
            key={silo.name}
            silo={silo}
            siloIndex={idx}
            sensors={sensors}
            motors={motors}
            gates={gates}
            thresholds={thresholds}
            quality={(quality[String(idx)] as QualityStatus) ?? 'libre'}
            motorRuntime={motorRuntime}
          />
        ))}
      </div>

      {silos.length === 0 && (
        <div className="text-center text-slate-400 py-12 text-sm">
          Cargando configuracion...
        </div>
      )}
    </div>
  )
}
