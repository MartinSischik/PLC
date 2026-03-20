import type { SiloConfig, WeatherLocation, WeatherResponse } from './types'

const BASE = ''

export async function fetchConfig(): Promise<SiloConfig[]> {
  const res = await fetch(`${BASE}/api/config`)
  const data = await res.json()
  return data.silos
}

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

export function getWsUrl(): string {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${window.location.host}/ws/scada`
}
