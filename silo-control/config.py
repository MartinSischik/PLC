# config.py
# Configuracion global del monitor de silo para S7-1515-2 PN (TIA/PLCSIM).
#
# SISTEMA MODULAR: para cambiar la topologia (silos, sensores, motores)
# solo editar la lista SILOS mas abajo.  Todo lo demas se deriva automaticamente.

from dataclasses import dataclass, field


# ── Definicion de sensores ────────────────────────────────────────────────────

@dataclass
class SensorConfig:
    """Configuracion de un sensor dentro de un silo.

    Attributes:
        index:         Indice global del sensor en DB1 (0..N).
        label:         Etiqueta visible en la GUI (ej. "T0", "H1").
        show_temp:     True si este sensor mide temperatura.
        show_humidity: True si este sensor mide humedad.
    """
    index: int
    label: str
    show_temp: bool = True
    show_humidity: bool = False


# ── Definicion de motores ─────────────────────────────────────────────────────

@dataclass
class MotorConfig:
    """Configuracion de un motor dentro de un silo.

    Attributes:
        index:      Indice global del motor en DB2 (0..N).
        label:      Etiqueta visible en la GUI (ej. "Ventilador 1").
        motor_type: Tipo de arranque: "soft_starter" | "vfd".
    """
    index: int
    label: str = ""
    motor_type: str = "soft_starter"   # "soft_starter" | "vfd"


# ── Definicion de silos ──────────────────────────────────────────────────────

@dataclass
class SiloDefinition:
    """Definicion de un silo: sus sensores y sus motores.

    Attributes:
        name:    Nombre del silo mostrado en la GUI.
        sensors: Lista de SensorConfig asignados a este silo.
        motors:  Lista de MotorConfig asignados a este silo.
    """
    name: str
    sensors: list = field(default_factory=list)   # list[SensorConfig]
    motors: list = field(default_factory=list)     # list[MotorConfig]


# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURACION DE SILOS — EDITAR AQUI PARA CAMBIAR LA TOPOLOGIA
# ══════════════════════════════════════════════════════════════════════════════
# Agregar/quitar silos, sensores o motores: solo modificar esta lista.
# El resto del sistema se adapta automaticamente.

SILOS: list = [
    SiloDefinition(
        name="Silo 1",
        sensors=[
            SensorConfig(index=0, label="T0", show_temp=True,  show_humidity=False),
            SensorConfig(index=1, label="H1", show_temp=False, show_humidity=True),
        ],
        motors=[MotorConfig(index=0, label="Motor 1 (32A)", motor_type="soft_starter")],
    ),
    SiloDefinition(
        name="Silo 2",
        sensors=[
            SensorConfig(index=2, label="T2", show_temp=True,  show_humidity=False),
            SensorConfig(index=3, label="H3", show_temp=False, show_humidity=True),
        ],
        motors=[MotorConfig(index=1, label="Motor 2 (38A)", motor_type="soft_starter")],
    ),
    SiloDefinition(
        name="Silo 3",
        sensors=[
            SensorConfig(index=4, label="T4", show_temp=True,  show_humidity=False),
            SensorConfig(index=5, label="H5", show_temp=False, show_humidity=True),
        ],
        motors=[MotorConfig(index=2, label="Motor 3 (47A)", motor_type="soft_starter")],
    ),
    SiloDefinition(
        name="Silo 4",
        sensors=[
            SensorConfig(index=6, label="T6", show_temp=True,  show_humidity=False),
            SensorConfig(index=7, label="H7", show_temp=False, show_humidity=True),
        ],
        motors=[MotorConfig(index=3, label="Motor 4 (47A)", motor_type="soft_starter")],
    ),
    SiloDefinition(
        name="Silo 5",
        sensors=[
            SensorConfig(index=8,  label="T8",  show_temp=True,  show_humidity=False),
            SensorConfig(index=9,  label="H9",  show_temp=False, show_humidity=True),
        ],
        motors=[MotorConfig(index=4, label="Motor 5 (47A)", motor_type="soft_starter")],
    ),
    SiloDefinition(
        name="Silo 6",
        sensors=[
            SensorConfig(index=10, label="T10", show_temp=True,  show_humidity=False),
            SensorConfig(index=11, label="H11", show_temp=False, show_humidity=True),
        ],
        motors=[MotorConfig(index=5, label="Motor 6 (77A)", motor_type="soft_starter")],
    ),
    SiloDefinition(
        name="Silo 7",
        sensors=[
            SensorConfig(index=12, label="T12", show_temp=True,  show_humidity=False),
            SensorConfig(index=13, label="H13", show_temp=False, show_humidity=True),
        ],
        motors=[MotorConfig(index=6, label="Motor 7 (93A)", motor_type="soft_starter")],
    ),
    SiloDefinition(
        name="Silo 8",
        sensors=[
            SensorConfig(index=14, label="T14", show_temp=True,  show_humidity=False),
            SensorConfig(index=15, label="H15", show_temp=False, show_humidity=True),
        ],
        motors=[MotorConfig(index=7, label="Motor 8 VFD (90kW)", motor_type="vfd")],
    ),
]


