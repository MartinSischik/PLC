# core/sim_temperature_service.py
# Servicio de simulacion de sensores en DB1.
#
# Genera parametros de simulacion automaticamente a partir de config.SILOS.
# Si se agregan o quitan sensores en config.py, el simulador se adapta solo.

import math
import random
import threading
import time

from core.plc_interface import SiloPLC
from config import SIMULATION_INTERVAL, SILOS


def _build_sensor_params() -> dict:
    """Genera parametros de simulacion para cada sensor definido en SILOS.

    Formato: {index: (tipo, base, amplitud, periodo, fase, ruido)}
    Los valores se asignan automaticamente para que cada sensor tenga
    lecturas distintas y realistas.
    """
    params = {}
    # Bases y rangos tipicos por tipo
    temp_bases = [28.0, 26.5, 27.0, 29.5, 25.0, 30.0, 27.5, 28.5]
    hum_bases  = [60.0, 62.0, 58.0, 64.0, 61.0, 59.0, 63.0, 57.0]
    ti = 0  # indice de temperatura
    hi = 0  # indice de humedad

    for silo in SILOS:
        for s_cfg in silo.sensors:
            idx = s_cfg.index
            # Fase unica por sensor para que no se sincronicen
            phase = idx * 0.9 + 0.3

            if s_cfg.show_humidity:
                base = hum_bases[hi % len(hum_bases)]
                params[idx] = ("hum", base, 11.0, 35.0 + idx * 3, phase, 2.0)
                hi += 1
            else:
                base = temp_bases[ti % len(temp_bases)]
                params[idx] = ("temp", base, 7.5, 25.0 + idx * 2, phase, 1.3)
                ti += 1

    return params


class SimTemperatureService:
    """Escribe sensores simulados en todos los slots activos de DB1."""

    def __init__(self, plc: SiloPLC, interval: float = SIMULATION_INTERVAL) -> None:
        self._plc = plc
        self._interval = interval
        self._running = False
        self._thread: threading.Thread | None = None
        self._sensor_params = _build_sensor_params()

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, name="SimTemperatureService", daemon=True)
        self._thread.start()
        print(f"[SIM] Servicio de simulacion iniciado (cada {self._interval}s, "
              f"{len(self._sensor_params)} sensores)")

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=self._interval + 1)
        print("[SIM] Servicio de simulacion detenido")

    def _loop(self) -> None:
        errors: list[int] = []
        while self._running:
            t = time.time()
            errors.clear()

            for idx, (tipo, base, amp, period, phase, noise) in self._sensor_params.items():
                val = round(base + amp * math.sin(t / period + phase)
                            + random.uniform(-noise, noise), 2)
                if tipo == "temp":
                    ok = self._plc.write_sensor(idx, val, 0.0, active=True)
                else:
                    ok = self._plc.write_sensor(idx, 0.0, val, active=True)
                if not ok:
                    errors.append(idx)

            if errors:
                print(f"[SIM] Error escribiendo sensores: {errors}")

            time.sleep(self._interval)
