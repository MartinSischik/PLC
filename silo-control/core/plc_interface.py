# core/plc_interface.py
# Interfaz de comunicacion con el PLC Siemens S7-1515-2 PN usando la
# libreria Snap7 (protocolo S7 sobre TCP/IP, puerto 102).
#
# Encapsula todas las operaciones de lectura/escritura en los tres Data
# Blocks del PLC.  El resto de la aplicacion nunca accede a Snap7
# directamente; solo usa esta clase.

import struct
import threading
import snap7
import snap7.util
from dataclasses import dataclass
from typing import Optional

from core.db_offsets import (
    DB_SENSORS, DB_MOTORS, DB_AUTOCONF,
    SENSOR_BLOCK_SIZE, DB1_TOTAL_SIZE,
    MOTOR_BLOCK_SIZE, DB2_TOTAL_SIZE, DB3_TOTAL_SIZE,
    SENSOR_TEMPERATURE_OFFSET, SENSOR_HUMIDITY_OFFSET,
    SENSOR_ACTIVE_BYTE_OFFSET, SENSOR_ACTIVE_BIT,
    MOTOR_BIT_CMD_RUN, MOTOR_BIT_IS_RUNNING,
    MOTOR_BIT_AUTO_MODE, MOTOR_BIT_ENABLED, MOTOR_BIT_FAULT,
    AUTOCONF_TEMP_MAX_OFFSET, AUTOCONF_TEMP_MIN_OFFSET,
    AUTOCONF_HUMID_MAX_OFFSET, AUTOCONF_FLAGS_BYTE_OFFSET,
    AUTOCONF_BIT_AUTO_GLOBAL, AUTOCONF_BIT_ALARM_ACTIVE,
    sensor_offset, motor_offset,
)
from config import PLC_IP, PLC_RACK, PLC_SLOT, SENSOR_COUNT, MOTOR_COUNT


# ══════════════════════════════════════════════════════════════════════════════
# Dataclasses para representar lecturas
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class SensorReading:
    """Lectura completa de un sensor de temperatura/humedad."""
    index:       int
    temperature: float
    humidity:    float
    active:      bool


@dataclass
class MotorStatus:
    """Estado completo de un motor."""
    index:      int
    cmd_run:    bool
    is_running: bool
    auto_mode:  bool
    enabled:    bool
    fault:      bool


# ══════════════════════════════════════════════════════════════════════════════
# Clase principal
# ══════════════════════════════════════════════════════════════════════════════

