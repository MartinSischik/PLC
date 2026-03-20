import { useState } from 'react'
import { ShieldCheck, ShieldOff, Settings } from 'lucide-react'
import { postEnableAll } from '../api'
import { ThresholdConfig } from './ThresholdConfig'

export function GlobalControls() {
  const [showConfig, setShowConfig] = useState(false)

  const handle = async (enable: boolean) => {
    const action = enable ? 'HABILITAR' : 'DESHABILITAR'
    if (!confirm(`¿${action} TODOS los motores?`)) return
    const res = await postEnableAll(enable)
    if (!res.ok) {
      alert(`Error: motores fallidos: ${res.failed.join(', ')}`)
    }
  }

  return (
    <>
      <div className="flex gap-2 px-4">
        <button
          onClick={() => handle(true)}
          className="flex-1 flex items-center justify-center gap-1.5 py-2.5 bg-emerald-50 text-emerald-700 rounded-xl text-xs font-bold active:scale-95 transition-transform"
        >
          <ShieldCheck size={16} />
          HAB TODO
        </button>
        <button
          onClick={() => handle(false)}
          className="flex-1 flex items-center justify-center gap-1.5 py-2.5 bg-red-50 text-red-700 rounded-xl text-xs font-bold active:scale-95 transition-transform"
        >
          <ShieldOff size={16} />
          DESH TODO
        </button>
        <button
          onClick={() => setShowConfig(true)}
          className="flex items-center justify-center gap-1.5 px-3 py-2.5 bg-slate-100 text-slate-600 rounded-xl text-xs font-bold active:scale-95 transition-transform"
        >
          <Settings size={16} />
          CONFIG
        </button>
      </div>

      {showConfig && <ThresholdConfig onClose={() => setShowConfig(false)} />}
    </>
  )
}
