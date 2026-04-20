import { useEffect, useState } from 'react'
import { Plus, Play, CheckCircle, XCircle, Clock } from 'lucide-react'
import type { WorkOrder, SiloConfig, OrderType, OrderStatus } from '../types'
import { fetchConfig, fetchWorkOrders, createWorkOrder, updateWorkOrderStatus } from '../api'

const ORDER_TYPES: { value: OrderType; label: string }[] = [
  { value: 'aireacion', label: 'Aireacion' },
  { value: 'enfriamiento', label: 'Enfriamiento' },
  { value: 'fumigacion', label: 'Fumigacion' },
  { value: 'otro', label: 'Otro' },
]

const STATUS_COLORS: Record<OrderStatus, string> = {
  pendiente: 'bg-amber-100 text-amber-700',
  en_progreso: 'bg-blue-100 text-blue-700',
  completada: 'bg-emerald-100 text-emerald-700',
  cancelada: 'bg-slate-100 text-slate-400',
}

const STATUS_LABELS: Record<OrderStatus, string> = {
  pendiente: 'Pendiente',
  en_progreso: 'En Progreso',
  completada: 'Completada',
  cancelada: 'Cancelada',
}

export function WorkOrdersPage() {
  const [orders, setOrders] = useState<WorkOrder[]>([])
  const [silos, setSilos] = useState<SiloConfig[]>([])
  const [showForm, setShowForm] = useState(false)
  const [filterSilo, setFilterSilo] = useState<number | undefined>(undefined)

  // Form state
  const [formSilo, setFormSilo] = useState(0)
  const [formType, setFormType] = useState<OrderType>('aireacion')
  const [formDesc, setFormDesc] = useState('')

  const load = () => {
    fetchWorkOrders(filterSilo).then(setOrders).catch(console.error)
  }

  useEffect(() => {
    fetchConfig().then(setSilos).catch(console.error)
  }, [])

  useEffect(() => { load() }, [filterSilo])

  async function handleCreate() {
    await createWorkOrder(formSilo, formType, formDesc)
    setShowForm(false)
    setFormDesc('')
    load()
  }

  async function handleStatus(id: number, status: OrderStatus) {
    await updateWorkOrderStatus(id, status)
    load()
  }

  return (
    <div className="space-y-4 pb-20 pt-4">
      <div className="px-4 flex items-center justify-between">
        <h2 className="text-lg font-bold text-slate-700">Ordenes de Trabajo</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-accent text-white text-xs font-bold active:scale-95 transition-transform"
        >
          <Plus size={14} /> Nueva
        </button>
      </div>

      {/* Filter */}
      <div className="px-4 flex gap-2 overflow-x-auto">
        <button
          onClick={() => setFilterSilo(undefined)}
          className={`shrink-0 px-3 py-1 rounded-full text-xs font-bold border transition-colors ${
            filterSilo === undefined ? 'bg-accent text-white border-accent' : 'bg-white text-slate-500 border-slate-200'
          }`}
        >
          Todos
        </button>
        {silos.map((s, i) => (
          <button
            key={i}
            onClick={() => setFilterSilo(i)}
            className={`shrink-0 px-3 py-1 rounded-full text-xs font-bold border transition-colors ${
              filterSilo === i ? 'bg-accent text-white border-accent' : 'bg-white text-slate-500 border-slate-200'
            }`}
          >
            {s.name}
          </button>
        ))}
      </div>

      {/* Create form */}
      {showForm && (
        <div className="mx-4 bg-white rounded-xl p-4 border border-slate-200 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[10px] font-bold text-slate-500 uppercase">Silo</label>
              <select
                value={formSilo}
                onChange={(e) => setFormSilo(Number(e.target.value))}
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
                value={formType}
                onChange={(e) => setFormType(e.target.value as OrderType)}
                className="w-full mt-1 px-3 py-2 rounded-lg border border-slate-200 text-sm"
              >
                {ORDER_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <label className="text-[10px] font-bold text-slate-500 uppercase">Descripcion</label>
            <input
              value={formDesc}
              onChange={(e) => setFormDesc(e.target.value)}
              placeholder="Descripcion opcional..."
              className="w-full mt-1 px-3 py-2 rounded-lg border border-slate-200 text-sm"
            />
          </div>
          <div className="flex gap-2 justify-end">
            <button onClick={() => setShowForm(false)} className="px-4 py-2 text-xs text-slate-500">
              Cancelar
            </button>
            <button
              onClick={handleCreate}
              className="px-4 py-2 bg-accent text-white rounded-lg text-xs font-bold active:scale-95"
            >
              Crear Orden
            </button>
          </div>
        </div>
      )}

      {/* Orders list */}
      <div className="px-4 space-y-2">
        {orders.map((o) => (
          <div key={o.id} className="bg-white rounded-xl p-3 border border-slate-200 space-y-2">
            <div className="flex items-center gap-2">
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${STATUS_COLORS[o.status]}`}>
                {STATUS_LABELS[o.status]}
              </span>
              <span className="text-xs font-bold text-slate-700">
                {silos[o.silo_index]?.name ?? `Silo ${o.silo_index}`}
              </span>
              <span className="text-[10px] text-slate-400 uppercase">{o.order_type}</span>
              <span className="text-[10px] text-slate-400 ml-auto">#{o.id}</span>
            </div>
            {o.description && (
              <p className="text-xs text-slate-500">{o.description}</p>
            )}
            <div className="flex items-center gap-1 text-[10px] text-slate-400">
              <Clock size={10} />
              {new Date(o.created_at).toLocaleString('es-CR')}
              {o.started_at && <span className="ml-2">Inicio: {new Date(o.started_at).toLocaleString('es-CR')}</span>}
              {o.completed_at && <span className="ml-2">Fin: {new Date(o.completed_at).toLocaleString('es-CR')}</span>}
            </div>

            {/* Action buttons based on current status */}
            {o.status === 'pendiente' && (
              <div className="flex gap-2">
                <button
                  onClick={() => handleStatus(o.id, 'en_progreso')}
                  className="flex items-center gap-1 px-3 py-1.5 bg-blue-50 text-blue-700 rounded-lg text-xs font-bold active:scale-95"
                >
                  <Play size={12} /> Iniciar
                </button>
                <button
                  onClick={() => handleStatus(o.id, 'cancelada')}
                  className="flex items-center gap-1 px-3 py-1.5 bg-slate-50 text-slate-500 rounded-lg text-xs font-bold active:scale-95"
                >
                  <XCircle size={12} /> Cancelar
                </button>
              </div>
            )}
            {o.status === 'en_progreso' && (
              <div className="flex gap-2">
                <button
                  onClick={() => handleStatus(o.id, 'completada')}
                  className="flex items-center gap-1 px-3 py-1.5 bg-emerald-50 text-emerald-700 rounded-lg text-xs font-bold active:scale-95"
                >
                  <CheckCircle size={12} /> Completar
                </button>
                <button
                  onClick={() => handleStatus(o.id, 'cancelada')}
                  className="flex items-center gap-1 px-3 py-1.5 bg-slate-50 text-slate-500 rounded-lg text-xs font-bold active:scale-95"
                >
                  <XCircle size={12} /> Cancelar
                </button>
              </div>
            )}
          </div>
        ))}

        {orders.length === 0 && (
          <div className="text-center text-slate-400 py-12 text-sm">
            No hay ordenes de trabajo
          </div>
        )}
      </div>
    </div>
  )
}
