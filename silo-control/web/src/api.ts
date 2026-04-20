import type { SiloConfig, WeatherLocation, WeatherResponse, WorkOrder, ScheduledAction, QualityStatus, WeatherThresholds, CurrentWeather } from './types'

const BASE = ''

// ── Config ──────────────────────────────────────────────────────────────

export async function fetchConfig(): Promise<SiloConfig[]> {
  const res = await fetch(`${BASE}/api/config`)
  const data = await res.json()
  return data.silos
}

// ── Motor commands ──────────────────────────────────────────────────────

export async function postMotorAction(
  index: number,
  action: 'command' | 'auto' | 'enabled',
  value: boolean,
): Promise<boolean> {
  const res = await fetch(`${BASE}/api/motor/${index}/${action}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ value }),
  })
  const data = await res.json()
  return data.ok ?? false
}

export async function postEnableAll(value: boolean): Promise<{ ok: boolean; failed: number[] }> {
  const res = await fetch(`${BASE}/api/motors/enable-all`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ value }),
  })
  return res.json()
}

export async function postAutoAll(value: boolean): Promise<{ ok: boolean; failed: number[] }> {
  const res = await fetch(`${BASE}/api/motors/auto-all`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ value }),
  })
  return res.json()
}

// ── Gate commands ────────────────────────────────────────────────────────

export async function postGateAction(
  index: number,
  action: 'open' | 'close' | 'stop',
): Promise<boolean> {
  const res = await fetch(`${BASE}/api/gate/${index}/command`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action }),
  })
  const data = await res.json()
  return data.ok ?? false
}

// ── Thresholds ──────────────────────────────────────────────────────────

export async function fetchThresholds(): Promise<{ temp_max: number; humid_max: number } | null> {
  const res = await fetch(`${BASE}/api/thresholds`)
  const data = await res.json()
  return data.ok ? { temp_max: data.temp_max, humid_max: data.humid_max } : null
}

export async function postThresholds(temp_max: number, humid_max: number): Promise<boolean> {
  const res = await fetch(`${BASE}/api/thresholds`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ temp_max, humid_max }),
  })
  const data = await res.json()
  return data.ok ?? false
}

// ── Quality Status ──────────────────────────────────────────────────────

export async function postQuality(siloIndex: number, status: QualityStatus): Promise<boolean> {
  const res = await fetch(`${BASE}/api/quality/${siloIndex}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  })
  const data = await res.json()
  return data.ok ?? false
}

// ── Work Orders ─────────────────────────────────────────────────────────

export async function fetchWorkOrders(siloIndex?: number): Promise<WorkOrder[]> {
  const params = siloIndex !== undefined ? `?silo_index=${siloIndex}` : ''
  const res = await fetch(`${BASE}/api/work-orders${params}`)
  const data = await res.json()
  return data.orders
}

export async function createWorkOrder(
  siloIndex: number,
  orderType: string,
  description: string = '',
): Promise<number> {
  const res = await fetch(`${BASE}/api/work-orders`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ silo_index: siloIndex, order_type: orderType, description }),
  })
  const data = await res.json()
  return data.id
}

export async function updateWorkOrderStatus(orderId: number, status: string): Promise<boolean> {
  const res = await fetch(`${BASE}/api/work-orders/${orderId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  })
  const data = await res.json()
  return data.ok ?? false
}

// ── Scheduled Actions ───────────────────────────────────────────────────

export async function fetchSchedule(siloIndex?: number): Promise<ScheduledAction[]> {
  const params = siloIndex !== undefined ? `?silo_index=${siloIndex}` : ''
  const res = await fetch(`${BASE}/api/schedule${params}`)
  const data = await res.json()
  return data.actions
}

export async function createScheduledAction(
  siloIndex: number,
  actionType: string,
  targetIndex: number,
  startTime: string,
  durationMin: number,
): Promise<number> {
  const res = await fetch(`${BASE}/api/schedule`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      silo_index: siloIndex,
      action_type: actionType,
      target_index: targetIndex,
      start_time: startTime,
      duration_min: durationMin,
    }),
  })
  const data = await res.json()
  return data.id
}

export async function deleteScheduledAction(actionId: number): Promise<boolean> {
  const res = await fetch(`${BASE}/api/schedule/${actionId}`, { method: 'DELETE' })
  const data = await res.json()
  return data.ok ?? false
}

// ── Motor Runtime ───────────────────────────────────────────────────────

export async function fetchMotorRuntime(): Promise<Record<string, number>> {
  const res = await fetch(`${BASE}/api/motor-runtime`)
  const data = await res.json()
  return data.totals
}

// ── Weather ─────────────────────────────────────────────────────────────

export async function fetchWeatherLocations(): Promise<WeatherLocation[]> {
  const res = await fetch(`${BASE}/api/weather/locations`)
  const data = await res.json()
  return data.locations
}

export async function fetchWeather(locationIndex: number): Promise<WeatherResponse | null> {
  const res = await fetch(`${BASE}/api/weather/${locationIndex}`)
  if (!res.ok) return null
  return res.json()
}

export async function fetchCurrentWeather(): Promise<CurrentWeather | null> {
  const res = await fetch(`${BASE}/api/weather/current`)
  const data = await res.json()
  return data.ok ? { temperature: data.temperature, humidity: data.humidity, fetched_at: data.fetched_at } : null
}

// ── Weather Thresholds ────────────────────────────────────────────────────

export async function fetchWeatherThresholds(): Promise<WeatherThresholds> {
  const res = await fetch(`${BASE}/api/weather-thresholds`)
  return res.json()
}

export async function postWeatherThresholds(thresholds: WeatherThresholds): Promise<boolean> {
  const res = await fetch(`${BASE}/api/weather-thresholds`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(thresholds),
  })
  const data = await res.json()
  return data.ok ?? false
}

// ── WebSocket ───────────────────────────────────────────────────────────

export function getWsUrl(): string {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${window.location.host}/ws/scada`
}
