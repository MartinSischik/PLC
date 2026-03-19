# core/db_offsets.py
# Constantes y funciones helper que describen la estructura de memoria de los
# tres Data Blocks del PLC.  Este archivo es la fuente de verdad para cualquier
# calculo de offset; si el PLC cambia su layout, solo hay que editar aqui.
#
# Los tamanos de DB1 y DB2 se calculan dinamicamente a partir de config.py.

from config import SENSOR_COUNT, MOTOR_COUNT

# ══════════════════════════════════════════════════════════════════════════════
# Numeros de Data Block
# ══════════════════════════════════════════════════════════════════════════════
DB_SENSORS  = 1   # DB1 – SensorData
DB_MOTORS   = 2   # DB2 – MotorControl
DB_AUTOCONF = 3   # DB3 – AutomationConfig

# ══════════════════════════════════════════════════════════════════════════════
# DB1 – SensorData
# ══════════════════════════════════════════════════════════════════════════════
# Cada sensor es un struct de 10 bytes:
#   +0  temperature  REAL  4 bytes
#   +4  humidity     REAL  4 bytes
#   +8  active       BOOL  1 byte (bit 0 del byte)
#   +9  (padding de 1 byte hasta completar 10)

SENSOR_BLOCK_SIZE = 10   # bytes por sensor
DB1_TOTAL_SIZE    = SENSOR_COUNT * SENSOR_BLOCK_SIZE

# Offsets internos dentro de cada struct de sensor
SENSOR_TEMPERATURE_OFFSET = 0   # REAL, 4 bytes
SENSOR_HUMIDITY_OFFSET    = 4   # REAL, 4 bytes
SENSOR_ACTIVE_BYTE_OFFSET = 8   # BOOL en bit 0 de este byte
SENSOR_ACTIVE_BIT         = 0   # bit 0


def sensor_offset(index: int) -> int:
    """Retorna el byte de inicio del sensor[index] dentro de DB1.

    Args:
        index: Indice del sensor (0..SENSOR_COUNT-1).

    Returns:
        Offset en bytes desde el inicio de DB1.

    Raises:
        ValueError: Si index esta fuera del rango valido.
    """
    if not (0 <= index < SENSOR_COUNT):
        raise ValueError(
            f"Indice de sensor invalido: {index}. "
            f"Debe estar entre 0 y {SENSOR_COUNT - 1} (SENSOR_COUNT={SENSOR_COUNT})."
        )
    return index * SENSOR_BLOCK_SIZE


# ══════════════════════════════════════════════════════════════════════════════
# DB2 – MotorControl
# ══════════════════════════════════════════════════════════════════════════════
# Cada motor ocupa exactamente 2 bytes (5 bits usados + padding):
#   bit 0  cmd_run    BOOL  Comando arranque manual (escribe Python)
#   bit 1  is_running BOOL  Estado real del motor   (escribe PLC)
#   bit 2  auto_mode  BOOL  Modo automatico activo  (escribe Python)
#   bit 3  enabled    BOOL  Motor habilitado        (escribe Python)
#   bit 4  fault      BOOL  Falla del motor         (escribe PLC)

MOTOR_BLOCK_SIZE = 2   # 2 bytes por motor (5 bits + padding)
DB2_TOTAL_SIZE   = MOTOR_COUNT * MOTOR_BLOCK_SIZE

# Numeros de bit dentro del byte del motor
MOTOR_BIT_CMD_RUN    = 0
MOTOR_BIT_IS_RUNNING = 1
MOTOR_BIT_AUTO_MODE  = 2
MOTOR_BIT_ENABLED    = 3
MOTOR_BIT_FAULT      = 4


def motor_offset(index: int) -> int:
    """Retorna el byte de inicio del motor[index] dentro de DB2.

    Args:
        index: Indice del motor (0..MOTOR_COUNT-1).

    Returns:
        Offset en bytes desde el inicio de DB2.

    Raises:
        ValueError: Si index esta fuera del rango valido.
    """
    if not (0 <= index < MOTOR_COUNT):
        raise ValueError(
            f"Indice de motor invalido: {index}. "
            f"Debe estar entre 0 y {MOTOR_COUNT - 1} (MOTOR_COUNT={MOTOR_COUNT})."
        )
    return index * MOTOR_BLOCK_SIZE


# ══════════════════════════════════════════════════════════════════════════════
# DB3 – AutomationConfig
# ══════════════════════════════════════════════════════════════════════════════
# Variables sueltas (no es array):
#   Offset  0  temp_max     REAL   4 bytes  Umbral max. temperatura (default 35.0 C)
#   Offset  4  temp_min     REAL   4 bytes  Umbral min. temperatura (default 10.0 C)
#   Offset  8  humid_max    REAL   4 bytes  Umbral max. humedad     (default 70.0 %RH)
#   Offset 12  auto_global  BOOL   bit 0    Modo automatico global  (default FALSE)
#   Offset 12  alarm_active BOOL   bit 1    Alarma activa           (default FALSE)

DB3_TOTAL_SIZE = 14   # bytes totales del bloque

AUTOCONF_TEMP_MAX_OFFSET     = 0    # REAL, 4 bytes
AUTOCONF_TEMP_MIN_OFFSET     = 4    # REAL, 4 bytes
AUTOCONF_HUMID_MAX_OFFSET    = 8    # REAL, 4 bytes
AUTOCONF_FLAGS_BYTE_OFFSET   = 12   # byte que contiene los dos BOOLs
AUTOCONF_BIT_AUTO_GLOBAL     = 0    # bit 0 del byte 12
AUTOCONF_BIT_ALARM_ACTIVE    = 1    # bit 1 del byte 12
