import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import CORS_ORIGINS, PLC_IP, PLC_RACK, PLC_SLOT, REFRESH_SECONDS
from app.plc_client import ReadOnlyPlcClient
from app.routes import router
from app.snapshot_builder import build_snapshot


async def _broadcast_loop(app: FastAPI, stop_event: asyncio.Event) -> None:
    while not stop_event.is_set():
        try:
            payload = await asyncio.to_thread(build_snapshot, app.state.plc)
            message = json.dumps(payload)

            dead_clients: set[WebSocket] = set()
            for ws in app.state.ws_clients.copy():
                try:
                    await ws.send_text(message)
                except Exception:
                    dead_clients.add(ws)

            app.state.ws_clients -= dead_clients
        except Exception as exc:
            print(f"[WS] broadcast error: {exc}")

        await asyncio.sleep(REFRESH_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    plc = ReadOnlyPlcClient(ip=PLC_IP, rack=PLC_RACK, slot=PLC_SLOT)
    connected = plc.connect()
    if not connected:
        print("[API] PLC unavailable. Running disconnected read-only mode.")

    app.state.plc = plc
    app.state.ws_clients = set()

    stop_event = asyncio.Event()
    broadcast_task = asyncio.create_task(_broadcast_loop(app, stop_event))

    app.state.stop_event = stop_event
    app.state.broadcast_task = broadcast_task

    yield

    stop_event.set()
    broadcast_task.cancel()
    try:
        await broadcast_task
    except asyncio.CancelledError:
        pass

    plc.disconnect()


app = FastAPI(title="Scada_Control Read-Only API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(router)


@app.websocket("/ws/monitor")
async def ws_monitor(ws: WebSocket):
    await ws.accept()
    clients = app.state.ws_clients
    clients.add(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        clients.discard(ws)


web_path = Path(__file__).resolve().parents[2] / "web"
if web_path.exists():
    app.mount("/", StaticFiles(directory=str(web_path), html=True), name="web")
