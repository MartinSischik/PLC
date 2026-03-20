import { useEffect, useState } from 'react'
import { RefreshCw } from 'lucide-react'
import type { WeatherLocation } from '../types'
import { fetchWeatherLocations } from '../api'
import { useWeather } from '../hooks/useWeather'
import { LocationSelector } from '../components/LocationSelector'
import { WeatherCard } from '../components/WeatherCard'

export function WeatherPage() {
  const [locations, setLocations] = useState<WeatherLocation[]>([])
  const [selected, setSelected] = useState(0)
  const { data, loading, error, refresh } = useWeather(selected)

  useEffect(() => {
    fetchWeatherLocations().then(setLocations).catch(console.error)
  }, [])

  return (
    <div className="space-y-4 pb-20 pt-4">
      <div className="px-4 flex items-center justify-between">
        <h2 className="text-lg font-bold text-slate-700">Pronóstico</h2>
        <button
          onClick={refresh}
          disabled={loading}
          className="p-2 rounded-lg bg-white border border-slate-200 text-slate-500 active:scale-95 transition-transform disabled:opacity-50"
        >
          <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {locations.length > 0 && (
        <LocationSelector
          locations={locations}
          selected={selected}
          onSelect={setSelected}
        />
      )}

      {loading && (
        <div className="text-center text-slate-400 py-12 text-sm">Cargando...</div>
      )}

      {error && (
        <div className="text-center text-red-500 py-12 text-sm">{error}</div>
      )}

      {data && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 px-4">
          {data.days.map((day, i) => (
            <WeatherCard key={i} day={day} />
          ))}
        </div>
      )}
    </div>
  )
}
