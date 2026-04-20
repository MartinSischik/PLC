# api/routes.py
# REST endpoints para SCADA y Weather.

import asyncio
from dataclasses import asdict
from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

from config import SILOS, MOTOR_COUNT, GATE_COUNT
from api.weather_service import get_locations, get_forecast, get_current_conditions_sync
from core.database import (
    get_all_silo_quality, set_silo_quality,
    create_work_order, get_work_orders, update_work_order_status,
    create_scheduled_action, get_scheduled_actions, delete_scheduled_action,
    get_motor_runtime_totals, get_motor_runtime_history,
    get_weather_thresholds, set_weather_thresholds,
)

router = APIRouter(prefix="/api")


# ── Modelos de request ──────────────────────────────────────────────────

class MotorAction(BaseModel):
    value: bool

class ThresholdsUpdate(BaseModel):
    temp_max: float
    humid_max: float

class QualityUpdate(BaseModel):
    status: str  # libre | ok | cuarentena

class WorkOrderCreate(BaseModel):
    silo_index: int
    order_type: str  # aireacion | enfriamiento | fumigacion | otro
    description: str = ""

class WorkOrderStatusUpdate(BaseModel):
    status: str  # pendiente | en_progreso | completada | cancelada

class ScheduledActionCreate(BaseModel):
    silo_index: int
    action_type: str  # motor | ventilador | compuerta
    target_index: int
    start_time: str   # ISO datetime
    duration_min: int

class WeatherThresholdsUpdate(BaseModel):
    ambient_temp_max: float
    ambient_humid_max: float
    weather_auto_enabled: bool


# ── Config ──────────────────────────────────────────────────────────────

@router.get("/config")
async def get_config():
    silos = []
    for silo in SILOS:
        silos.append({
            "name": silo.name,
            "sensors": [asdict(s) for s in silo.sensors],
            "motors": [asdict(m) for m in silo.motors],
            "level_sensors": [asdict(ls) for ls in silo.level_sensors],
            "gates": [asdict(g) for g in silo.gates],
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


@router.post("/motors/auto-all")
async def motors_auto_all(body: MotorAction, request: Request):
    plc = request.app.state.plc
    failed = []
    for i in range(MOTOR_COUNT):
        ok = await asyncio.to_thread(plc.set_motor_auto_mode, i, body.value)
        if not ok:
            failed.append(i)
    return {"ok": len(failed) == 0, "failed": failed}


# ── Gate commands ─────────────────────────────────────────────────────

class GateAction(BaseModel):
    action: str  # "open" | "close" | "stop"

@router.post("/gate/{index}/command")
async def gate_command(index: int, body: GateAction, request: Request):
    if not (0 <= index < GATE_COUNT):
        return {"ok": False, "error": f"Gate index {index} out of range"}
    plc = request.app.state.plc
    if body.action == "open":
        ok = await asyncio.to_thread(plc.set_gate_open, index)
    elif body.action == "close":
        ok = await asyncio.to_thread(plc.set_gate_close, index)
    elif body.action == "stop":
        ok = await asyncio.to_thread(plc.set_gate_stop, index)
    else:
        return {"ok": False, "error": f"Invalid action: {body.action}"}
    return {"ok": ok}


# ── Weather ─────────────────────────────────────────────────────────────

@router.get("/weather/locations")
async def weather_locations():
    return {"locations": get_locations()}


@router.get("/weather/current")
async def weather_current():
    data = await asyncio.to_thread(get_current_conditions_sync)
    if data is None:
        return {"ok": False, "error": "No current conditions available"}
    return {"ok": True, **data}


@router.get("/weather/{location_index}")
async def weather_forecast(location_index: int):
    data = await get_forecast(location_index)
    if data is None:
        return {"ok": False, "error": "Failed to fetch forecast"}
    return data


# ── Weather Thresholds ────────────────────────────────────────────────────

@router.get("/weather-thresholds")
async def weather_thresholds_get():
    return get_weather_thresholds()


@router.post("/weather-thresholds")
async def weather_thresholds_set(body: WeatherThresholdsUpdate):
    await asyncio.to_thread(
        set_weather_thresholds,
        body.ambient_temp_max,
        body.ambient_humid_max,
        body.weather_auto_enabled,
    )
    return {"ok": True}


# ── Quality Status ────────────────────────────────────────────────────────

@router.get("/quality")
async def quality_list():
    return {"quality": get_all_silo_quality()}


@router.post("/quality/{silo_index}")
async def quality_update(silo_index: int, body: QualityUpdate):
    ok = set_silo_quality(silo_index, body.status)
    return {"ok": ok}


# ── Work Orders ───────────────────────────────────────────────────────────

@router.get("/work-orders")
async def work_orders_list(silo_index: Optional[int] = None, status: Optional[str] = None):
    return {"orders": get_work_orders(silo_index, status)}


@router.post("/work-orders")
async def work_order_create(body: WorkOrderCreate):
    oid = create_work_order(body.silo_index, body.order_type, body.description)
    return {"ok": True, "id": oid}


@router.patch("/work-orders/{order_id}")
async def work_order_update(order_id: int, body: WorkOrderStatusUpdate):
    ok = update_work_order_status(order_id, body.status)
    return {"ok": ok}


# ── Scheduled Actions ─────────────────────────────────────────────────────

@router.get("/schedule")
async def schedule_list(silo_index: Optional[int] = None):
    return {"actions": get_scheduled_actions(silo_index)}


@router.post("/schedule")
async def schedule_create(body: ScheduledActionCreate):
    aid = create_scheduled_action(
        body.silo_index, body.action_type, body.target_index,
        body.start_time, body.duration_min,
    )
    return {"ok": True, "id": aid}


@router.delete("/schedule/{action_id}")
async def schedule_delete(action_id: int):
    delete_scheduled_action(action_id)
    return {"ok": True}


# ── Motor Runtime ─────────────────────────────────────────────────────────

@router.get("/motor-runtime")
async def motor_runtime_list():
    return {"totals": get_motor_runtime_totals()}


@router.get("/motor-runtime/{motor_index}")
async def motor_runtime_detail(motor_index: int, limit: int = 50):
    return {"history": get_motor_runtime_history(motor_index, limit)}
