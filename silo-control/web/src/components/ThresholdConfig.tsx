import { useEffect, useRef, useState } from 'react'
import { X, Thermometer, Droplets, Cloud, ToggleLeft, ToggleRight } from 'lucide-react'
import { fetchThresholds, postThresholds, fetchWeatherThresholds, postWeatherThresholds } from '../api'
import { useScada } from '../hooks/useScada'

interface Props {
  onClose: () => void
}

export function ThresholdConfig({ onClose }: Props) {
  const { currentWeather } = useScada()

  // Silo thresholds
  const [tempMax, setTempMax] = useState('')
  const [humidMax, setHumidMax] = useState('')

  // Weather thresholds
  const [ambientTempMax, setAmbientTempMax] = useState('')
  const [ambientHumidMax, setAmbientHumidMax] = useState('')
  const [weatherAutoEnabled, setWeatherAutoEnabled] = useState(false)

  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const overlayRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetchThresholds().then((data) => {
      if (data) {
        setTempMax(String(data.temp_max))
        setHumidMax(String(data.humid_max))
      }
    })
    fetchWeatherThresholds().then((data) => {
      setAmbientTempMax(String(data.ambient_temp_max))
      setAmbientHumidMax(String(data.ambient_humid_max))
      setWeatherAutoEnabled(data.weather_auto_enabled)
    })
  }, [])

  const handleSave = async () => {
    const t = parseFloat(tempMax)
    const h = parseFloat(humidMax)
    const at = parseFloat(ambientTempMax)
    const ah = parseFloat(ambientHumidMax)
    if (isNaN(t) || isNaN(h) || isNaN(at) || isNaN(ah)) return
    setSaving(true)
    const [ok1, ok2] = await Promise.all([
      postThresholds(t, h),
      postWeatherThresholds({ ambient_temp_max: at, ambient_humid_max: ah, weather_auto_enabled: weatherAutoEnabled }),
    ])
    setSaving(false)
    if (ok1 && ok2) {
      setSaved(true)
      setTimeout(() => { setSaved(false); onClose() }, 800)
    }
  }

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/40 px-4 pb-4 sm:pb-0"
      onClick={(e) => { if (e.target === overlayRef.current) onClose() }}
    >
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-5 max-h-[85dvh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-slate-800 text-base">Configuración</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={20} />
          </button>
        </div>

        {/* ── Silo thresholds ── */}
        <p className="text-[11px] font-bold text-slate-400 uppercase mb-3">Umbrales de silo</p>
        <div className="space-y-3 mb-5">
          <div>
            <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 mb-1">
              <Thermometer size={14} className="text-orange-400" />
              Temperatura máxima silo (°C)
            </label>
            <input
              type="number"
              step="0.5"
              value={tempMax}
              onChange={(e) => setTempMax(e.target.value)}
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
          </div>
          <div>
            <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 mb-1">
              <Droplets size={14} className="text-blue-400" />
              Humedad máxima silo (%)
            </label>
            <input
              type="number"
              step="1"
              value={humidMax}
              onChange={(e) => setHumidMax(e.target.value)}
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
          </div>
        </div>

        {/* ── Weather thresholds ── */}
        <div className="border-t border-slate-100 pt-4 mb-3">
          <div className="flex items-center justify-between mb-3">
            <p className="text-[11px] font-bold text-slate-400 uppercase flex items-center gap-1.5">
              <Cloud size={12} />
              Control por clima exterior
            </p>
            <button
              onClick={() => setWeatherAutoEnabled(!weatherAutoEnabled)}
              className={`flex items-center gap-1 text-xs font-bold transition-colors ${
                weatherAutoEnabled ? 'text-blue-600' : 'text-slate-400'
              }`}
            >
              {weatherAutoEnabled
                ? <ToggleRight size={22} className="text-blue-500" />
                : <ToggleLeft size={22} />
              }
              {weatherAutoEnabled ? 'ON' : 'OFF'}
            </button>
          </div>

          {/* Current ambient conditions */}
          {currentWeather && (
            <div className="bg-slate-50 rounded-lg px-3 py-2 mb-3 flex gap-4 text-xs">
              <span className="text-slate-500">Exterior ahora:</span>
              <span className="font-bold text-slate-700">
                {currentWeather.temperature != null ? `${currentWeather.temperature.toFixed(1)}°C` : '---'}
              </span>
              <span className="font-bold text-slate-700">
                {currentWeather.humidity != null ? `${currentWeather.humidity}%` : '---'}
              </span>
            </div>
          )}

          <p className="text-[10px] text-slate-400 mb-3">
            Si el clima exterior supera estos límites, los ventiladores en AUTO no arrancan.
          </p>

          <div className="space-y-3">
            <div>
              <label className={`flex items-center gap-1.5 text-xs font-semibold mb-1 ${weatherAutoEnabled ? 'text-slate-500' : 'text-slate-300'}`}>
                <Thermometer size={14} className={weatherAutoEnabled ? 'text-orange-400' : 'text-slate-300'} />
                Temperatura exterior máxima (°C)
              </label>
              <input
                type="number"
                step="0.5"
                value={ambientTempMax}
                onChange={(e) => setAmbientTempMax(e.target.value)}
                disabled={!weatherAutoEnabled}
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:opacity-40 disabled:bg-slate-50"
              />
            </div>
            <div>
              <label className={`flex items-center gap-1.5 text-xs font-semibold mb-1 ${weatherAutoEnabled ? 'text-slate-500' : 'text-slate-300'}`}>
                <Droplets size={14} className={weatherAutoEnabled ? 'text-blue-400' : 'text-slate-300'} />
                Humedad exterior máxima (%)
              </label>
              <input
                type="number"
                step="1"
                value={ambientHumidMax}
                onChange={(e) => setAmbientHumidMax(e.target.value)}
                disabled={!weatherAutoEnabled}
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:opacity-40 disabled:bg-slate-50"
              />
            </div>
          </div>
        </div>

        <button
          onClick={handleSave}
          disabled={saving || saved}
          className="mt-4 w-full py-2.5 rounded-xl text-sm font-bold transition-colors
            bg-blue-600 text-white active:scale-95
            disabled:opacity-60"
        >
          {saved ? '✓ Guardado' : saving ? 'Guardando...' : 'Guardar'}
        </button>
      </div>
    </div>
  )
}
