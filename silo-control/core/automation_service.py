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
from core.database import get_weather_thresholds
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

        # Solo silo_fan — únicos motores controlados por automatización de temperatura
        self._silo_fans: list[list[int]] = [
            [m.index for m in silo.motors if m.motor_type == 'silo_fan'] for silo in SILOS
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

        # Verificar condiciones meteorológicas exteriores → trigger independiente
        weather_cfg = get_weather_thresholds()
        weather_trigger = False
        if weather_cfg["weather_auto_enabled"]:
            try:
                from api.weather_service import get_current_conditions_sync
                current = get_current_conditions_sync()
                if current is not None:
                    t_out = current.get("temperature")
                    h_out = current.get("humidity")
                    if (t_out is not None and t_out > weather_cfg["ambient_temp_max"]) or \
                       (h_out is not None and h_out > weather_cfg["ambient_humid_max"]):
                        weather_trigger = True
                        print(f"[AUTO] Trigger clima exterior activo "
                              f"(T={t_out}°C H={h_out}%)")
            except Exception as e:
                print(f"[AUTO] Error leyendo clima exterior: {e}")

        # Indice sensor -> lectura para acceso rapido
        sensor_map = {s.index: s for s in sensors}
        motor_map  = {m.index: m for m in motors}

        for silo_idx, (sensor_indices, fan_indices) in enumerate(
            zip(self._silo_sensors, self._silo_fans)
        ):
            if not fan_indices:
                continue

            # ── Alarma de silo: cualquier sensor supera umbral (con histéresis) ──
            currently_alarm = self._alarm_state[silo_idx]
            silo_alarm = currently_alarm

            for si in sensor_indices:
                s = sensor_map.get(si)
                if s is None or not s.active:
                    continue
                threshold_temp  = temp_max  if not currently_alarm else (temp_max  - HYSTERESIS)
                threshold_humid = humid_max if not currently_alarm else (humid_max - HYSTERESIS)
                if (s.temperature > 0 and s.temperature > threshold_temp) or \
                   (s.humidity    > 0 and s.humidity    > threshold_humid):
                    silo_alarm = True
                    break
            else:
                # Ningún sensor superó el umbral → alarma silo se apaga
                if currently_alarm:
                    silo_alarm = False

            self._alarm_state[silo_idx] = silo_alarm

            # ── Trigger final: alarma silo OR clima exterior ──
            should_run = silo_alarm or weather_trigger

            # ── Aplicar solo a silo_fans en AUTO + HAB ──
            for mi in fan_indices:
                m = motor_map.get(mi)
                if m is None or not m.auto_mode or not m.enabled:
                    continue
                if m.cmd_run != should_run:
                    self._plc.set_motor_command(mi, should_run)
                    state = "ARRANCAR" if should_run else "DETENER"
                    reason = " [clima]" if weather_trigger and not silo_alarm else \
                             " [silo]"  if silo_alarm else ""
                    print(f"[AUTO] Silo {silo_idx+1} fan {mi}: {state}{reason}")