class SiloPLC:
    """Interfaz de alto nivel con el PLC del silo industrial.

    Gestiona la conexion Snap7 y provee metodos tipados para leer/escribir
    los tres Data Blocks.  Todos los errores se capturan internamente;
    los metodos nunca lanzan excepciones al caller: devuelven None o False.

    Thread-safety: se usa un threading.RLock() para serializar todos los
    accesos a self._client.
    """

    def __init__(
        self,
        ip:   str = PLC_IP,
        rack: int = PLC_RACK,
        slot: int = PLC_SLOT,
    ) -> None:
        self._ip   = ip
        self._rack = rack
        self._slot = slot
        self._client = snap7.client.Client()
        self._lock = threading.RLock()

    # ── Gestion de conexion ──────────────────────────────────────────────

    def connect(self) -> bool:
        with self._lock:
            try:
                self._client.connect(self._ip, self._rack, self._slot)
                print(f"[PLC] Conectado a {self._ip} (rack={self._rack}, slot={self._slot})")
                return True
            except Exception as e:
                print(f"[PLC] Error de conexion: {e}")
                return False

    def disconnect(self) -> None:
        with self._lock:
            try:
                self._client.disconnect()
                print("[PLC] Desconectado.")
            except Exception as e:
                print(f"[PLC] Error al desconectar: {e}")

    def is_connected(self) -> bool:
        with self._lock:
            try:
                return self._client.get_connected()
            except Exception:
                return False

    def _reconnect(self) -> bool:
        with self._lock:
            print("[PLC] Intentando reconexion...")
            try:
                self._client.disconnect()
            except Exception:
                pass
            return self.connect()

    # ══════════════════════════════════════════════════════════════════════
    # DB1 – SensorData: lectura
    # ══════════════════════════════════════════════════════════════════════

    def read_sensor(self, index: int) -> Optional[SensorReading]:
        with self._lock:
            try:
                start = sensor_offset(index)
                data  = self._client.db_read(DB_SENSORS, start, SENSOR_BLOCK_SIZE)
                return self._parse_sensor(index, data)
            except Exception as e:
                print(f"[PLC] Error leyendo sensor {index}: {e}")
                if self._reconnect():
                    try:
                        start = sensor_offset(index)
                        data  = self._client.db_read(DB_SENSORS, start, SENSOR_BLOCK_SIZE)
                        return self._parse_sensor(index, data)
                    except Exception as e2:
                        print(f"[PLC] Error tras reconexion (sensor {index}): {e2}")
                return None

    def read_all_sensors(self) -> list[SensorReading]:
        """Lee todos los sensores de DB1 en una sola operacion de red."""
        if SENSOR_COUNT == 0 or DB1_TOTAL_SIZE == 0:
            return []
        with self._lock:
            try:
                data    = self._client.db_read(DB_SENSORS, 0, DB1_TOTAL_SIZE)
                sensors = []
                for i in range(SENSOR_COUNT):
                    offset = i * SENSOR_BLOCK_SIZE
                    chunk  = data[offset: offset + SENSOR_BLOCK_SIZE]
                    sensors.append(self._parse_sensor(i, chunk))
                return sensors
            except Exception as e:
                print(f"[PLC] Error leyendo todos los sensores: {e}")
                if self._reconnect():
                    try:
                        data    = self._client.db_read(DB_SENSORS, 0, DB1_TOTAL_SIZE)
                        sensors = []
                        for i in range(SENSOR_COUNT):
                            offset = i * SENSOR_BLOCK_SIZE
                            chunk  = data[offset: offset + SENSOR_BLOCK_SIZE]
                            sensors.append(self._parse_sensor(i, chunk))
                        return sensors
                    except Exception as e2:
                        print(f"[PLC] Error tras reconexion (all sensors): {e2}")
                return []

    def _parse_sensor(self, index: int, data: bytearray) -> SensorReading:
        temperature = struct.unpack_from('>f', data, SENSOR_TEMPERATURE_OFFSET)[0]
        humidity    = struct.unpack_from('>f', data, SENSOR_HUMIDITY_OFFSET)[0]
        active      = snap7.util.get_bool(data, SENSOR_ACTIVE_BYTE_OFFSET, SENSOR_ACTIVE_BIT)
        return SensorReading(
            index=index,
            temperature=round(temperature, 2),
            humidity=round(humidity, 2),
            active=active,
        )

    # ══════════════════════════════════════════════════════════════════════
    # DB1 – SensorData: escritura (para simulador / bridge)
    # ══════════════════════════════════════════════════════════════════════

    def write_sensor(
        self,
        index:       int,
        temperature: float,
        humidity:    float,
        active:      bool,
    ) -> bool:
        with self._lock:
            try:
                data = bytearray(SENSOR_BLOCK_SIZE)
                struct.pack_into('>f', data, SENSOR_TEMPERATURE_OFFSET, temperature)
                struct.pack_into('>f', data, SENSOR_HUMIDITY_OFFSET,    humidity)
                snap7.util.set_bool(data, SENSOR_ACTIVE_BYTE_OFFSET, SENSOR_ACTIVE_BIT, active)
                start = sensor_offset(index)
                self._client.db_write(DB_SENSORS, start, data)
                return True
            except Exception as e:
                print(f"[PLC] Error escribiendo sensor {index}: {e}")
                if self._reconnect():
                    try:
                        data = bytearray(SENSOR_BLOCK_SIZE)
                        struct.pack_into('>f', data, SENSOR_TEMPERATURE_OFFSET, temperature)
                        struct.pack_into('>f', data, SENSOR_HUMIDITY_OFFSET,    humidity)
                        snap7.util.set_bool(data, SENSOR_ACTIVE_BYTE_OFFSET, SENSOR_ACTIVE_BIT, active)
                        start = sensor_offset(index)
                        self._client.db_write(DB_SENSORS, start, data)
                        return True
                    except Exception as e2:
                        print(f"[PLC] Error tras reconexion (write sensor {index}): {e2}")
                return False

    # ══════════════════════════════════════════════════════════════════════
    # DB2 – MotorControl: lectura
    # ══════════════════════════════════════════════════════════════════════

    def read_motor(self, index: int) -> Optional[MotorStatus]:
        with self._lock:
            try:
                start = motor_offset(index)
                data  = self._client.db_read(DB_MOTORS, start, MOTOR_BLOCK_SIZE)
                return self._parse_motor(index, data)
            except Exception as e:
                print(f"[PLC] Error leyendo motor {index}: {e}")
                if self._reconnect():
                    try:
                        start = motor_offset(index)
                        data  = self._client.db_read(DB_MOTORS, start, MOTOR_BLOCK_SIZE)
                        return self._parse_motor(index, data)
                    except Exception as e2:
                        print(f"[PLC] Error tras reconexion (motor {index}): {e2}")
                return None

    def read_all_motors(self) -> list[MotorStatus]:
        """Lee todos los motores de DB2 en una sola operacion de red."""
        if MOTOR_COUNT == 0 or DB2_TOTAL_SIZE == 0:
            return []
        with self._lock:
            try:
                data   = self._client.db_read(DB_MOTORS, 0, DB2_TOTAL_SIZE)
                motors = []
                for i in range(MOTOR_COUNT):
                    offset = i * MOTOR_BLOCK_SIZE
                    chunk = data[offset: offset + MOTOR_BLOCK_SIZE]
                    motors.append(self._parse_motor(i, chunk))
                return motors
            except Exception as e:
                print(f"[PLC] Error leyendo todos los motores: {e}")
                if self._reconnect():
                    try:
                        data   = self._client.db_read(DB_MOTORS, 0, DB2_TOTAL_SIZE)
                        motors = []
                        for i in range(MOTOR_COUNT):
                            offset = i * MOTOR_BLOCK_SIZE
                            chunk = data[offset: offset + MOTOR_BLOCK_SIZE]
                            motors.append(self._parse_motor(i, chunk))
                        return motors
                    except Exception as e2:
                        print(f"[PLC] Error tras reconexion (all motors): {e2}")
                return []

    def _parse_motor(self, index: int, data: bytearray) -> MotorStatus:
        return MotorStatus(
            index=index,
            cmd_run    = snap7.util.get_bool(data, 0, MOTOR_BIT_CMD_RUN),
            is_running = snap7.util.get_bool(data, 0, MOTOR_BIT_IS_RUNNING),
            auto_mode  = snap7.util.get_bool(data, 0, MOTOR_BIT_AUTO_MODE),
            enabled    = snap7.util.get_bool(data, 0, MOTOR_BIT_ENABLED),
            fault      = snap7.util.get_bool(data, 0, MOTOR_BIT_FAULT),
        )

    # ══════════════════════════════════════════════════════════════════════
    # DB2 – MotorControl: escritura de bits individuales
    # ══════════════════════════════════════════════════════════════════════

    def _write_motor_bit(self, index: int, bit: int, value: bool) -> bool:
        with self._lock:
            try:
                start = motor_offset(index)
                data  = self._client.db_read(DB_MOTORS, start, MOTOR_BLOCK_SIZE)
                snap7.util.set_bool(data, 0, bit, value)
                self._client.db_write(DB_MOTORS, start, data)
                return True
            except Exception as e:
                print(f"[PLC] Error escribiendo bit {bit} del motor {index}: {e}")
                if self._reconnect():
                    try:
                        start = motor_offset(index)
                        data  = self._client.db_read(DB_MOTORS, start, MOTOR_BLOCK_SIZE)
                        snap7.util.set_bool(data, 0, bit, value)
                        self._client.db_write(DB_MOTORS, start, data)
                        return True
                    except Exception as e2:
                        print(f"[PLC] Error tras reconexion (motor bit {index}/{bit}): {e2}")
                return False

    def set_motor_command(self, index: int, run: bool) -> bool:
        with self._lock:
            return self._write_motor_bit(index, MOTOR_BIT_CMD_RUN, run)

    def set_motor_auto_mode(self, index: int, auto: bool) -> bool:
        with self._lock:
            return self._write_motor_bit(index, MOTOR_BIT_AUTO_MODE, auto)

    def set_motor_enabled(self, index: int, enabled: bool) -> bool:
        with self._lock:
            return self._write_motor_bit(index, MOTOR_BIT_ENABLED, enabled)

    # ══════════════════════════════════════════════════════════════════════
    # DB3 – AutomationConfig
    # ══════════════════════════════════════════════════════════════════════

    def set_thresholds(self, temp_max: float, humid_max: float) -> bool:
        with self._lock:
            try:
                data = self._client.db_read(DB_AUTOCONF, 0, DB3_TOTAL_SIZE)
                struct.pack_into('>f', data, AUTOCONF_TEMP_MAX_OFFSET,  temp_max)
                struct.pack_into('>f', data, AUTOCONF_HUMID_MAX_OFFSET, humid_max)
                self._client.db_write(DB_AUTOCONF, 0, data)
                return True
            except Exception as e:
                print(f"[PLC] Error escribiendo umbrales: {e}")
                if self._reconnect():
                    try:
                        data = self._client.db_read(DB_AUTOCONF, 0, DB3_TOTAL_SIZE)
                        struct.pack_into('>f', data, AUTOCONF_TEMP_MAX_OFFSET,  temp_max)
                        struct.pack_into('>f', data, AUTOCONF_HUMID_MAX_OFFSET, humid_max)
                        self._client.db_write(DB_AUTOCONF, 0, data)
                        return True
                    except Exception as e2:
                        print(f"[PLC] Error tras reconexion (set_thresholds): {e2}")
                return False

    def set_temperature_thresholds(self, temp_max: float, temp_min: float) -> bool:
        with self._lock:
            try:
                data = self._client.db_read(DB_AUTOCONF, 0, DB3_TOTAL_SIZE)
                struct.pack_into('>f', data, AUTOCONF_TEMP_MAX_OFFSET, temp_max)
                struct.pack_into('>f', data, AUTOCONF_TEMP_MIN_OFFSET, temp_min)
                self._client.db_write(DB_AUTOCONF, 0, data)
                return True
            except Exception as e:
                print(f"[PLC] Error escribiendo temp_max/temp_min: {e}")
                if self._reconnect():
                    try:
                        data = self._client.db_read(DB_AUTOCONF, 0, DB3_TOTAL_SIZE)
                        struct.pack_into('>f', data, AUTOCONF_TEMP_MAX_OFFSET, temp_max)
                        struct.pack_into('>f', data, AUTOCONF_TEMP_MIN_OFFSET, temp_min)
                        self._client.db_write(DB_AUTOCONF, 0, data)
                        return True
                    except Exception as e2:
                        print(f"[PLC] Error tras reconexion (set_temperature_thresholds): {e2}")
                return False

    def read_thresholds(self) -> Optional[dict]:
        with self._lock:
            try:
                data = self._client.db_read(DB_AUTOCONF, 0, DB3_TOTAL_SIZE)
                return self._parse_autoconf(data)
            except Exception as e:
                print(f"[PLC] Error leyendo umbrales: {e}")
                if self._reconnect():
                    try:
                        data = self._client.db_read(DB_AUTOCONF, 0, DB3_TOTAL_SIZE)
                        return self._parse_autoconf(data)
                    except Exception as e2:
                        print(f"[PLC] Error tras reconexion (read_thresholds): {e2}")
                return None

    def _parse_autoconf(self, data: bytearray) -> dict:
        return {
            "temp_max":     round(struct.unpack_from('>f', data, AUTOCONF_TEMP_MAX_OFFSET)[0], 2),
            "temp_min":     round(struct.unpack_from('>f', data, AUTOCONF_TEMP_MIN_OFFSET)[0], 2),
            "humid_max":    round(struct.unpack_from('>f', data, AUTOCONF_HUMID_MAX_OFFSET)[0], 2),
            "auto_global":  snap7.util.get_bool(data, AUTOCONF_FLAGS_BYTE_OFFSET, AUTOCONF_BIT_AUTO_GLOBAL),
            "alarm_active": snap7.util.get_bool(data, AUTOCONF_FLAGS_BYTE_OFFSET, AUTOCONF_BIT_ALARM_ACTIVE),
        }
