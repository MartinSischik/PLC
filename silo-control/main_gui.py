# main_gui.py
# Entry point del monitor S7-1515-2 PN (TIA Portal / PLCSIM) con GUI.
#
# Uso:
#   cd silo-control
#   python main_gui.py

from config import PLC_IP, PLC_RACK, PLC_SLOT
from core.plc_interface import SiloPLC
from gui.app import SiloApp


def main() -> None:
    """Conecta al PLC S7 y abre la ventana grafica."""

    print(f"[PLC] Conectando a S7 en {PLC_IP} (rack={PLC_RACK}, slot={PLC_SLOT})...")
    plc = SiloPLC(ip=PLC_IP, rack=PLC_RACK, slot=PLC_SLOT)

    if not plc.connect():
        # La app igual arranca pero mostrara "DESCONECTADO" en el header.
        print("[PLC] Advertencia: PLC no disponible. La GUI arrancara en modo desconectado.")

    app = SiloApp(plc=plc)
    app.mainloop()

    print("[PLC] Aplicacion cerrada.")


if __name__ == "__main__":
    main()
