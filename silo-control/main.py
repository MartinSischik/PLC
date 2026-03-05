# main.py
# Entry point del sistema SCADA para control de silos industriales.
#
# Responsabilidades:
#   1. Conectar al PLC.
#   2. Arrancar el simulador de sensores (escribe en DB1 cada 2 s).
#   3. Mostrar un dashboard en consola que se refresca cada 3 segundos.
#   4. Aceptar comandos por teclado en un hilo separado para controlar
#      motores y umbrales sin interrumpir el ciclo de monitoreo.

import sys
import threading
import time
from typing import Optional

from config import PLC_IP, PLC_RACK, PLC_SLOT
from core.plc_interface import SiloPLC, SensorReading, MotorStatus


# ══════════════════════════════════════════════════════════════════════════════
# Constantes de presentación
# ══════════════════════════════════════════════════════════════════════════════

MONITOR_INTERVAL = 3.0   # segundos entre cada refresco del dashboard

HEADER = """
╔══════════════════════════════════════════════════════════════════════╗
║         S7-1515-2 PN / PLCSIM – MONITOR DE SILO (CLI)               ║
║         Sensores, motores y automatización en DBs del PLC           ║
╠══════════════════════════════════════════════════════════════════════╣
║  COMANDOS DISPONIBLES                                                ║
║  ─────────────────────────────────────────────────────────────────  ║
║  start N      → encender ventilador N  (N = 0-3)                    ║
║  stop N       → apagar ventilador N                                 ║
║  auto N       → poner ventilador N en modo automático               ║
║  manual N     → poner ventilador N en modo manual                   ║
║  enable N     → habilitar ventilador N                              ║
║  disable N    → deshabilitar ventilador N                           ║
║  temp XX.X    → cambiar umbral máximo de temperatura (°C)           ║
║  quit         → desconectar y salir                                 ║
╚══════════════════════════════════════════════════════════════════════╝
"""


# ══════════════════════════════════════════════════════════════════════════════
# Funciones de presentación del dashboard
# ══════════════════════════════════════════════════════════════════════════════

def _bool_icon(value: bool, true_str: str = "ON ", false_str: str = "OFF") -> str:
    """Retorna una cadena coloreada para representar un booleano."""
    return true_str if value else false_str


