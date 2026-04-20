import { RefreshCw, Droplets } from 'lucide-react'
import { useWeather } from '../hooks/useWeather'
import { WeatherCard } from '../components/WeatherCard'

export function WeatherPage() {
  // Location 0 = Limon (now the only location)
  const { data, loading, error, refresh } = useWeather(0)

  return (
    <div className="space-y-4 pb-20 pt-4">
      <div className="px-4 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-slate-700">Clima - Limon</h2>
          <p className="text-[10px] text-slate-400">Variable de control para humedad relativa</p>
        </div>
        <button
          onClick={refresh}
          disabled={loading}
          className="p-2 rounded-lg bg-white border border-slate-200 text-slate-500 active:scale-95 transition-transform disabled:opacity-50"
        >
          <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {/* Current humidity summary */}
      {data && data.days.length > 0 && (
        <div className="mx-4 bg-blue-50 rounded-xl p-4 border border-blue-100">
          <div className="flex items-center gap-2 mb-2">
            <Droplets size={18} className="text-blue-600" />
            <span className="text-sm font-bold text-blue-800">Humedad Relativa Hoy</span>
          </div>
          <div className="flex gap-6">
            <div>
              <span className="text-[10px] text-blue-500 uppercase">Dia</span>
              <div className="text-2xl font-bold text-blue-700">
                {data.days[0].humidity_day !== null ? `${data.days[0].humidity_day}%` : '--'}
              </div>
            </div>
            <div>
              <span className="text-[10px] text-blue-500 uppercase">Noche</span>
              <div className="text-2xl font-bold text-blue-700">
                {data.days[0].humidity_night !== null ? `${data.days[0].humidity_night}%` : '--'}
              </div>
            </div>
          </div>
        </div>
      )}

      {loading && !data && (
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
