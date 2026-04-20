import struct
import threading
from typing import Any

from app.config import GATE_COUNT, MOTOR_COUNT, PLC_IP, PLC_RACK, PLC_SLOT, SENSOR_COUNT
from app.db_layout import (
    AUTOCONF_BIT_ALARM_ACTIVE,
    AUTOCONF_BIT_AUTO_GLOBAL,
    AUTOCONF_FLAGS_BYTE_OFFSET,
    AUTOCONF_HUMID_MAX_OFFSET,
    AUTOCONF_TEMP_MAX_OFFSET,
    AUTOCONF_TEMP_MIN_OFFSET,
    DB_AUTOCONF,
    DB_GATES,
    DB_MONITOR_LEVEL_GAS,
    DB_MOTORS,
    DB_SENSORS,
    DB1_TOTAL_SIZE,
    DB2_TOTAL_SIZE,
    DB3_TOTAL_SIZE,
    DB13_TOTAL_SIZE,
    GATE_BIT_FAULT,
    GATE_BIT_IN_MOTION,
    GATE_BIT_IS_CLOSED,
    GATE_BIT_IS_OPEN,
    GATE_BLOCK_SIZE,
    MONITOR_GAS_ACTIVE_BIT,
    MONITOR_GAS_FLAGS_BYTE,
    MONITOR_GAS_PPM_OFFSET,
    MONITOR_GAS_TRIP_BIT,
    MONITOR_GAS_WARN_BIT,
    MONITOR_LEVEL_FLAGS_BYTE,
    MONITOR_LEVEL_HIGH_BIT,
    MONITOR_LEVEL_LOW_BIT,
    MONITOR_STRIDE,
    MOTOR_FLAGS_BYTE_OFFSET,
    MOTOR_BIT_AUTO_MODE,
    MOTOR_BIT_ENABLED,
    MOTOR_BIT_FAULT,
    MOTOR_BIT_IS_RUNNING,
    MOTOR_BLOCK_SIZE,
    SENSOR_ACTIVE_BIT,
    SENSOR_ACTIVE_BYTE_OFFSET,
    SENSOR_BLOCK_SIZE,
    SENSOR_HUMIDITY_OFFSET,
    SENSOR_TEMPERATURE_OFFSET,
)

try:
    import snap7  # type: ignore
except Exception:
    snap7 = None


def _get_bool(data: bytearray, byte_index: int, bit_index: int) -> bool:
    if byte_index >= len(data):
        return False
    return bool(data[byte_index] & (1 << bit_index))


