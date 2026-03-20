import { useEffect, useRef, useState } from 'react'
import { X, Thermometer, Droplets } from 'lucide-react'
import { fetchThresholds, postThresholds } from '../api'

interface Props {
  onClose: () => void
}

export function ThresholdConfig({ onClose }: Props) {
  const [tempMax, setTempMax] = useState('')
  const [humidMax, setHumidMax] = useState('')
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
  }, [])

  const handleSave = async () => {
    const t = parseFloat(tempMax)
    const h = parseFloat(humidMax)
    if (isNaN(t) || isNaN(h)) return
    setSaving(true)
    const ok = await postThresholds(t, h)
    setSaving(false)
    if (ok) {
      setSaved(true)
      setTimeout(() => { setSaved(false); onClose() }, 800)
    }
  }

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
      onClick={(e) => { if (e.target === overlayRef.current) onClose() }}
    >
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-xs p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-slate-800 text-base">Umbrales de alarma</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={20} />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 mb-1">
              <Thermometer size={14} className="text-orange-400" />
              Temperatura máxima (°C)
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
              Humedad máxima (%)
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

        <button
          onClick={handleSave}
          disabled={saving || saved}
          className="mt-5 w-full py-2.5 rounded-xl text-sm font-bold transition-colors
            bg-blue-600 text-white active:scale-95
            disabled:opacity-60"
        >
          {saved ? '✓ Guardado' : saving ? 'Guardando...' : 'Guardar'}
        </button>
      </div>
    </div>
  )
}
