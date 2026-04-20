# diagnose_sensor_overwrite.py
# Diagnostica si DB1 es sobreescrito por logica del PLC despues de una escritura Python.

import time

from config import PLC_IP, PLC_RACK, PLC_SLOT
from core.plc_interface import SiloPLC


def _fmt(sensor) -> str:
    if sensor is None:
        return "None"
    return f"idx={sensor.index} T={sensor.temperature:.2f} H={sensor.humidity:.2f} A={sensor.active}"


def main() -> None:
    plc = SiloPLC(ip=PLC_IP, rack=PLC_RACK, slot=PLC_SLOT)
    if not plc.connect():
        print("[DIAG] No se pudo conectar al PLC")
        return

    print("[DIAG] Iniciando prueba de sobreescritura en DB1...")
    print("[DIAG] Escribiendo T0/T1/H2 y verificando lectura inmediata y diferida")

    try:
        cycle = 0
        while True:
            cycle += 1
            # Valores distintivos para detectar sobrescritura facilmente.
            t0 = 31.11 + (cycle % 5)
            t1 = 36.22 + (cycle % 7)
            h2 = 58.33 + (cycle % 3)

            ok0 = plc.write_sensor(0, t0, 0.0, active=True)
            ok1 = plc.write_sensor(1, t1, 0.0, active=True)
            ok2 = plc.write_sensor(2, 0.0, h2, active=True)

            if not (ok0 and ok1 and ok2):
                print(f"[DIAG][{cycle}] ERROR write_sensor -> ok0={ok0} ok1={ok1} ok2={ok2}")
                time.sleep(1.0)
                continue

            # Lectura inmediata tras escribir.
            s0_now = plc.read_sensor(0)
            s1_now = plc.read_sensor(1)
            s2_now = plc.read_sensor(2)

            # Lectura diferida; si aqui cambia a 0, probablemente el PLC lo pisa en scan.
            time.sleep(0.25)
            s0_late = plc.read_sensor(0)
            s1_late = plc.read_sensor(1)
            s2_late = plc.read_sensor(2)

            print(f"\n[DIAG][{cycle}] TARGET: T0={t0:.2f} T1={t1:.2f} H2={h2:.2f}")
            print(f"  NOW : {_fmt(s0_now)} | {_fmt(s1_now)} | {_fmt(s2_now)}")
            print(f"  LATE: {_fmt(s0_late)} | {_fmt(s1_late)} | {_fmt(s2_late)}")

            def _close(a: float, b: float, eps: float = 0.2) -> bool:
                return abs(a - b) <= eps

            late_ok = (
                s0_late is not None and s1_late is not None and s2_late is not None
                and _close(s0_late.temperature, t0)
                and _close(s1_late.temperature, t1)
                and _close(s2_late.humidity, h2)
            )

            if not late_ok:
                print("  [WARN] DB1 parece ser sobreescrito despues de escribir desde Python.")
                print("         Revisa logica en TIA que escriba DB1.SensorData en cada scan.")

            time.sleep(1.0)

    except KeyboardInterrupt:
        pass
    finally:
        plc.disconnect()
        print("[DIAG] Fin")


if __name__ == "__main__":
    main()
