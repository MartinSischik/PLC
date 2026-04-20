import type { GateConfig, GateStatus } from '../types'
import { postGateAction } from '../api'

interface Props {
  config: GateConfig
  status?: GateStatus
}

export function GateControl({ config, status }: Props) {
  const s = status ?? {
    index: config.index,
    cmd_open: false,
    cmd_close: false,
    is_open: false,
    is_closed: false,
    in_motion: false,
    fault: false,
  }

  const stateText = s.in_motion
    ? 'MOVIENDO'
    : s.is_open
    ? 'ABIERTA'
    : s.is_closed
    ? 'CERRADA'
    : '---'

  const stateColor = s.in_motion
    ? 'text-amber-600'
    : s.is_open
    ? 'text-emerald-600'
    : s.is_closed
    ? 'text-slate-500'
    : 'text-slate-400'

  const typeLabel =
    config.gate_type === 'distribucion'
      ? 'DIST'
      : config.gate_type === 'descarga_lateral'
      ? 'D.LAT'
      : 'DESC'

  return (
    <div className="bg-white rounded-lg p-3 space-y-2">
      <div className="flex items-center gap-2">
        <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-purple-100 text-purple-700">
          {typeLabel}
        </span>
        <span className="text-sm font-medium text-slate-700 flex-1 truncate">
          {config.label || `Compuerta ${config.index}`}
        </span>
        <span className={`text-xs font-bold ${stateColor}`}>{stateText}</span>
        {s.fault && (
          <span className="text-xs font-bold text-red-600">FALLA</span>
        )}
      </div>

      <div className="flex gap-2">
        <button
          onClick={() => postGateAction(config.index, 'open')}
          disabled={s.is_open && !s.in_motion}
          className="flex-1 py-2 rounded-lg text-xs font-bold transition-colors active:scale-95 bg-emerald-100 text-emerald-700 disabled:opacity-40"
        >
          ABRIR
        </button>
        <button
          onClick={() => postGateAction(config.index, 'stop')}
          className="flex-1 py-2 rounded-lg text-xs font-bold transition-colors active:scale-95 bg-amber-100 text-amber-700"
        >
          STOP
        </button>
        <button
          onClick={() => postGateAction(config.index, 'close')}
          disabled={s.is_closed && !s.in_motion}
          className="flex-1 py-2 rounded-lg text-xs font-bold transition-colors active:scale-95 bg-red-100 text-red-700 disabled:opacity-40"
        >
          CERRAR
        </button>
      </div>
    </div>
  )
}
