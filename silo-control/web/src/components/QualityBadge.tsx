import { useState } from 'react'
import type { QualityStatus } from '../types'
import { postQuality } from '../api'

interface Props {
  siloIndex: number
  quality: QualityStatus
}

const STATUS_CONFIG: Record<QualityStatus, { label: string; bg: string }> = {
  libre: { label: 'LIBRE', bg: 'bg-slate-500' },
  ok: { label: 'OK', bg: 'bg-emerald-500' },
  cuarentena: { label: 'CUARENTENA', bg: 'bg-red-500' },
}

const OPTIONS: QualityStatus[] = ['libre', 'ok', 'cuarentena']

export function QualityBadge({ siloIndex, quality }: Props) {
  const [open, setOpen] = useState(false)
  const cfg = STATUS_CONFIG[quality] ?? STATUS_CONFIG.libre

  async function handleSelect(status: QualityStatus) {
    setOpen(false)
    await postQuality(siloIndex, status)
  }

  return (
    <div className="relative">
      <button
        onClick={(e) => { e.stopPropagation(); setOpen(!open) }}
        className={`${cfg.bg} text-white text-[10px] font-bold px-2 py-0.5 rounded-full active:scale-95 transition-transform`}
      >
        {cfg.label}
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-8 z-50 bg-white rounded-lg shadow-lg border border-slate-200 overflow-hidden min-w-[120px]">
            {OPTIONS.map((opt) => (
              <button
                key={opt}
                onClick={() => handleSelect(opt)}
                className={`block w-full text-left px-3 py-2 text-xs font-medium hover:bg-slate-50 ${
                  opt === quality ? 'bg-slate-100 font-bold' : ''
                } ${opt === 'cuarentena' ? 'text-red-600' : opt === 'ok' ? 'text-emerald-600' : 'text-slate-600'}`}
              >
                {STATUS_CONFIG[opt].label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
