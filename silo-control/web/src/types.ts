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

export interface GateStatus {
  index: number
  cmd_open: boolean
  cmd_close: boolean
  is_open: boolean
  is_closed: boolean
  in_motion: boolean
  fault: boolean
}

export interface Thresholds {
  temp_max: number
  temp_min: number
  humid_max: number
  auto_global: boolean
  alarm_active: boolean
}

export interface CurrentWeather {
  temperature: number | null
  humidity: number | null
  fetched_at: string
}

export interface WeatherThresholds {
  ambient_temp_max: number
  ambient_humid_max: number
  weather_auto_enabled: boolean
}

export interface ScadaUpdate {
  type: 'scada_update'
  timestamp: string
  connected: boolean
  sensors: SensorReading[]
  motors: MotorStatus[]
  gates: GateStatus[]
  thresholds: Thresholds | null
  quality: Record<string, string>       // silo_index -> "libre"|"ok"|"cuarentena"
  motor_runtime: Record<string, number> // motor_index -> total_hours
  current_weather: CurrentWeather | null
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
  motor_type: 'silo_fan' | 'rfan' | 'barredora' | 'soft_starter' | 'vfd' | 'contactor'
}

export interface LevelSensorConfig {
  label: string
  sensor_type: 'hl' | 'll'
}

export interface GateConfig {
  index: number
  label: string
  gate_type: 'distribucion' | 'descarga_central' | 'descarga_lateral'
}

export interface SiloConfig {
  name: string
  sensors: SensorConfig[]
  motors: MotorConfig[]
  level_sensors: LevelSensorConfig[]
  gates: GateConfig[]
}

// ── Quality types ────────────────────────────────────────────────────

export type QualityStatus = 'libre' | 'ok' | 'cuarentena'

// ── Work Order types ─────────────────────────────────────────────────

export type OrderType = 'aireacion' | 'enfriamiento' | 'fumigacion' | 'otro'
export type OrderStatus = 'pendiente' | 'en_progreso' | 'completada' | 'cancelada'

export interface WorkOrder {
  id: number
  silo_index: number
  order_type: OrderType
  description: string
  status: OrderStatus
  created_at: string
  started_at: string | null
  completed_at: string | null
}

// ── Scheduler types ──────────────────────────────────────────────────

export interface ScheduledAction {
  id: number
  silo_index: number
  action_type: 'motor' | 'ventilador' | 'compuerta'
  target_index: number
  start_time: string
  duration_min: number
  enabled: number
  executed: number
  created_at: string
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
  humidity_day: number | null
  humidity_night: number | null
}

export interface WeatherResponse {
  location: WeatherLocation
  fetched_at: string
  days: ForecastDay[]
}
