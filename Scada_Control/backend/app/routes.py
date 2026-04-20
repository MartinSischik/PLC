from fastapi import APIRouter, Request

from app.snapshot_builder import build_config_payload, build_snapshot

router = APIRouter(prefix="/api")


@router.get("/health")
async def health(request: Request) -> dict:
    plc = request.app.state.plc
    return {
        "ok": True,
        "connected": plc.is_connected(),
        "mode": "read_only_monitor",
    }


@router.get("/config")
async def config() -> dict:
    return build_config_payload()


@router.get("/snapshot")
async def snapshot(request: Request) -> dict:
    plc = request.app.state.plc
    return build_snapshot(plc)
