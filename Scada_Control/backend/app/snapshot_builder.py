from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from app.config import HUMID_WARN_MARGIN, SILOS, TEMP_WARN_MARGIN


def build_config_payload() -> dict[str, Any]:
    silos = []
    for silo in SILOS:
        silos.append(
            {
                "name": silo.name,
                "sensors": [asdict(s) for s in silo.sensors],
                "motors": [asdict(m) for m in silo.motors],
                "level_sensors": [asdict(l) for l in silo.level_sensors],
                "gas_sensors": [asdict(g) for g in silo.gas_sensors],
                "gates": [asdict(g) for g in silo.gates],
            }
        )
    return {"silos": silos}


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_snapshot(plc) -> dict[str, Any]:
    connected = plc.is_connected()

    analog_rows = plc.read_analog_sensors() if connected else []
    motor_rows = plc.read_motors() if connected else []
    gate_rows = plc.read_gates() if connected else []
    thresholds = plc.read_thresholds() if connected else None
    monitor_rows = plc.read_level_gas_monitor(len(SILOS)) if connected else []

    analog_by_index = {row["index"]: row for row in analog_rows}
    motor_by_index = {row["index"]: row for row in motor_rows}
    gate_by_index = {row["index"]: row for row in gate_rows}
    monitor_by_silo = {row["silo_index"]: row for row in monitor_rows}

    alerts: list[str] = []
    silos_payload: list[dict[str, Any]] = []
    sensor_count = 0
    active_sensor_count = 0

    for silo_index, silo in enumerate(SILOS):
        monitor = monitor_by_silo.get(silo_index)

        sensors_payload = []
        for sensor in silo.sensors:
            sensor_count += 1
            row = analog_by_index.get(sensor.index)
            active = bool(row and row.get("active"))
            if active:
                active_sensor_count += 1

            temp_value = row.get("temperature") if row else None
            humid_value = row.get("humidity") if row else None
            sensors_payload.append(
                {
                    "index": sensor.index,
                    "label": sensor.label,
                    "temperature": temp_value,
                    "humidity": humid_value,
                    "active": active,
                }
            )

            if thresholds and active:
                temp_max = thresholds.get("temp_max")
                temp_min = thresholds.get("temp_min")
                humid_max = thresholds.get("humid_max")

                if sensor.show_temp and isinstance(temp_value, (int, float)):
                    if temp_value >= temp_max:
                        alerts.append(f"{silo.name} {sensor.label}: temp alta ({temp_value}C)")
                    elif temp_value <= temp_min:
                        alerts.append(f"{silo.name} {sensor.label}: temp baja ({temp_value}C)")
                    elif temp_value >= (temp_max - TEMP_WARN_MARGIN):
                        alerts.append(f"{silo.name} {sensor.label}: temp en advertencia ({temp_value}C)")

                if sensor.show_humidity and isinstance(humid_value, (int, float)):
                    if humid_value >= humid_max:
                        alerts.append(f"{silo.name} {sensor.label}: humedad alta ({humid_value}%)")
                    elif humid_value >= (humid_max - HUMID_WARN_MARGIN):
                        alerts.append(f"{silo.name} {sensor.label}: humedad en advertencia ({humid_value}%)")

        motors_payload = []
        for motor in silo.motors:
            row = motor_by_index.get(motor.index, {})
            motors_payload.append(
                {
                    "index": motor.index,
                    "label": motor.label,
                    "motor_type": motor.motor_type,
                    "is_running": bool(row.get("is_running", False)),
                    "auto_mode": bool(row.get("auto_mode", False)),
                    "enabled": bool(row.get("enabled", False)),
                    "fault": bool(row.get("fault", False)),
                }
            )

        gates_payload = []
        for gate in silo.gates:
            row = gate_by_index.get(gate.index, {})
            gates_payload.append(
                {
                    "index": gate.index,
                    "label": gate.label,
                    "gate_type": gate.gate_type,
                    "is_open": bool(row.get("is_open", False)),
                    "is_closed": bool(row.get("is_closed", False)),
                    "in_motion": bool(row.get("in_motion", False)),
                    "fault": bool(row.get("fault", False)),
                }
            )

        level_payload = {
            "high": monitor.get("level_high") if monitor else None,
            "low": monitor.get("level_low") if monitor else None,
            "source": "db_monitor" if monitor else "unknown",
        }

        gases_payload = []
        for gas in silo.gas_sensors:
            gas_payload = {
                "label": gas.label,
                "gas_type": gas.gas_type,
                "unit": gas.unit,
                "ppm": monitor.get("gas_ppm") if monitor else None,
                "active": bool(monitor.get("gas_active", False)) if monitor else False,
                "alarm_warn": bool(monitor.get("gas_warn", False)) if monitor else False,
                "alarm_trip": bool(monitor.get("gas_trip", False)) if monitor else False,
                "source": "db_monitor" if monitor else "unknown",
            }
            if gas_payload["alarm_trip"]:
                alerts.append(f"{silo.name} {gas.label}: alarma TRIP de gas")
            elif gas_payload["alarm_warn"]:
                alerts.append(f"{silo.name} {gas.label}: alarma WARN de gas")
            gases_payload.append(gas_payload)

        silos_payload.append(
            {
                "silo_index": silo_index,
                "silo_name": silo.name,
                "sensors": sensors_payload,
                "levels": level_payload,
                "gases": gases_payload,
                "motors": motors_payload,
                "gates": gates_payload,
            }
        )

    return {
        "type": "monitor_update",
        "timestamp": _iso_now(),
        "connected": connected,
        "silos": silos_payload,
        "thresholds": thresholds,
        "alerts": alerts,
        "summary": {
            "silo_count": len(SILOS),
            "sensor_count": sensor_count,
            "active_sensor_count": active_sensor_count,
            "alarm_count": len(alerts),
        },
    }
