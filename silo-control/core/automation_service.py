# core/automation_service.py
# Replica la logica de FB2 (AutomationLogic) del PLC en modo simulacion.
#
# Cuando el PLC real esta conectado, FB2 se ejecuta en el PLC y este servicio
# NO debe iniciarse. Solo se usa cuando SENSOR_SOURCE == "sim" o sin PLC real.
#
# Logica:
#   - Cada ciclo lee sensores, motores y umbrales desde el PLC (DB1/DB2/DB3).
#   - Por cada silo: si cualquier sensor supera temp_max o humid_max, hay alarma.
#   - Motores en auto_mode + enabled + silo en alarma -> cmd_run = True.
#   - Motores en auto_mode + enabled + silo sin alarma -> cmd_run = False.
#   - Motores en manual o deshabilitados: no se tocan.

import threading
import time

from core.plc_interface import SiloPLC
from config import SILOS, SIMULATION_INTERVAL


# Margen de histéresis: el motor se apaga solo cuando el valor baja
# este margen por debajo del umbral (evita on/off rápido en el límite).
HYSTERESIS = 2.0


class AutomationService:
    """Servicio de automatizacion por software (equivalente a FB2 en el PLC)."""

    def __init__(self, plc: SiloPLC, interval: float = SIMULATION_INTERVAL) -> None:
        self._plc = plc
        self._interval = interval
        self._running = False
        self._thread: threading.Thread | None = None

        # Mapa silo_index -> lista de motor indices
        self._silo_motors: list[list[int]] = [
            [m.index for m in silo.motors] for silo in SILOS
        ]
        # Mapa silo_index -> lista de sensor indices
        self._silo_sensors: list[list[int]] = [
            [s.index for s in silo.sensors] for silo in SILOS
        ]
        # Estado de alarma por silo (para histéresis)
        self._alarm_state: list[bool] = [False] * len(SILOS)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, name="AutomationService", daemon=True)
        self._thread.start()
        print(f"[AUTO] Servicio de automatizacion iniciado (cada {self._interval}s)")

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=self._interval + 1)
        print("[AUTO] Servicio de automatizacion detenido")

    def _loop(self) -> None:
        while self._running:
            try:
                self._tick()
            except Exception as e:
                print(f"[AUTO] Error en ciclo: {e}")
            time.sleep(self._interval)

    def _tick(self) -> None:
        sensors = self._plc.read_all_sensors()
        motors  = self._plc.read_all_motors()
        thresholds = self._plc.read_thresholds()

        if not sensors or not motors or thresholds is None:
            return

        temp_max  = thresholds.get("temp_max",  35.0)
        humid_max = thresholds.get("humid_max", 70.0)

        # Indice sensor -> lectura para acceso rapido
        sensor_map = {s.index: s for s in sensors}
        motor_map  = {m.index: m for m in motors}

        for silo_idx, (sensor_indices, motor_indices) in enumerate(
            zip(self._silo_sensors, self._silo_motors)
        ):
            # Histéresis: se activa al superar el umbral,
            # se desactiva solo cuando baja HYSTERESIS por debajo.
            currently_alarm = self._alarm_state[silo_idx]
            new_alarm = currently_alarm  # mantener estado por defecto

            for si in sensor_indices:
                s = sensor_map.get(si)
                if s is None or not s.active:
                    continue
                if not currently_alarm:
                    # Condicion de activacion: superar umbral
                    if s.temperature > temp_max or s.humidity > humid_max:
                        new_alarm = True
                        break
                else:
                    # Condicion de desactivacion: bajar del umbral con margen
                    if s.temperature > (temp_max - HYSTERESIS) or s.humidity > (humid_max - HYSTERESIS):
                        new_alarm = True
                        break
                    else:
                        new_alarm = False

            self._alarm_state[silo_idx] = new_alarm

            # Aplicar logica a cada motor del silo
            for mi in motor_indices:
                m = motor_map.get(mi)
                if m is None:
                    continue
                if not m.auto_mode or not m.enabled:
                    continue  # no tocar motores en manual o deshabilitados
                if m.cmd_run != new_alarm:
                    self._plc.set_motor_command(mi, new_alarm)
                    state = "ARRANCAR" if new_alarm else "DETENER"
                    print(f"[AUTO] Silo {silo_idx+1} motor {mi}: {state} "
                          f"(alarma={new_alarm})")
