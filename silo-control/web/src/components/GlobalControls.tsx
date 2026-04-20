import { useState } from 'react'
import { ShieldCheck, ShieldOff, Settings, PlayCircle, StopCircle } from 'lucide-react'
import { postEnableAll, postAutoAll } from '../api'
import { ThresholdConfig } from './ThresholdConfig'

export function GlobalControls() {
  const [showConfig, setShowConfig] = useState(false)

  const handleEnable = async (enable: boolean) => {
    const action = enable ? 'HABILITAR' : 'DESHABILITAR'
    if (!confirm(`¿${action} TODOS los motores?`)) return
    const res = await postEnableAll(enable)
    if (!res.ok) alert(`Error motores: ${res.failed.join(', ')}`)
  }

  const handleAuto = async (auto: boolean) => {
    const action = auto ? 'poner en AUTO' : 'poner en MANUAL'
    if (!confirm(`¿${action} TODOS los motores?`)) return
    const res = await postAutoAll(auto)
    if (!res.ok) alert(`Error motores: ${res.failed.join(', ')}`)
  }

  return (
    <>
      <div className="flex gap-2 px-4">
        <button
          onClick={() => handleEnable(true)}
          className="flex-1 flex items-center justify-center gap-1 py-2.5 bg-emerald-50 text-emerald-700 rounded-xl text-xs font-bold active:scale-95 transition-transform"
        >
          <ShieldCheck size={15} />
          HAB
        </button>
        <button
          onClick={() => handleEnable(false)}
          className="flex-1 flex items-center justify-center gap-1 py-2.5 bg-red-50 text-red-700 rounded-xl text-xs font-bold active:scale-95 transition-transform"
        >
          <ShieldOff size={15} />
          DESH
        </button>
        <button
          onClick={() => handleAuto(true)}
          className="flex-1 flex items-center justify-center gap-1 py-2.5 bg-blue-50 text-blue-700 rounded-xl text-xs font-bold active:scale-95 transition-transform"
        >
          <PlayCircle size={15} />
          AUTO
        </button>
        <button
          onClick={() => handleAuto(false)}
          className="flex-1 flex items-center justify-center gap-1 py-2.5 bg-amber-50 text-amber-700 rounded-xl text-xs font-bold active:scale-95 transition-transform"
        >
          <StopCircle size={15} />
          MANUAL
        </button>
        <button
          onClick={() => setShowConfig(true)}
          className="flex items-center justify-center gap-1 px-3 py-2.5 bg-slate-100 text-slate-600 rounded-xl text-xs font-bold active:scale-95 transition-transform"
        >
          <Settings size={15} />
        </button>
      </div>

      {showConfig && <ThresholdConfig onClose={() => setShowConfig(false)} />}
    </>
  )
}
