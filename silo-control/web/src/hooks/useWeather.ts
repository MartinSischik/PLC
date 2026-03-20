import { useEffect, useState, useCallback } from 'react'
import type { WeatherResponse } from '../types'
import { fetchWeather } from '../api'

interface WeatherState {
  data: WeatherResponse | null
  loading: boolean
  error: string | null
}

export function useWeather(locationIndex: number) {
  const [state, setState] = useState<WeatherState>({
    data: null,
    loading: false,
    error: null,
  })

  const load = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: null }))
    try {
      const data = await fetchWeather(locationIndex)
      setState({ data, loading: false, error: data ? null : 'Sin datos' })
    } catch (e) {
      setState({ data: null, loading: false, error: 'Error de conexión' })
    }
  }, [locationIndex])

  useEffect(() => {
    load()
  }, [load])

  return { ...state, refresh: load }
}
