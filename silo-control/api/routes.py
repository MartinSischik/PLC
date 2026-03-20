# api/routes.py
# REST endpoints para SCADA y Weather.

import asyncio
from dataclasses import asdict

from fastapi import APIRouter, Request
from pydantic import BaseModel

from config import SILOS, MOTOR_COUNT
from api.weather_service import get_locations, get_forecast

router = APIRouter(prefix="/api")


# ── Modelos de request ──────────────────────────────────────────────────

class MotorAction(BaseModel):
    value: bool

class ThresholdsUpdate(BaseModel):
    temp_max: float
    humid_max: float


# ── Config ──────────────────────────────────────────────────────────────

@router.get("/config")
async def get_config():
    silos = []
    for silo in SILOS:
        silos.append({
            "name": silo.name,
            "sensors": [asdict(s) for s in silo.sensors],
            "motors": [asdict(m) for m in silo.motors],
        })
    return {"silos": silos}


# ── Thresholds ──────────────────────────────────────────────────────────

@router.get("/thresholds")
async def get_thresholds(request: Request):
    plc = request.app.state.plc
    data = await asyncio.to_thread(plc.read_thresholds)
    if data is None:
        return {"ok": False}
    return {"ok": True, **data}

@router.post("/thresholds")
async def set_thresholds(body: ThresholdsUpdate, request: Request):
    plc = request.app.state.plc
    ok = await asyncio.to_thread(plc.set_thresholds, body.temp_max, body.humid_max)
    return {"ok": ok}


# ── Motor commands ──────────────────────────────────────────────────────

@router.post("/motor/{index}/command")
async def motor_command(index: int, body: MotorAction, request: Request):
    if not (0 <= index < MOTOR_COUNT):
        return {"ok": False, "error": f"Motor index {index} out of range"}
    plc = request.app.state.plc
    ok = await asyncio.to_thread(plc.set_motor_command, index, body.value)
    return {"ok": ok}


@router.post("/motor/{index}/auto")
async def motor_auto(index: int, body: MotorAction, request: Request):
    if not (0 <= index < MOTOR_COUNT):
        return {"ok": False, "error": f"Motor index {index} out of range"}
    plc = request.app.state.plc
    ok = await asyncio.to_thread(plc.set_motor_auto_mode, index, body.value)
    return {"ok": ok}


@router.post("/motor/{index}/enabled")
async def motor_enabled(index: int, body: MotorAction, request: Request):
    if not (0 <= index < MOTOR_COUNT):
        return {"ok": False, "error": f"Motor index {index} out of range"}
    plc = request.app.state.plc
    ok = await asyncio.to_thread(plc.set_motor_enabled, index, body.value)
    return {"ok": ok}


@router.post("/motors/enable-all")
async def motors_enable_all(body: MotorAction, request: Request):
    plc = request.app.state.plc
    failed = []
    for i in range(MOTOR_COUNT):
        ok = await asyncio.to_thread(plc.set_motor_enabled, i, body.value)
        if not ok:
            failed.append(i)
    return {"ok": len(failed) == 0, "failed": failed}


# ── Weather ─────────────────────────────────────────────────────────────

@router.get("/weather/locations")
async def weather_locations():
    return {"locations": get_locations()}


@router.get("/weather/{location_index}")
async def weather_forecast(location_index: int):
    data = await get_forecast(location_index)
    if data is None:
        return {"ok": False, "error": "Failed to fetch forecast"}
    return data
