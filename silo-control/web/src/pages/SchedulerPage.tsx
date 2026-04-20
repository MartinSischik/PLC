import { useEffect, useState } from 'react'
import { Plus, Trash2, Clock, CheckCircle } from 'lucide-react'
import type { ScheduledAction, SiloConfig } from '../types'
import { fetchConfig, fetchSchedule, createScheduledAction, deleteScheduledAction } from '../api'

const ACTION_TYPES = [
  { value: 'motor', label: 'Motor' },
  { value: 'ventilador', label: 'Ventilador' },
  { value: 'compuerta', label: 'Compuerta' },
]

export function SchedulerPage() {
  const [actions, setActions] = useState<ScheduledAction[]>([])
  const [silos, setSilos] = useState<SiloConfig[]>([])
  const [showForm, setShowForm] = useState(false)

  // Form
  const [fSilo, setFSilo] = useState(0)
  const [fType, setFType] = useState('motor')
  const [fTarget, setFTarget] = useState(0)
  const [fStart, setFStart] = useState('')
  const [fDuration, setFDuration] = useState(60)

  const load = () => {
    fetchSchedule().then(setActions).catch(console.error)
  }

  useEffect(() => {
    fetchConfig().then(setSilos).catch(console.error)
    load()
  }, [])

  async function handleCreate() {
    await createScheduledAction(fSilo, fType, fTarget, fStart, fDuration)
    setShowForm(false)
    load()
  }

  async function handleDelete(id: number) {
    await deleteScheduledAction(id)
    load()
  }

  // Get motors for selected silo
  const selectedSilo = silos[fSilo]
  const targets = selectedSilo?.motors ?? []

  return (
    <div className="space-y-4 pb-20 pt-4">
      <div className="px-4 flex items-center justify-between">
        <h2 className="text-lg font-bold text-slate-700">Programador</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-accent text-white text-xs font-bold active:scale-95 transition-transform"
        >
          <Plus size={14} /> Programar
        </button>
      </div>

      {/* Create form */}
      {showForm && (
        <div className="mx-4 bg-white rounded-xl p-4 border border-slate-200 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[10px] font-bold text-slate-500 uppercase">Silo</label>
              <select
                value={fSilo}
                onChange={(e) => setFSilo(Number(e.target.value))}
                className="w-full mt-1 px-3 py-2 rounded-lg border border-slate-200 text-sm"
              >
                {silos.map((s, i) => (
                  <option key={i} value={i}>{s.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-[10px] font-bold text-slate-500 uppercase">Tipo</label>
              <select
                value={fType}
                onChange={(e) => setFType(e.target.value)}
                className="w-full mt-1 px-3 py-2 rounded-lg border border-slate-200 text-sm"
              >
                {ACTION_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[10px] font-bold text-slate-500 uppercase">Motor/Target</label>
              <select
                value={fTarget}
                onChange={(e) => setFTarget(Number(e.target.value))}
                className="w-full mt-1 px-3 py-2 rounded-lg border border-slate-200 text-sm"
              >
                {targets.map((m) => (
                  <option key={m.index} value={m.index}>{m.label || `Motor ${m.index}`}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-[10px] font-bold text-slate-500 uppercase">Duracion (min)</label>
              <input
                type="number"
                value={fDuration}
                onChange={(e) => setFDuration(Number(e.target.value))}
                min={1}
                className="w-full mt-1 px-3 py-2 rounded-lg border border-slate-200 text-sm"
              />
            </div>
          </div>
          <div>
            <label className="text-[10px] font-bold text-slate-500 uppercase">Fecha/Hora Inicio</label>
            <input
              type="datetime-local"
              value={fStart}
              onChange={(e) => setFStart(e.target.value)}
              className="w-full mt-1 px-3 py-2 rounded-lg border border-slate-200 text-sm"
            />
          </div>
          <div className="flex gap-2 justify-end">
            <button onClick={() => setShowForm(false)} className="px-4 py-2 text-xs text-slate-500">
              Cancelar
            </button>
            <button
              onClick={handleCreate}
              disabled={!fStart}
              className="px-4 py-2 bg-accent text-white rounded-lg text-xs font-bold active:scale-95 disabled:opacity-50"
            >
              Programar
            </button>
          </div>
        </div>
      )}

      {/* Actions list */}
      <div className="px-4 space-y-2">
        {actions.map((a) => {
          const silo = silos[a.silo_index]
          const isExecuted = a.executed === 1
          return (
            <div
              key={a.id}
              className={`bg-white rounded-xl p-3 border space-y-1 ${
                isExecuted ? 'border-slate-100 opacity-60' : 'border-slate-200'
              }`}
            >
              <div className="flex items-center gap-2">
                {isExecuted ? (
                  <CheckCircle size={14} className="text-emerald-500" />
                ) : (
                  <Clock size={14} className="text-amber-500" />
                )}
                <span className="text-xs font-bold text-slate-700">
                  {silo?.name ?? `Silo ${a.silo_index}`}
                </span>
                <span className="text-[10px] bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full font-bold uppercase">
                  {a.action_type}
                </span>
                <span className="text-[10px] text-slate-400">Target #{a.target_index}</span>
                {!isExecuted && (
                  <button
                    onClick={() => handleDelete(a.id)}
                    className="ml-auto p-1 text-slate-400 hover:text-red-500"
                  >
                    <Trash2 size={14} />
                  </button>
                )}
              </div>
              <div className="flex items-center gap-3 text-[10px] text-slate-500">
                <span>Inicio: {new Date(a.start_time).toLocaleString('es-CR')}</span>
                <span>Duracion: {a.duration_min} min</span>
              </div>
            </div>
          )
        })}

        {actions.length === 0 && (
          <div className="text-center text-slate-400 py-12 text-sm">
            No hay acciones programadas
          </div>
        )}
      </div>
    </div>
  )
}
