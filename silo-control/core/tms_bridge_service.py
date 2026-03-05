# core/tms_bridge_service.py
# Servicio puente: lee TMS6000 y escribe sensores logicos en DB1 del PLC.

import threading
import time

from core.plc_interface import SiloPLC
from core.tms6000_provider import Tms6000Provider
from config import TMS_BRIDGE_INTERVAL, TMS_MARK_INACTIVE_ON_FAILURE


class TmsBridgeService:
    """Bridge de sensores TMS6000 -> PLC DB1 (indices 0,1,2)."""

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
        print(f"[BRIDGE] TMS->PLC iniciado (cada {self._interval}s)")

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

            values = self._provider.read_logical_sensors()
            if values.ok:
                # T0 y T1: temperatura (humedad no usada en esos indices)
                self._plc.write_sensor(0, values.t0_temp or 0.0, 0.0, active=True)
                self._plc.write_sensor(1, values.t1_temp or 0.0, 0.0, active=True)
                # T2: humedad (temperatura no usada en ese indice)
                self._plc.write_sensor(2, 0.0, values.t2_hum or 0.0, active=True)
                # T3..T7 no existen en esta topologia.
                for i in range(3, 8):
                    self._plc.write_sensor(i, 0.0, 0.0, active=False)
            elif TMS_MARK_INACTIVE_ON_FAILURE:
                for i in range(8):
                    self._plc.write_sensor(i, 0.0, 0.0, active=False)

            time.sleep(self._interval)