class ReadOnlyPlcClient:
    """Read-only PLC client. No write methods are exposed."""

    def __init__(self, ip: str = PLC_IP, rack: int = PLC_RACK, slot: int = PLC_SLOT) -> None:
        self._ip = ip
        self._rack = rack
        self._slot = slot
        self._lock = threading.RLock()
        self._client = snap7.client.Client() if snap7 else None

    def connect(self) -> bool:
        if self._client is None:
            print("[PLC] python-snap7 not available. Running disconnected.")
            return False
        with self._lock:
            try:
                self._client.connect(self._ip, self._rack, self._slot)
                print(f"[PLC] Connected to {self._ip} (rack={self._rack}, slot={self._slot})")
                return True
            except Exception as exc:
                print(f"[PLC] Connection error: {exc}")
                return False

    def disconnect(self) -> None:
        if self._client is None:
            return
        with self._lock:
            try:
                self._client.disconnect()
            except Exception:
                pass

    def is_connected(self) -> bool:
        if self._client is None:
            return False
        with self._lock:
            try:
                return bool(self._client.get_connected())
            except Exception:
                return False

    def _db_read(self, db_number: int, start: int, size: int) -> bytearray | None:
        if self._client is None:
            return None
        with self._lock:
            try:
                return self._client.db_read(db_number, start, size)
            except Exception:
                return None

    def read_analog_sensors(self) -> list[dict[str, Any]]:
        if SENSOR_COUNT == 0 or DB1_TOTAL_SIZE == 0:
            return []
        raw = self._db_read(DB_SENSORS, 0, DB1_TOTAL_SIZE)
        if raw is None:
            return []

        rows: list[dict[str, Any]] = []
        for idx in range(SENSOR_COUNT):
            start = idx * SENSOR_BLOCK_SIZE
            block = raw[start : start + SENSOR_BLOCK_SIZE]
            if len(block) < SENSOR_BLOCK_SIZE:
                continue
            try:
                temperature = round(struct.unpack_from(">f", block, SENSOR_TEMPERATURE_OFFSET)[0], 2)
                humidity = round(struct.unpack_from(">f", block, SENSOR_HUMIDITY_OFFSET)[0], 2)
            except struct.error:
                temperature = 0.0
                humidity = 0.0
            active = _get_bool(block, SENSOR_ACTIVE_BYTE_OFFSET, SENSOR_ACTIVE_BIT)
            rows.append(
                {
                    "index": idx,
                    "temperature": temperature,
                    "humidity": humidity,
                    "active": active,
                }
            )
        return rows

    def read_motors(self) -> list[dict[str, Any]]:
        if MOTOR_COUNT == 0 or DB2_TOTAL_SIZE == 0:
            return []
        raw = self._db_read(DB_MOTORS, 0, DB2_TOTAL_SIZE)
        if raw is None:
            return []

        rows: list[dict[str, Any]] = []
        for idx in range(MOTOR_COUNT):
            start = idx * MOTOR_BLOCK_SIZE
            block = raw[start : start + MOTOR_BLOCK_SIZE]
            if len(block) < MOTOR_BLOCK_SIZE:
                continue
            rows.append(
                {
                    "index": idx,
                    "is_running": _get_bool(block, MOTOR_FLAGS_BYTE_OFFSET, MOTOR_BIT_IS_RUNNING),
                    "auto_mode": _get_bool(block, MOTOR_FLAGS_BYTE_OFFSET, MOTOR_BIT_AUTO_MODE),
                    "enabled": _get_bool(block, MOTOR_FLAGS_BYTE_OFFSET, MOTOR_BIT_ENABLED),
                    "fault": _get_bool(block, MOTOR_FLAGS_BYTE_OFFSET, MOTOR_BIT_FAULT),
                }
            )
        return rows

    def read_gates(self) -> list[dict[str, Any]]:
        if GATE_COUNT == 0 or DB13_TOTAL_SIZE == 0:
            return []
        raw = self._db_read(DB_GATES, 0, DB13_TOTAL_SIZE)
        if raw is None:
            return []

        rows: list[dict[str, Any]] = []
        for idx in range(GATE_COUNT):
            start = idx * GATE_BLOCK_SIZE
            block = raw[start : start + GATE_BLOCK_SIZE]
            if len(block) < GATE_BLOCK_SIZE:
                continue
            rows.append(
                {
                    "index": idx,
                    "is_open": _get_bool(block, 0, GATE_BIT_IS_OPEN),
                    "is_closed": _get_bool(block, 0, GATE_BIT_IS_CLOSED),
                    "in_motion": _get_bool(block, 0, GATE_BIT_IN_MOTION),
                    "fault": _get_bool(block, 0, GATE_BIT_FAULT),
                }
            )
        return rows

    def read_thresholds(self) -> dict[str, Any] | None:
        raw = self._db_read(DB_AUTOCONF, 0, DB3_TOTAL_SIZE)
        if raw is None or len(raw) < DB3_TOTAL_SIZE:
            return None
        try:
            temp_max = round(struct.unpack_from(">f", raw, AUTOCONF_TEMP_MAX_OFFSET)[0], 2)
            temp_min = round(struct.unpack_from(">f", raw, AUTOCONF_TEMP_MIN_OFFSET)[0], 2)
            humid_max = round(struct.unpack_from(">f", raw, AUTOCONF_HUMID_MAX_OFFSET)[0], 2)
        except struct.error:
            return None

        return {
            "temp_max": temp_max,
            "temp_min": temp_min,
            "humid_max": humid_max,
            "auto_global": _get_bool(raw, AUTOCONF_FLAGS_BYTE_OFFSET, AUTOCONF_BIT_AUTO_GLOBAL),
            "alarm_active": _get_bool(raw, AUTOCONF_FLAGS_BYTE_OFFSET, AUTOCONF_BIT_ALARM_ACTIVE),
        }

    def read_level_gas_monitor(self, silo_count: int) -> list[dict[str, Any]]:
        if silo_count <= 0:
            return []

        raw = self._db_read(DB_MONITOR_LEVEL_GAS, 0, silo_count * MONITOR_STRIDE)
        if raw is None:
            return []

        rows: list[dict[str, Any]] = []
        for silo_index in range(silo_count):
            start = silo_index * MONITOR_STRIDE
            block = raw[start : start + MONITOR_STRIDE]
            if len(block) < MONITOR_STRIDE:
                continue

            try:
                gas_ppm = round(struct.unpack_from(">f", block, MONITOR_GAS_PPM_OFFSET)[0], 2)
            except struct.error:
                gas_ppm = None

            rows.append(
                {
                    "silo_index": silo_index,
                    "level_high": _get_bool(block, MONITOR_LEVEL_FLAGS_BYTE, MONITOR_LEVEL_HIGH_BIT),
                    "level_low": _get_bool(block, MONITOR_LEVEL_FLAGS_BYTE, MONITOR_LEVEL_LOW_BIT),
                    "gas_ppm": gas_ppm,
                    "gas_active": _get_bool(block, MONITOR_GAS_FLAGS_BYTE, MONITOR_GAS_ACTIVE_BIT),
                    "gas_warn": _get_bool(block, MONITOR_GAS_FLAGS_BYTE, MONITOR_GAS_WARN_BIT),
                    "gas_trip": _get_bool(block, MONITOR_GAS_FLAGS_BYTE, MONITOR_GAS_TRIP_BIT),
                }
            )
        return rows
