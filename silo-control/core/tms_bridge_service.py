# core/tms_bridge_service.py
# Servicio puente: lee TMS6000 y escribe sensores en DB1 del PLC.
#
# Usa TMS_SENSOR_MAP de config.py para mapear registros Modbus a slots DB1.
# Soporta N sensores — agregar uno es agregar una linea en TMS_SENSOR_MAP.

import threading
import time

from core.plc_interface import SiloPLC
from core.tms6000_provider import Tms6000Provider
from config import (
    TMS_BRIDGE_INTERVAL,
    TMS_MARK_INACTIVE_ON_FAILURE,
    TMS_SENSOR_MAP,
    SENSOR_COUNT,
)


class TmsBridgeService:
    """Bridge generico TMS6000 -> PLC DB1 usando TMS_SENSOR_MAP."""

    def __init__(
        self,
        plc: SiloPLC,
        provider: Tms6000Provider,
        interval: float = TMS_BRIDGE_INTERVAL,
    ) -> None:
        self._plc = plc
        self._provider = provider
        self._interval = interval
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, name="TmsBridge", daemon=True)
        self._thread.start()
        print(f"[BRIDGE] TMS->PLC iniciado (cada {self._interval}s, "
              f"{len(TMS_SENSOR_MAP)} sensores mapeados)")

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=self._interval + 1)
        self._provider.disconnect()
        print("[BRIDGE] TMS->PLC detenido")

    def _loop(self) -> None:
        while self._running:
            if not self._provider.is_connected():
                self._provider.connect()

            readings = self._provider.read_sensors()
            all_ok = all(val is not None for _, val in readings.values())

            if all_ok or not TMS_MARK_INACTIVE_ON_FAILURE:
                # Escribir valores leidos en DB1
                for db_idx, (kind, val) in readings.items():
                    if val is None:
                        continue
                    if kind == "temp":
                        self._plc.write_sensor(db_idx, val, 0.0, active=True)
                    else:
                        self._plc.write_sensor(db_idx, 0.0, val, active=True)

                # Desactivar slots que NO estan en el mapa
                mapped = set(readings.keys())
                for i in range(SENSOR_COUNT):
                    if i not in mapped:
                        self._plc.write_sensor(i, 0.0, 0.0, active=False)

            elif TMS_MARK_INACTIVE_ON_FAILURE:
                # Fallo total: desactivar todos los sensores
                for i in range(SENSOR_COUNT):
                    self._plc.write_sensor(i, 0.0, 0.0, active=False)

            time.sleep(self._interval)
