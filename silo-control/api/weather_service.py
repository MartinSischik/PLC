# api/weather_service.py
# Proxy para The Weather Company API con caché TTL.

import time
from typing import Optional

import httpx

# ── Configuración Weather ───────────────────────────────────────────────
API_KEY = "cd2ec8a3256e45d2aec8a3256e45d24f"

LOCATIONS = [
    {"name": "Limón",       "lat":  9.9900,  "lon": -83.0360},
]

FORECAST_DAYS = 5
CACHE_TTL = 600          # 10 minutos pronóstico
CURRENT_CACHE_TTL = 300  # 5 minutos condiciones actuales

WEATHER_ICONS: dict[int, str] = {
    1: "sunny", 2: "sunny",
    3: "partly_cloudy", 4: "partly_cloudy", 5: "partly_cloudy", 6: "partly_cloudy",
    7: "cloudy", 8: "cloudy", 9: "cloudy", 10: "cloudy", 11: "cloudy",
    12: "rain", 13: "rain", 14: "rain",
    15: "snow", 16: "snow", 17: "snow", 18: "snow",
    19: "storm", 20: "storm", 21: "storm",
    37: "thunderstorm", 38: "thunderstorm", 39: "thunderstorm",
    40: "rain", 41: "rain", 42: "rain", 43: "rain",
    44: "rain", 45: "rain", 46: "rain", 47: "rain",
}

# ── Caché en memoria ────────────────────────────────────────────────────
_cache: dict[int, tuple[float, dict]] = {}
_current_cache: tuple[float, dict] | None = None  # (timestamp, data)


def get_locations() -> list[dict]:
    return LOCATIONS


async def get_forecast(location_index: int) -> Optional[dict]:
    if location_index < 0 or location_index >= len(LOCATIONS):
        return None

    now = time.time()
    if location_index in _cache:
        cached_time, cached_data = _cache[location_index]
        if now - cached_time < CACHE_TTL:
            return cached_data

    loc = LOCATIONS[location_index]
    url = f"https://api.weather.com/v3/wx/forecast/daily/{FORECAST_DAYS}day"
    params = {
        "geocode": f"{loc['lat']},{loc['lon']}",
        "format": "json",
        "units": "m",
        "language": "es-ES",
        "apiKey": API_KEY,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            raw = resp.json()

        days = []
        for i in range(FORECAST_DAYS):
            icon_code = None
            if raw.get("daypart") and raw["daypart"][0].get("iconCode"):
                codes = raw["daypart"][0]["iconCode"]
                idx = i * 2  # day part
                if idx < len(codes) and codes[idx] is not None:
                    icon_code = codes[idx]
                elif idx + 1 < len(codes) and codes[idx + 1] is not None:
                    icon_code = codes[idx + 1]

            # Extract humidity from daypart data
            humidity_day = None
            humidity_night = None
            if raw.get("daypart") and raw["daypart"][0].get("relativeHumidity"):
                hum_list = raw["daypart"][0]["relativeHumidity"]
                idx_d = i * 2
                idx_n = i * 2 + 1
                if idx_d < len(hum_list):
                    humidity_day = hum_list[idx_d]
                if idx_n < len(hum_list):
                    humidity_night = hum_list[idx_n]

            days.append({
                "day_name": raw.get("dayOfWeek", [None] * FORECAST_DAYS)[i],
                "date": raw.get("validTimeLocal", [None] * FORECAST_DAYS)[i],
                "temp_max": raw.get("temperatureMax", [None] * FORECAST_DAYS)[i],
                "temp_min": raw.get("temperatureMin", [None] * FORECAST_DAYS)[i],
                "icon_code": icon_code,
                "icon_name": WEATHER_ICONS.get(icon_code, "cloudy") if icon_code else "cloudy",
                "precipitation_mm": raw.get("qpf", [None] * FORECAST_DAYS)[i],
                "narrative": raw.get("narrative", [""] * FORECAST_DAYS)[i],
                "humidity_day": humidity_day,
                "humidity_night": humidity_night,
            })

        result = {
            "location": loc,
            "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "days": days,
        }

        _cache[location_index] = (now, result)
        return result

    except Exception as e:
        print(f"[WEATHER] Error fetching forecast: {e}")
        if location_index in _cache:
            return _cache[location_index][1]
        return None


def get_current_conditions_sync() -> Optional[dict]:
    """Retorna temperatura y humedad de hoy en Limón derivados del pronóstico cacheado.
    Usa temp promedio (max+min)/2 del día 0 y humedad diurna del daypart 0."""
    # El pronóstico (índice 0 = Limón) se renueva cada CACHE_TTL segundos.
    # Extraemos el día 0 (hoy) para obtener los valores más recientes disponibles.
    cached = _cache.get(0)
    if cached is None:
        return None
    _, forecast = cached
    days = forecast.get("days", [])
    if not days:
        return None
    today = days[0]

    t_max = today.get("temp_max")
    t_min = today.get("temp_min")
    temp: Optional[float] = None
    if t_max is not None and t_min is not None:
        temp = round((t_max + t_min) / 2.0, 1)
    elif t_max is not None:
        temp = float(t_max)
    elif t_min is not None:
        temp = float(t_min)

    humid = today.get("humidity_day")

    return {
        "temperature": temp,
        "humidity": humid,
        "fetched_at": forecast.get("fetched_at", ""),
    }
