import type { MotorConfig, MotorStatus } from '../types'
import { postMotorAction } from '../api'

interface Props {
  config: MotorConfig
  status?: MotorStatus
}

export function MotorControl({ config, status }: Props) {
  const s = status ?? {
    index: config.index,
    cmd_run: false,
    is_running: false,
    auto_mode: false,
    enabled: false,
    fault: false,
  }

  const isVFD = config.motor_type === 'vfd'

  const send = async (action: 'command' | 'auto' | 'enabled', value: boolean) => {
    await postMotorAction(config.index, action, value)
  }

  return (
    <div className="bg-white rounded-lg p-3 space-y-2">
      {/* Header row */}
      <div className="flex items-center gap-2 flex-wrap">
        <span
          className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
            isVFD
              ? 'bg-pink-100 text-pink-700'
              : 'bg-blue-100 text-blue-700'
          }`}
        >
          {isVFD ? 'VFD' : 'SS'}
        </span>
        <span className="text-sm font-medium text-slate-700 flex-1 truncate">
          {config.label || `Motor ${config.index}`}
        </span>
        <span
          className={`text-xs font-bold ${
            s.is_running ? 'text-emerald-600' : 'text-slate-400'
          }`}
        >
          {s.is_running ? 'ON' : 'OFF'}
        </span>
        <span
          className={`text-xs font-bold ${
            s.enabled ? 'text-emerald-600' : 'text-red-600'
          }`}
        >
          {s.enabled ? 'HAB' : 'DESH'}
        </span>
        <span
          className={`text-xs font-bold ${
            s.fault ? 'text-red-600' : 'text-emerald-600'
          }`}
        >
          {s.fault ? 'FALLA' : 'OK'}
        </span>
      </div>

      {/* Buttons */}
      <div className="flex gap-2">
        <button
          onClick={() => send('auto', !s.auto_mode)}
          className={`flex-1 py-2.5 rounded-lg text-xs font-bold transition-colors active:scale-95 ${
            s.auto_mode
              ? 'bg-blue-100 text-blue-700'
              : 'bg-amber-100 text-amber-700'
          }`}
        >
          {s.auto_mode ? 'AUTO' : 'MANUAL'}
        </button>
        <button
          onClick={() => send('command', !s.is_running)}
          className={`flex-1 py-2.5 rounded-lg text-xs font-bold transition-colors active:scale-95 ${
            s.is_running
              ? 'bg-red-100 text-red-700'
              : 'bg-emerald-100 text-emerald-700'
          }`}
        >
          {s.is_running ? 'STOP' : 'START'}
        </button>
        <button
          onClick={() => send('enabled', !s.enabled)}
          className={`flex-1 py-2.5 rounded-lg text-xs font-bold transition-colors active:scale-95 ${
            s.enabled
              ? 'bg-slate-100 text-slate-600'
              : 'bg-red-100 text-red-700'
          }`}
        >
          {s.enabled ? 'DESH' : 'HAB'}
        </button>
      </div>
    </div>
  )
}
