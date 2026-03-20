// ── SCADA types ────────────────────────────────────────────────────────

export interface SensorReading {
  index: number
  temperature: number
  humidity: number
  active: boolean
}

export interface MotorStatus {
  index: number
  cmd_run: boolean
  is_running: boolean
  auto_mode: boolean
  enabled: boolean
  fault: boolean
}

export interface Thresholds {
  temp_max: number
  temp_min: number
  humid_max: number
  auto_global: boolean
  alarm_active: boolean
}

export interface ScadaUpdate {
  type: 'scada_update'
  timestamp: string
  connected: boolean
  sensors: SensorReading[]
  motors: MotorStatus[]
  thresholds: Thresholds | null
}

// ── Config types ───────────────────────────────────────────────────────

export interface SensorConfig {
  index: number
  label: string
  show_temp: boolean
  show_humidity: boolean
}

export interface MotorConfig {
  index: number
  label: string
  motor_type: 'soft_starter' | 'vfd'
}

export interface SiloConfig {
  name: string
  sensors: SensorConfig[]
  motors: MotorConfig[]
}

// ── Weather types ──────────────────────────────────────────────────────

export interface WeatherLocation {
  name: string
  lat: number
  lon: number
}

export interface ForecastDay {
  day_name: string | null
  date: string | null
  temp_max: number | null
  temp_min: number | null
  icon_code: number | null
  icon_name: string
  precipitation_mm: number | null
  narrative: string
}

export interface WeatherResponse {
  location: WeatherLocation
  fetched_at: string
  days: ForecastDay[]
}
