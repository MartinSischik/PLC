# simulate_temperatures.py
# Script separado para simular temperaturas/humedad en DB1 del PLC.

import time

from config import PLC_IP, PLC_RACK, PLC_SLOT
from core.plc_interface import SiloPLC
from core.sim_temperature_service import SimTemperatureService


def main() -> None:
    plc = SiloPLC(ip=PLC_IP, rack=PLC_RACK, slot=PLC_SLOT)
    if not plc.connect():
        print("[SIM-TEMP] No se pudo conectar al PLC.")
        return

    sim = SimTemperatureService(plc=plc)
    sim.start()
    print("[SIM-TEMP] Simulador iniciado. Ctrl+C para salir.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        sim.stop()
        plc.disconnect()
        print("[SIM-TEMP] Simulador detenido.")


if __name__ == "__main__":
    main()
