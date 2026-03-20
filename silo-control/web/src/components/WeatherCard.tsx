import { Sun, Cloud, CloudRain, CloudSnow, CloudLightning, Tornado } from 'lucide-react'
import type { ForecastDay } from '../types'

const iconMap: Record<string, typeof Sun> = {
  sunny: Sun,
  partly_cloudy: Cloud,
  cloudy: Cloud,
  rain: CloudRain,
  snow: CloudSnow,
  storm: Tornado,
  thunderstorm: CloudLightning,
}

function tempColor(t: number | null): string {
  if (t === null) return 'text-slate-400'
  if (t >= 35) return 'text-red-500'
  if (t <= 10) return 'text-blue-500'
  return 'text-emerald-600'
}

export function WeatherCard({ day }: { day: ForecastDay }) {
  const Icon = iconMap[day.icon_name] ?? Cloud

  return (
    <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-200 space-y-2">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-sm font-bold text-slate-700">{day.day_name ?? '---'}</div>
          <div className="text-[10px] text-slate-400">
            {day.date ? new Date(day.date).toLocaleDateString('es-CR') : ''}
          </div>
        </div>
        <Icon size={32} className="text-accent2" />
      </div>

      <div className="flex items-center gap-4">
        <div>
          <span className="text-xs text-slate-400">Max </span>
          <span className={`text-lg font-bold ${tempColor(day.temp_max)}`}>
            {day.temp_max !== null ? `${day.temp_max}°` : '--'}
          </span>
        </div>
        <div>
          <span className="text-xs text-slate-400">Min </span>
          <span className={`text-lg font-bold ${tempColor(day.temp_min)}`}>
            {day.temp_min !== null ? `${day.temp_min}°` : '--'}
          </span>
        </div>
        {day.precipitation_mm !== null && day.precipitation_mm > 0 && (
          <div className="text-xs text-blue-500 font-medium">
            💧 {day.precipitation_mm} mm
          </div>
        )}
      </div>

      {day.narrative && (
        <p className="text-xs text-slate-500 leading-relaxed">{day.narrative}</p>
      )}
    </div>
  )
}
