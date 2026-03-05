# core/plc_interface.py
# Interfaz de comunicación con el PLC Siemens S7-1515-2 PN usando la
# librería Snap7 (protocolo S7 sobre TCP/IP, puerto 102).
#
# Encapsula todas las operaciones de lectura/escritura en los tres Data
# Blocks del PLC.  El resto de la aplicación nunca accede a Snap7
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
from config import PLC_IP, PLC_RACK, PLC_SLOT


# ══════════════════════════════════════════════════════════════════════════════
# Dataclasses para representar lecturas
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class SensorReading:
    """Lectura completa de un sensor de temperatura/humedad.

    Attributes:
        index:       Número de sensor en el array DB1 (0-7).
        temperature: Temperatura en °C.
        humidity:    Humedad relativa en %RH.
        active:      True si el sensor está operativo.
    """
    index:       int
    temperature: float
    humidity:    float
    active:      bool


@dataclass
class MotorStatus:
    """Estado completo de un motor.

    Attributes:
        index:      Número de motor en el array DB2 (0-3).
        cmd_run:    Comando de arranque manual enviado por Python.
        is_running: Estado real del motor, reportado por el PLC.
        auto_mode:  True si el motor obedece la automatización del PLC.
        enabled:    True si el motor está habilitado para operar.
        fault:      True si el PLC detectó una falla en el motor.
    """
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

    Gestiona la conexión Snap7 y provee métodos tipados para leer/escribir
    los tres Data Blocks.  Todos los errores se capturan internamente;
    los métodos nunca lanzan excepciones al caller: devuelven None o False.

    Thread-safety: se usa un threading.RLock() para serializar todos los
    accesos a self._client.  Se usa RLock (reentrante) en lugar de Lock
    porque _reconnect() llama a connect(), y ambos necesitan adquirir el
    mismo lock desde el mismo hilo sin causar deadlock.

    Uso básico::

        plc = SiloPLC()
        if plc.connect():
            sensor = plc.read_sensor(0)
            print(sensor.temperature)
        plc.disconnect()
    """

    def __init__(
        self,
        ip:   str = PLC_IP,
        rack: int = PLC_RACK,
        slot: int = PLC_SLOT,
    ) -> None:
        """Inicializa la interfaz (no conecta todavía).

        Args:
            ip:   Dirección IP del PLC o PLCSim Advanced.
            rack: Rack del PLC (0 para S7-1500).
            slot: Slot de la CPU (1 para S7-1500).
        """
        self._ip   = ip
        self._rack = rack
        self._slot = slot
        self._client = snap7.client.Client()
        # RLock permite que el mismo hilo adquiera el lock múltiples veces
        # (necesario porque _reconnect → connect, ambos dentro de with self._lock).
        self._lock = threading.RLock()

    # ── Gestión de conexión ────────────────────────────────────────────────

    def connect(self) -> bool:
        """Conecta al PLC usando los parámetros de configuración.

        Returns:
            True si la conexión fue exitosa, False en caso contrario.
        """
        with self._lock:
            try:
                self._client.connect(self._ip, self._rack, self._slot)
                print(f"[PLC] Conectado a {self._ip} (rack={self._rack}, slot={self._slot})")
                return True
            except Exception as e:
                print(f"[PLC] Error de conexión: {e}")
                return False

    def disconnect(self) -> None:
        """Desconecta del PLC de forma ordenada."""
        with self._lock:
            try:
                self._client.disconnect()
                print("[PLC] Desconectado.")
            except Exception as e:
                print(f"[PLC] Error al desconectar: {e}")

    def is_connected(self) -> bool:
        """Retorna True si el cliente Snap7 reporta conexión activa."""
        with self._lock:
            try:
                return self._client.get_connected()
            except Exception:
                return False

    # ── Reconexión interna ────────────────────────────────────────────────

    def _reconnect(self) -> bool:
        """Intenta reconectar una sola vez.  Uso interno.

        Siempre se llama desde dentro de un bloque with self._lock ya
        adquirido; el RLock permite re-adquirirlo sin deadlock.
        """
        with self._lock:
            print("[PLC] Intentando reconexión...")
            try:
                self._client.disconnect()
            except Exception:
                pass
            return self.connect()

    # ══════════════════════════════════════════════════════════════════════
    # DB1 – SensorData: lectura de sensores
    # ══════════════════════════════════════════════════════════════════════

    def read_sensor(self, index: int) -> Optional[SensorReading]:
        """Lee los datos de un sensor individual desde DB1.

        Realiza un db_read de exactamente 10 bytes a partir del offset
        del sensor indicado.

        Args:
            index: Índice del sensor (0-7).

        Returns:
            SensorReading con los datos del sensor, o None si hubo error.
        """
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
                        print(f"[PLC] Error tras reconexión (sensor {index}): {e2}")
                return None

    def read_all_sensors(self) -> list[SensorReading]:
        """Lee los 8 sensores de DB1 en una sola operación de red.

        Returns:
            Lista de hasta 8 SensorReading.  Si hay error retorna lista vacía.
        """
        with self._lock:
            try:
                data    = self._client.db_read(DB_SENSORS, 0, DB1_TOTAL_SIZE)
                sensors = []
                for i in range(8):
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
                        for i in range(8):
                            offset = i * SENSOR_BLOCK_SIZE
                            chunk  = data[offset: offset + SENSOR_BLOCK_SIZE]
                            sensors.append(self._parse_sensor(i, chunk))
                        return sensors
                    except Exception as e2:
                        print(f"[PLC] Error tras reconexión (all sensors): {e2}")
                return []

    def _parse_sensor(self, index: int, data: bytearray) -> SensorReading:
        """Convierte 10 bytes raw en un SensorReading.  Uso interno."""
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
    # DB1 – SensorData: escritura (para el simulador)
    # ══════════════════════════════════════════════════════════════════════

    def write_sensor(
        self,
        index:       int,
        temperature: float,
        humidity:    float,
        active:      bool,
    ) -> bool:
        """Escribe los datos de un sensor en DB1 (usado por el simulador).

        Construye los 10 bytes del struct y los envía al PLC.

        Args:
            index:       Índice del sensor (0-7).
            temperature: Temperatura en °C.
            humidity:    Humedad relativa en %RH.
            active:      True si el sensor está operativo.

        Returns:
            True si la escritura fue exitosa, False en caso contrario.
        """
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
                        print(f"[PLC] Error tras reconexión (write sensor {index}): {e2}")
                return False

    # ══════════════════════════════════════════════════════════════════════
    # DB2 – MotorControl: lectura de motores
    # ══════════════════════════════════════════════════════════════════════

    def read_motor(self, index: int) -> Optional[MotorStatus]:
        """Lee el estado completo de un motor desde DB2.

        Args:
            index: Índice del motor (0-3).

        Returns:
            MotorStatus con todos los bits del motor, o None si hubo error.
        """
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
                        print(f"[PLC] Error tras reconexión (motor {index}): {e2}")
                return None

    def read_all_motors(self) -> list[MotorStatus]:
        """Lee los 4 motores de DB2 en una sola operación de red.

        Returns:
            Lista de hasta 4 MotorStatus.  Si hay error retorna lista vacía.
        """
        with self._lock:
            try:
                data   = self._client.db_read(DB_MOTORS, 0, DB2_TOTAL_SIZE)
                motors = []
                for i in range(4):
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
                        for i in range(4):
                            offset = i * MOTOR_BLOCK_SIZE
                            chunk = data[offset: offset + MOTOR_BLOCK_SIZE]
                            motors.append(self._parse_motor(i, chunk))
                        return motors
                    except Exception as e2:
                        print(f"[PLC] Error tras reconexión (all motors): {e2}")
                return []

    def _parse_motor(self, index: int, data: bytearray) -> MotorStatus:
        """Convierte 1 byte raw en un MotorStatus.  Uso interno."""
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
    # IMPORTANTE: se hace read-modify-write para no tocar bits ajenos.
    # El PLC gestiona is_running y fault; Python gestiona cmd_run,
    # auto_mode y enabled.

    def _write_motor_bit(self, index: int, bit: int, value: bool) -> bool:
        """Lee el byte del motor, modifica un bit y lo escribe de vuelta.

        El lock cubre la operación completa read-modify-write para que
        ningún otro hilo pueda intercalarse entre el db_read y el db_write.

        Args:
            index: Índice del motor (0-3).
            bit:   Número de bit a modificar (0-4).
            value: Nuevo valor del bit.

        Returns:
            True si la operación fue exitosa, False en caso contrario.
        """
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
                        print(f"[PLC] Error tras reconexión (motor bit {index}/{bit}): {e2}")
                return False

    def set_motor_command(self, index: int, run: bool) -> bool:
        """Envía el comando de arranque/parada manual al motor.

        Solo tiene efecto si el motor tiene auto_mode=False.

        Args:
            index: Índice del motor (0-3).
            run:   True para arrancar, False para parar.

        Returns:
            True si la escritura fue exitosa.
        """
        with self._lock:
            return self._write_motor_bit(index, MOTOR_BIT_CMD_RUN, run)

    def set_motor_auto_mode(self, index: int, auto: bool) -> bool:
        """Activa o desactiva el modo automático del motor.

        En modo automático el PLC decide si el motor corre según los umbrales.
        En modo manual, Python controla el motor con set_motor_command.

        Args:
            index: Índice del motor (0-3).
            auto:  True para modo automático, False para modo manual.

        Returns:
            True si la escritura fue exitosa.
        """
        with self._lock:
            return self._write_motor_bit(index, MOTOR_BIT_AUTO_MODE, auto)

    def set_motor_enabled(self, index: int, enabled: bool) -> bool:
        """Habilita o deshabilita un motor (override de máxima prioridad).

        Un motor con enabled=False siempre estará apagado,
        independientemente del modo automático o del comando manual.

        Args:
            index:   Índice del motor (0-3).
            enabled: True para habilitar, False para deshabilitar.

        Returns:
            True si la escritura fue exitosa.
        """
        with self._lock:
            return self._write_motor_bit(index, MOTOR_BIT_ENABLED, enabled)

    # ══════════════════════════════════════════════════════════════════════
    # DB3 – AutomationConfig
    # ══════════════════════════════════════════════════════════════════════

    def set_thresholds(self, temp_max: float, humid_max: float) -> bool:
        """Actualiza los umbrales de temperatura máxima y humedad máxima en DB3.

        Lee primero el bloque completo para conservar temp_min y los BOOLs,
        modifica solo los campos necesarios y escribe todo de vuelta.

        Args:
            temp_max:  Nuevo umbral máximo de temperatura en °C.
            humid_max: Nuevo umbral máximo de humedad en %RH.

        Returns:
            True si la escritura fue exitosa.
        """
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
                        print(f"[PLC] Error tras reconexión (set_thresholds): {e2}")
                return False

    def set_temperature_thresholds(self, temp_max: float, temp_min: float) -> bool:
        """Actualiza temp_max y temp_min en DB3 sin tocar humid_max ni flags."""
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
                        print(f"[PLC] Error tras reconexión (set_temperature_thresholds): {e2}")
                return False

    def read_thresholds(self) -> Optional[dict]:
        """Lee todos los valores de configuración desde DB3.

        Returns:
            Diccionario con las claves:
                temp_max     (float)
                temp_min     (float)
                humid_max    (float)
                auto_global  (bool)
                alarm_active (bool)
            o None si hubo error.
        """
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
                        print(f"[PLC] Error tras reconexión (read_thresholds): {e2}")
                return None

    def _parse_autoconf(self, data: bytearray) -> dict:
        """Convierte los 14 bytes de DB3 en un diccionario.  Uso interno."""
        return {
            "temp_max":     round(struct.unpack_from('>f', data, AUTOCONF_TEMP_MAX_OFFSET)[0], 2),
            "temp_min":     round(struct.unpack_from('>f', data, AUTOCONF_TEMP_MIN_OFFSET)[0], 2),
            "humid_max":    round(struct.unpack_from('>f', data, AUTOCONF_HUMID_MAX_OFFSET)[0], 2),
            "auto_global":  snap7.util.get_bool(data, AUTOCONF_FLAGS_BYTE_OFFSET, AUTOCONF_BIT_AUTO_GLOBAL),
            "alarm_active": snap7.util.get_bool(data, AUTOCONF_FLAGS_BYTE_OFFSET, AUTOCONF_BIT_ALARM_ACTIVE),
        }
