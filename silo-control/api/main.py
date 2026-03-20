# api/main.py
# FastAPI backend para SCADA web + Weather.
# Reemplaza main_gui.py como entry point web.
#
# Uso:
#   cd silo-control
#   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

import asyncio
import json
import time
from contextlib import asynccontextmanager
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import (
    PLC_IP, PLC_RACK, PLC_SLOT,
    ENABLE_TMS_BRIDGE, SENSOR_SOURCE,
)
from core.plc_interface import SiloPLC
from core.tms6000_provider import Tms6000Provider
from core.tms_bridge_service import TmsBridgeService
from core.sim_temperature_service import SimTemperatureService
from core.automation_service import AutomationService
from api.routes import router


# ── Helpers ─────────────────────────────────────────────────────────────

def _read_plc_state(plc: SiloPLC) -> dict:
    """Lee todo el estado del PLC (bloqueante — ejecutar en thread)."""
    connected = plc.is_connected()
    if not connected:
        return {
            "type": "scada_update",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "connected": False,
            "sensors": [],
            "motors": [],
            "thresholds": None,
        }

    sensors = plc.read_all_sensors()
    motors = plc.read_all_motors()
    thresholds = plc.read_thresholds()

    return {
        "type": "scada_update",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "connected": True,
        "sensors": [asdict(s) for s in sensors],
        "motors": [asdict(m) for m in motors],
        "thresholds": thresholds,
    }


# ── WebSocket clients ──────────────────────────────────────────────────

_ws_clients: set[WebSocket] = set()


async def _broadcast_loop(
    plc: SiloPLC,
    clients: set,
    stop_event: asyncio.Event,
) -> None:
    """Loop de broadcast: lee PLC cada 2s y envía a todos los WebSocket."""
    while not stop_event.is_set():
        try:
            data = await asyncio.to_thread(_read_plc_state, plc)
            msg = json.dumps(data)
            dead: set[WebSocket] = set()
            for ws in clients.copy():
                try:
                    await ws.send_text(msg)
                except Exception:
                    dead.add(ws)
            clients -= dead
        except Exception as e:
            print(f"[WS] Broadcast error: {e}")
        await asyncio.sleep(0.5)


# ── Lifespan ────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: conectar PLC e iniciar servicios (misma lógica que main_gui.py)
    print(f"[API] Conectando a PLC S7 en {PLC_IP}...")
    plc = SiloPLC(ip=PLC_IP, rack=PLC_RACK, slot=PLC_SLOT)
    bridge = None
    sim_service = None
    auto_service = None

    if not plc.connect():
        print("[API] PLC no disponible. Backend arranca en modo desconectado.")

    if SENSOR_SOURCE == "tms" and ENABLE_TMS_BRIDGE and plc.is_connected():
        provider = Tms6000Provider()
        bridge = TmsBridgeService(plc=plc, provider=provider)
        bridge.start()
    elif SENSOR_SOURCE == "sim":
        sim_service = SimTemperatureService(plc=plc)
        sim_service.start()
        # En simulacion, replicar la logica de FB2 (AutomationLogic del PLC)
        auto_service = AutomationService(plc=plc)
        auto_service.start()

    app.state.plc = plc
    app.state.bridge = bridge
    app.state.sim_service = sim_service
    app.state.auto_service = auto_service
    app.state.ws_clients = set()

    # Iniciar broadcast WebSocket
    stop_event = asyncio.Event()
    broadcast_task = asyncio.create_task(
        _broadcast_loop(plc, app.state.ws_clients, stop_event)
    )

    yield

    # Shutdown
    stop_event.set()
    broadcast_task.cancel()
    try:
        await broadcast_task
    except asyncio.CancelledError:
        pass
    if bridge is not None:
        bridge.stop()
    if sim_service is not None:
        sim_service.stop()
    if auto_service is not None:
        auto_service.stop()
    plc.disconnect()
    print("[API] Shutdown completo.")


# ── App ─────────────────────────────────────────────────────────────────

app = FastAPI(title="SCADA Silo Control", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


# ── WebSocket endpoint ──────────────────────────────────────────────────

@app.websocket("/ws/scada")
async def ws_scada(ws: WebSocket):
    await ws.accept()
    clients = app.state.ws_clients
    clients.add(ws)
    print(f"[WS] Cliente conectado ({len(clients)} total)")
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        clients.discard(ws)
        print(f"[WS] Cliente desconectado ({len(clients)} total)")


# ── Servir frontend estático en producción ──────────────────────────────

dist_path = Path(__file__).parent.parent / "web" / "dist"
if dist_path.exists():
    app.mount("/", StaticFiles(directory=str(dist_path), html=True), name="static")