def print_dashboard(
    plc: SiloPLC,
    sensors: list[SensorReading],
    motors:  list[MotorStatus],
    thresholds: Optional[dict],
) -> None:
    """Imprime el estado actual del silo en consola.

    Args:
        plc:        Instancia del PLC (para estado de conexión).
        sensors:    Lista de SensorReading leída desde DB1.
        motors:     Lista de MotorStatus leída desde DB2.
        thresholds: Diccionario leído desde DB3, o None si hubo error.
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    connected = plc.is_connected()

    print("\n" + "═" * 70)
    print(f"  S7-1515-2 PN  |  {timestamp}  |  PLC: {'CONECTADO' if connected else 'DESCONECTADO'}")
    print("═" * 70)

    # ── Cables sensor ──────────────────────────────────────────────────────
    print("\n  [ SENSORES DB1 ]")
    print(f"  {'ID':>3}  {'Estado':>10}  {'Max (°C)':>10}  {'Avg (°C)':>10}")
    print("  " + "─" * 42)
    for s in sensors:
        estado = "ACTIVO " if s.active else "inactivo"
        temp   = f"{s.temperature:>9.2f}" if s.active else "        -"
        hum    = f"{s.humidity:>9.2f}"    if s.active else "        -"
        print(f"  [{s.index}]  {estado:>10}  {temp}  {hum}")

    # ── Ventiladores ───────────────────────────────────────────────────────
    print("\n  [ VENTILACIÓN ]")
    print(f"  {'ID':>3}  {'Habilitado':>10}  {'Modo':>8}  {'Corriendo':>10}  {'Cmd':>6}  {'Falla':>6}")
    print("  " + "─" * 58)
    for m in motors:
        habilitado = _bool_icon(m.enabled,    "SI ",  "NO ")
        modo       = "AUTO  " if m.auto_mode else "MANUAL"
        corriendo  = _bool_icon(m.is_running, "SI ",  "NO ")
        cmd        = _bool_icon(m.cmd_run,    "RUN",  "---")
        falla      = _bool_icon(m.fault,      "FALLA","  OK ")
        print(f"  [{m.index}]  {habilitado:>10}  {modo:>8}  {corriendo:>10}  {cmd:>6}  {falla:>6}")

    # ── Umbrales y alarma ─────────────────────────────────────────────────
    print("\n  [ AUTOMATIZACIÓN ]")
    if thresholds:
        alarma   = "*** ALARMA ACTIVA ***" if thresholds["alarm_active"] else "Sin alarma"
        auto_gbl = "GLOBAL AUTO" if thresholds["auto_global"] else "Global manual"
        print(f"  Temp máx: {thresholds['temp_max']:>6.1f} °C  |  "
              f"Temp mín: {thresholds['temp_min']:>6.1f} °C")
        print(f"  Estado: {auto_gbl}  |  {alarma}")
    else:
        print("  (error al leer DB3)")

    print("\n  Escribe un comando y pulsa Enter > ", end="", flush=True)


# ══════════════════════════════════════════════════════════════════════════════
# Procesador de comandos de teclado
# ══════════════════════════════════════════════════════════════════════════════

def process_command(line: str, plc: SiloPLC) -> bool:
    """Interpreta y ejecuta un comando de texto.

    Args:
        line: Línea leída del stdin (ya sin salto de línea).
        plc:  Instancia de SiloPLC conectada.

    Returns:
        False si el comando es "quit" (señal para terminar), True en el resto.
    """
    parts = line.strip().lower().split()
    if not parts:
        return True

    cmd = parts[0]

    # ── quit ──────────────────────────────────────────────────────────────
    if cmd == "quit":
        return False

    # ── comandos con índice de motor ──────────────────────────────────────
    if cmd in ("start", "stop", "auto", "manual", "enable", "disable"):
        if len(parts) < 2:
            print(f"  [!] Uso: {cmd} N  (N = 0-3)")
            return True
        try:
            n = int(parts[1])
        except ValueError:
            print(f"  [!] '{parts[1]}' no es un número válido.")
            return True

        if not (0 <= n <= 3):
            print(f"  [!] Índice {n} fuera de rango.  Motores válidos: 0-3.")
            return True

        if cmd == "start":
            ok = plc.set_motor_command(n, True)
        elif cmd == "stop":
            ok = plc.set_motor_command(n, False)
        elif cmd == "auto":
            ok = plc.set_motor_auto_mode(n, True)
        elif cmd == "manual":
            ok = plc.set_motor_auto_mode(n, False)
        elif cmd == "enable":
            ok = plc.set_motor_enabled(n, True)
        else:   # disable
            ok = plc.set_motor_enabled(n, False)

        status = "OK" if ok else "ERROR"
        print(f"  [{status}] {cmd.upper()} ventilador {n}")
        return True

    # ── temp ──────────────────────────────────────────────────────────────
    if cmd == "temp":
        if len(parts) < 2:
            print(f"  [!] Uso: temp XX.X")
            return True
        try:
            valor = float(parts[1])
        except ValueError:
            print(f"  [!] '{parts[1]}' no es un número válido.")
            return True

        cfg = plc.read_thresholds()
        if cfg is None:
            print("  [ERROR] No se pudo leer los umbrales actuales.")
            return True

        ok = plc.set_temperature_thresholds(temp_max=valor, temp_min=cfg["temp_min"])
        print(f"  [{'OK' if ok else 'ERROR'}] Umbral temperatura máxima → {valor} °C")
        return True

    # ── comando desconocido ───────────────────────────────────────────────
    print(f"  [!] Comando desconocido: '{cmd}'.  Escribe 'quit' para salir.")
    return True


# ══════════════════════════════════════════════════════════════════════════════
# Hilo de entrada de teclado
# ══════════════════════════════════════════════════════════════════════════════

class InputThread(threading.Thread):
    """Hilo que lee líneas de stdin y las procesa como comandos.

    Corre como daemon para que no impida la salida del programa principal.
    """

    def __init__(self, plc: SiloPLC, stop_event: threading.Event) -> None:
        super().__init__(name="InputThread", daemon=True)
        self._plc        = plc
        self._stop_event = stop_event

    def run(self) -> None:
        """Lee stdin indefinidamente hasta recibir 'quit' o EOF."""
        while not self._stop_event.is_set():
            try:
                line = input()
            except (EOFError, KeyboardInterrupt):
                self._stop_event.set()
                break
            if not process_command(line, self._plc):
                self._stop_event.set()
                break


# ══════════════════════════════════════════════════════════════════════════════
# Bucle de monitoreo
# ══════════════════════════════════════════════════════════════════════════════

def monitoring_loop(
    plc:       SiloPLC,
    stop_event: threading.Event,
) -> None:
    """Refresca el dashboard en consola cada MONITOR_INTERVAL segundos.

    Args:
        plc:        Instancia de SiloPLC conectada.
        stop_event: Evento que indica cuándo debe terminar el bucle.
    """
    while not stop_event.is_set():
        sensors    = plc.read_all_sensors()
        motors     = plc.read_all_motors()
        thresholds = plc.read_thresholds()
        print_dashboard(plc, sensors, motors, thresholds)
        stop_event.wait(timeout=MONITOR_INTERVAL)


# ══════════════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    """Función principal del sistema SCADA."""

    print(HEADER)
    print(f"  Conectando al PLC en {PLC_IP} (rack={PLC_RACK}, slot={PLC_SLOT})...")

    # 1. Conectar al PLC S7 / PLCSIM
    plc = SiloPLC(ip=PLC_IP, rack=PLC_RACK, slot=PLC_SLOT)
    if not plc.connect():
        print("\n  [ERROR FATAL] No se pudo conectar al PLC. Verifica:")
        print(f"    • Que la IP {PLC_IP} sea accesible desde esta maquina.")
        print("    • Que rack/slot correspondan a la CPU (S7-1500: 0/1).")
        print("    • Que PLCSIM/TIA tenga el proyecto cargado y en RUN.")
        sys.exit(1)

    # 3. Evento compartido entre hilos para coordinar la salida
    stop_event = threading.Event()

    # 4. Hilo de entrada de teclado
    input_thread = InputThread(plc, stop_event)
    input_thread.start()

    # 5. Bucle de monitoreo (corre en el hilo principal)
    try:
        monitoring_loop(plc, stop_event)
    except KeyboardInterrupt:
        print("\n\n  [INFO] Interrupción de teclado recibida (Ctrl+C).")
        stop_event.set()

    # 5. Limpieza ordenada
    print("  Desconectando del PLC...")
    plc.disconnect()
    print("  Monitor S7-1515-2 PN terminado.\n")


if __name__ == "__main__":
    main()