# ══════════════════════════════════════════════════════════════════════════════
# CONTEOS DERIVADOS — NO EDITAR (se calculan solos desde SILOS)
# ══════════════════════════════════════════════════════════════════════════════

def _derive_counts() -> tuple:
    """Calcula sensor_count y motor_count a partir de SILOS."""
    all_sensor_indices = [s.index for silo in SILOS for s in silo.sensors]
    all_motor_indices  = [m.index for silo in SILOS for m in silo.motors]
    sc = (max(all_sensor_indices) + 1) if all_sensor_indices else 0
    mc = (max(all_motor_indices)  + 1) if all_motor_indices  else 0
    return sc, mc

SENSOR_COUNT, MOTOR_COUNT = _derive_counts()


# ── Conexion al PLC S7-1515-2 PN (Snap7 / PLCSIM) ──────────────────────────
PLC_IP   = "192.168.0.1"      # IP de la CPU real o instancia PLCSIM
PLC_RACK = 0                   # S7-1500 usa rack 0
PLC_SLOT = 1                   # CPU en slot 1

# ── Fuente de sensores ───────────────────────────────────────────────────────
# - "tms": puente TMS6000 -> PLC
# - "sim": simulador de sensores
# - "none": no hay escritor externo (DB1 quedara con lo que escriba el PLC)
SENSOR_SOURCE = "sim"

# ── Simulador de sensores ────────────────────────────────────────────────────
SIMULATION_INTERVAL = 2.0

# ── Puente TMS6000 -> PLC ───────────────────────────────────────────────────
ENABLE_TMS_BRIDGE = True

# Conexion Modbus TCP al NL6000/TMS6000
TMS_IP   = "192.168.0.50"
TMS_PORT = 502
TMS_UNIT = 1

# Ciclo del bridge (segundos)
TMS_BRIDGE_INTERVAL = 2.0
TMS_TIMEOUT_SECONDS = 2.0

# Mapeo config-driven: DB1 index -> (registro Modbus, tipo)
# Editar este dict para mapear sensores TMS a slots de DB1.
TMS_SENSOR_MAP: dict = {
    # db1_index: (modbus_register, "temp"|"hum")
    0:  (0,  "temp"),   # T0  — Silo 1 temperatura
    1:  (1,  "hum"),    # H1  — Silo 1 humedad
    2:  (2,  "temp"),   # T2  — Silo 2 temperatura
    3:  (3,  "hum"),    # H3  — Silo 2 humedad
    4:  (4,  "temp"),   # T4  — Silo 3 temperatura
    5:  (5,  "hum"),    # H5  — Silo 3 humedad
    6:  (6,  "temp"),   # T6  — Silo 4 temperatura
    7:  (7,  "hum"),    # H7  — Silo 4 humedad
    8:  (8,  "temp"),   # T8  — Silo 5 temperatura
    9:  (9,  "hum"),    # H9  — Silo 5 humedad
    10: (10, "temp"),   # T10 — Silo 6 temperatura
    11: (11, "hum"),    # H11 — Silo 6 humedad
    12: (12, "temp"),   # T12 — Silo 7 temperatura
    13: (13, "hum"),    # H13 — Silo 7 humedad
    14: (14, "temp"),   # T14 — Silo 8 temperatura
    15: (15, "hum"),    # H15 — Silo 8 humedad
}

# Escala y valor invalido de registros Modbus
TMS_REGISTER_SCALE = 0.1
TMS_NO_SENSOR_VALUE = 0x7FFF

# Comportamiento al perder lectura del TMS:
# True  -> desactiva sensores en PLC
# False -> conserva ultimo valor en DB1
TMS_MARK_INACTIVE_ON_FAILURE = True
