# main_gui.py
# Entry point del monitor S7-1515-2 PN (TIA Portal / PLCSIM) con GUI.
#
# Uso:
#   cd silo-control
#   python main_gui.py

from config import PLC_IP, PLC_RACK, PLC_SLOT, ENABLE_TMS_BRIDGE, SENSOR_SOURCE
from core.plc_interface import SiloPLC
from core.tms6000_provider import Tms6000Provider
from core.tms_bridge_service import TmsBridgeService
from core.sim_temperature_service import SimTemperatureService
from gui.app import SiloApp


def main() -> None:
    """Conecta al PLC S7 y abre la ventana grafica."""

    print(f"[PLC] Conectando a S7 en {PLC_IP} (rack={PLC_RACK}, slot={PLC_SLOT})...")
    plc = SiloPLC(ip=PLC_IP, rack=PLC_RACK, slot=PLC_SLOT)
    bridge: TmsBridgeService | None = None
    sim_service: SimTemperatureService | None = None

    if not plc.connect():
        # La app igual arranca pero mostrara "DESCONECTADO" en el header.
        print("[PLC] Advertencia: PLC no disponible. La GUI arrancara en modo desconectado.")

    if SENSOR_SOURCE == "tms" and ENABLE_TMS_BRIDGE and plc.is_connected():
        provider = Tms6000Provider()
        bridge = TmsBridgeService(plc=plc, provider=provider)
        bridge.start()
    elif SENSOR_SOURCE == "tms" and ENABLE_TMS_BRIDGE:
        print("[BRIDGE] No iniciado porque PLC no esta conectado.")
    elif SENSOR_SOURCE == "sim":
        if plc.is_connected():
            sim_service = SimTemperatureService(plc=plc)
            sim_service.start()
        else:
            print("[SIM] No iniciado porque PLC no esta conectado.")
    elif SENSOR_SOURCE == "none":
        print("[SENSORS] SENSOR_SOURCE='none': DB1 usara valores que existan en PLC.")

    app = SiloApp(plc=plc)
    try:
        app.mainloop()
    finally:
        if bridge is not None:
            bridge.stop()
        if sim_service is not None:
            sim_service.stop()

    print("[PLC] Aplicacion cerrada.")


if __name__ == "__main__":
    main()
