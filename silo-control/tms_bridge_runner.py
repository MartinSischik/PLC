# tms_bridge_runner.py
# Ejecuta el puente TMS6000 -> PLC en modo standalone.

import time

from config import PLC_IP, PLC_RACK, PLC_SLOT
from core.plc_interface import SiloPLC
from core.tms6000_provider import Tms6000Provider
from core.tms_bridge_service import TmsBridgeService


def main() -> None:
    plc = SiloPLC(ip=PLC_IP, rack=PLC_RACK, slot=PLC_SLOT)
    if not plc.connect():
        print("[BRIDGE] No se pudo conectar al PLC. Abortando.")
        return

    provider = Tms6000Provider()
    bridge = TmsBridgeService(plc=plc, provider=provider)
    bridge.start()

    print("[BRIDGE] Corriendo. Ctrl+C para salir.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        bridge.stop()
        plc.disconnect()


if __name__ == "__main__":
    main()
