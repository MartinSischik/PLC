# core/sensor_simulator.py
# Simulador de sensores de temperatura y humedad.
#
# Como no hay hardware físico en el entorno de desarrollo, esta clase
# genera valores sintéticos mediante funciones sinusoidales con ruido
# aleatorio y los escribe en DB1 del PLC a intervalos regulares.
#
# Sensores 0-3 → active=True  (simulan sensores conectados)
# Sensores 4-7 → active=False (simulan sensores desconectados)

import math
import random
import threading
import time

from core.plc_interface import SiloPLC
from config import SIMULATION_INTERVAL


class SensorSimulator:
    """Escribe valores simulados de temperatura y humedad en DB1 del PLC.

    Corre en un hilo daemon para no bloquear el programa principal.
    Cada sensor activo tiene un desfase de fase diferente, de modo que
    las lecturas varían de forma independiente y natural entre sí.

    Uso::

        sim = SensorSimulator(plc)
        sim.start()
        # ... programa principal ...
        sim.stop()
    """

    # Desfases de fase (en radianes) para diferenciar cada sensor.
    # Se aplican tanto a temperatura como a humedad.
    _PHASE_OFFSETS = [0.0, 0.8, 1.6, 2.4]   # uno por sensor activo (0-3)

    def __init__(
        self,
        plc:      SiloPLC,
        interval: float = SIMULATION_INTERVAL,
    ) -> None:
        """Inicializa el simulador.

        Args:
            plc:      Instancia de SiloPLC ya conectada al PLC.
            interval: Segundos entre cada actualización de los sensores.
        """
        self._plc      = plc
        self._interval = interval
        self._running  = False
        self._thread: threading.Thread | None = None

    # ── Ciclo de vida ──────────────────────────────────────────────────────

    def start(self) -> None:
        """Arranca el hilo del simulador.

        Si el simulador ya está corriendo, este método no hace nada.
        """
        if self._running:
            print("[SIM] El simulador ya está en marcha.")
            return

        self._running = True
        self._thread  = threading.Thread(
            target=self._loop,
            name="SensorSimulator",
            daemon=True,      # muere automáticamente cuando el proceso principal termina
        )
        self._thread.start()
        print(f"[SIM] Simulador iniciado (intervalo={self._interval}s, sensores 0-3 activos).")

    def stop(self) -> None:
        """Detiene el hilo del simulador de forma ordenada."""
        if not self._running:
            return
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=self._interval + 1)
        print("[SIM] Simulador detenido.")

    def is_running(self) -> bool:
        """Retorna True si el simulador está activo."""
        return self._running and (self._thread is not None) and self._thread.is_alive()

    # ── Bucle interno ──────────────────────────────────────────────────────

    def _loop(self) -> None:
        """Bucle principal del hilo: genera y escribe valores en DB1."""
        while self._running:
            t = time.time()   # tiempo absoluto para la función sinusoidal

            # Sensores 0-3: activos, con datos simulados
            for i in range(4):
                phase = self._PHASE_OFFSETS[i]
                temp  = self._simulate_temperature(t, phase)
                hum   = self._simulate_humidity(t, phase)
                self._plc.write_sensor(i, temp, hum, active=True)

            # Sensores 4-7: inactivos (sin datos)
            for i in range(4, 8):
                self._plc.write_sensor(i, 0.0, 0.0, active=False)

            time.sleep(self._interval)

    # ── Generadores de valores ─────────────────────────────────────────────

    @staticmethod
    def _simulate_temperature(t: float, phase: float) -> float:
        """Genera un valor de temperatura simulado.

        Fórmula: 30 + 10 * sin(t/30 + phase) + ruido ∈ [-2, 2]
        Rango aproximado: 18-42 °C

        Args:
            t:     Tiempo Unix actual (para variación lenta).
            phase: Desfase en radianes (diferencia los sensores entre sí).

        Returns:
            Temperatura en °C redondeada a 2 decimales.
        """
        base  = 30.0 + 10.0 * math.sin(t / 30.0 + phase)
        noise = random.uniform(-2.0, 2.0)
        return round(base + noise, 2)

    @staticmethod
    def _simulate_humidity(t: float, phase: float) -> float:
        """Genera un valor de humedad simulado.

        Fórmula: 65 + 15 * sin(t/45 + 1.5 + phase) + ruido ∈ [-3, 3]
        Rango aproximado: 47-83 %RH

        El periodo más largo (45 s vs 30 s) y el desfase adicional de 1.5 rad
        hacen que la humedad varíe de forma independiente a la temperatura.

        Args:
            t:     Tiempo Unix actual.
            phase: Desfase en radianes.

        Returns:
            Humedad relativa en %RH redondeada a 2 decimales.
        """
        base  = 65.0 + 15.0 * math.sin(t / 45.0 + 1.5 + phase)
        noise = random.uniform(-3.0, 3.0)
        return round(base + noise, 2)
