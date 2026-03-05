# core/sim_temperature_service.py
# Servicio de simulacion de T0/T1 temperatura y T2 humedad en DB1.

import math
import random
import threading
import time

from core.plc_interface import SiloPLC
from config import SIMULATION_INTERVAL


class SimTemperatureService:
    """Escribe sensores simulados en DB1 para topologia T0/T1/H2."""

    def __init__(self, plc: SiloPLC, interval: float = SIMULATION_INTERVAL) -> None:
        self._plc = plc
        self._interval = interval
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, name="SimTemperatureService", daemon=True)
        self._thread.start()
        print(f"[SIM] Servicio de simulacion iniciado (cada {self._interval}s)")

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=self._interval + 1)
        print("[SIM] Servicio de simulacion detenido")

    def _loop(self) -> None:
        while self._running:
            t = time.time()
            t0 = self._temp_wave(t, 0.0)
            t1 = self._temp_wave(t, 1.1)
            h2 = self._hum_wave(t)

            ok0 = self._plc.write_sensor(0, t0, 0.0, active=True)
            ok1 = self._plc.write_sensor(1, t1, 0.0, active=True)
            ok2 = self._plc.write_sensor(2, 0.0, h2, active=True)
            for i in range(3, 8):
                self._plc.write_sensor(i, 0.0, 0.0, active=False)

            if not (ok0 and ok1 and ok2):
                print(f"[SIM] Error escribiendo DB1 (ok0={ok0}, ok1={ok1}, ok2={ok2})")

            time.sleep(self._interval)

    @staticmethod
    def _temp_wave(t: float, phase: float) -> float:
        return round(28.0 + 8.0 * math.sin(t / 25.0 + phase) + random.uniform(-1.5, 1.5), 2)

    @staticmethod
    def _hum_wave(t: float) -> float:
        return round(60.0 + 12.0 * math.sin(t / 40.0 + 1.2) + random.uniform(-2.0, 2.0), 2)
