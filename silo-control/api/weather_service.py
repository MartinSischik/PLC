# api/weather_service.py
# Proxy para The Weather Company API con caché TTL.

import time
from typing import Optional

import httpx

# ── Configuración Weather ───────────────────────────────────────────────
API_KEY = "cd2ec8a3256e45d2aec8a3256e45d24f"

LOCATIONS = [
    {"name": "San José",    "lat":  9.9281,  "lon": -84.0907},
    {"name": "Liberia",     "lat": 10.6333,  "lon": -85.4333},
    {"name": "Limón",       "lat":  9.9900,  "lon": -83.0360},
    {"name": "Puntarenas",  "lat":  9.9763,  "lon": -84.8327},
    {"name": "Alajuela",    "lat": 10.0162,  "lon": -84.2144},
]

FORECAST_DAYS = 5
CACHE_TTL = 600  # 10 minutos

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

            days.append({
                "day_name": raw.get("dayOfWeek", [None] * FORECAST_DAYS)[i],
                "date": raw.get("validTimeLocal", [None] * FORECAST_DAYS)[i],
                "temp_max": raw.get("temperatureMax", [None] * FORECAST_DAYS)[i],
                "temp_min": raw.get("temperatureMin", [None] * FORECAST_DAYS)[i],
                "icon_code": icon_code,
                "icon_name": WEATHER_ICONS.get(icon_code, "cloudy") if icon_code else "cloudy",
                "precipitation_mm": raw.get("qpf", [None] * FORECAST_DAYS)[i],
                "narrative": raw.get("narrative", [""] * FORECAST_DAYS)[i],
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
