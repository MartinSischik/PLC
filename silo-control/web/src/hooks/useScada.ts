import { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react'
import type { SensorReading, MotorStatus, Thresholds, ScadaUpdate } from '../types'
import { getWsUrl } from '../api'

export interface ScadaState {
  sensors: SensorReading[]
  motors: MotorStatus[]
  thresholds: Thresholds | null
  connected: boolean
  wsConnected: boolean
}

const defaultState: ScadaState = {
  sensors: [],
  motors: [],
  thresholds: null,
  connected: false,
  wsConnected: false,
}

export const ScadaContext = createContext<ScadaState>(defaultState)

export function useScada(): ScadaState {
  return useContext(ScadaContext)
}

/** Hook interno — usar solo en el provider (App.tsx) */
export function useScadaConnection(): ScadaState {
  const [state, setState] = useState<ScadaState>(defaultState)
  const wsRef = useRef<WebSocket | null>(null)
  const retryRef = useRef(1000)

  const connect = useCallback(() => {
    const ws = new WebSocket(getWsUrl())
    wsRef.current = ws

    ws.onopen = () => {
      retryRef.current = 1000
      setState((s) => ({ ...s, wsConnected: true }))
    }

    ws.onmessage = (ev) => {
      try {
        const data: ScadaUpdate = JSON.parse(ev.data)
        setState({
          sensors: data.sensors,
          motors: data.motors,
          thresholds: data.thresholds,
          connected: data.connected,
          wsConnected: true,
        })
      } catch { /* ignore parse errors */ }
    }

    ws.onclose = () => {
      setState((s) => ({ ...s, wsConnected: false }))
      const delay = Math.min(retryRef.current, 10000)
      retryRef.current = delay * 1.5
      setTimeout(connect, delay)
    }

    ws.onerror = () => ws.close()
  }, [])

  useEffect(() => {
    connect()
    return () => {
      wsRef.current?.close()
    }
  }, [connect])

  return state
}
