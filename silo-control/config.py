# config.py
# Configuracion global del monitor de silo para S7-1515-2 PN (TIA/PLCSIM).
#
# SISTEMA MODULAR: para cambiar la topologia (silos, sensores, motores, compuertas)
# solo editar la lista SILOS mas abajo.  Todo lo demas se deriva automaticamente.

from dataclasses import dataclass, field


# ── Definicion de sensores ────────────────────────────────────────────────────

@dataclass
class SensorConfig:
    """Sensor analogico (temperatura / humedad) en DB1."""
    index: int
    label: str
    show_temp: bool = True
    show_humidity: bool = False


@dataclass
class LevelSensorConfig:
    """Sensor de nivel digital (HL = alto, LL = bajo)."""
    label: str
    sensor_type: str = "hl"  # "hl" | "ll"


# ── Definicion de motores ─────────────────────────────────────────────────────

@dataclass
class MotorConfig:
    """Motor controlado por PLC via DQ arranque + DI confirmacion/falla.
    motor_type: "silo_fan" | "rfan" | "barredora" | "soft_starter" | "vfd" | "contactor"
    """
    index: int
    label: str = ""
    motor_type: str = "contactor"


# ── Definicion de compuertas ──────────────────────────────────────────────────

@dataclass
class GateConfig:
    """Compuerta electrica motorizada.
    Control: DQ abrir + DQ cerrar → DI fin de carrera.
    gate_type: "distribucion" | "descarga_central" | "descarga_lateral"
    """
    index: int
    label: str = ""
    gate_type: str = "descarga_central"


# ── Definicion de silos ──────────────────────────────────────────────────────

@dataclass
class SiloDefinition:
    """Definicion completa de un silo."""
    name: str
    sensors: list = field(default_factory=list)        # list[SensorConfig]
    motors: list = field(default_factory=list)          # list[MotorConfig]
    level_sensors: list = field(default_factory=list)   # list[LevelSensorConfig]
    gates: list = field(default_factory=list)            # list[GateConfig]


# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURACION DE SILOS — EDITAR AQUI PARA CAMBIAR LA TOPOLOGIA
# ══════════════════════════════════════════════════════════════════════════════
#
# Motores por silo (segun planos Proyecto IGL 25052025.pdf):
#   - 2 Silo Fans    (18.5 kW, contactor KM, págs. 137-144)
#   - 3 RFANs        (1.5 kW,  arranque directo, págs. 29-40)
#   - 1 Barredora     (18.5 kW, contactor, S260R)
#   Total: 6 motores/silo × 4 silos = 24 motores
#
# Compuertas por silo:
#   - Distribución (DQ abrir/cerrar, DI fin carrera, págs. 227-234)
#   - Descarga central (págs. 239-252)
#   - Descarga lateral (S2, S3, S4 solamente)
#
# Indices de motor (DB2): 0..23
#   S1: 0-5,  S2: 6-11,  S3: 12-17,  S4: 18-23
#
# Indices de compuerta (DB4): 0..N
#   S1: 0-1,  S2: 2-4,  S3: 5-7,  S4: 8-10,  + CR01(11)

SILOS: list = [
    # ── SILO 1 ────────────────────────────────────────────────────────────
    SiloDefinition(
        name="Silo 1",
        sensors=[
            SensorConfig(index=0, label="T-S1", show_temp=True,  show_humidity=False),
            SensorConfig(index=1, label="H-S1", show_temp=False, show_humidity=True),
        ],
        motors=[
            # Silo Fans (18.5 kW, contactor) — págs. 137-138
            MotorConfig(index=0,  label="Silo Fan 1",  motor_type="silo_fan"),
            MotorConfig(index=1,  label="Silo Fan 2",  motor_type="silo_fan"),
            # RFANs extractores (1.5 kW, arranque directo) — págs. 29-34
            MotorConfig(index=2,  label="RFAN 01",     motor_type="rfan"),
            MotorConfig(index=3,  label="RFAN 02",     motor_type="rfan"),
            MotorConfig(index=4,  label="RFAN 03",     motor_type="rfan"),
            # Barredora (18.5 kW) — S260R-S1
            MotorConfig(index=5,  label="Barredora S1", motor_type="barredora"),
        ],
        level_sensors=[
            LevelSensorConfig(label="HL-S1", sensor_type="hl"),
            LevelSensorConfig(label="LL-S1", sensor_type="ll"),
        ],
        gates=[
            GateConfig(index=0, label="Distrib. S1",    gate_type="distribucion"),
            GateConfig(index=1, label="Descarga S1",    gate_type="descarga_central"),
        ],
    ),
    # ── SILO 2 ────────────────────────────────────────────────────────────
    SiloDefinition(
        name="Silo 2",
        sensors=[
            SensorConfig(index=2, label="T-S2", show_temp=True,  show_humidity=False),
            SensorConfig(index=3, label="H-S2", show_temp=False, show_humidity=True),
        ],
        motors=[
            MotorConfig(index=6,  label="Silo Fan 3",  motor_type="silo_fan"),
            MotorConfig(index=7,  label="Silo Fan 4",  motor_type="silo_fan"),
            MotorConfig(index=8,  label="RFAN 04",     motor_type="rfan"),
            MotorConfig(index=9,  label="RFAN 05",     motor_type="rfan"),
            MotorConfig(index=10, label="RFAN 06",     motor_type="rfan"),
            MotorConfig(index=11, label="Barredora S2", motor_type="barredora"),
        ],
        level_sensors=[
            LevelSensorConfig(label="HL-S2", sensor_type="hl"),
            LevelSensorConfig(label="LL-S2", sensor_type="ll"),
        ],
        gates=[
            GateConfig(index=2, label="Distrib. S2",         gate_type="distribucion"),
            GateConfig(index=3, label="Descarga Central S2", gate_type="descarga_central"),
            GateConfig(index=4, label="Descarga Lateral S2", gate_type="descarga_lateral"),
        ],
    ),
    # ── SILO 3 ────────────────────────────────────────────────────────────
    SiloDefinition(
        name="Silo 3",
        sensors=[
            SensorConfig(index=4, label="T-S3", show_temp=True,  show_humidity=False),
            SensorConfig(index=5, label="H-S3", show_temp=False, show_humidity=True),
        ],
        motors=[
            MotorConfig(index=12, label="Silo Fan 5",  motor_type="silo_fan"),
            MotorConfig(index=13, label="Silo Fan 6",  motor_type="silo_fan"),
            MotorConfig(index=14, label="RFAN 07",     motor_type="rfan"),
            MotorConfig(index=15, label="RFAN 08",     motor_type="rfan"),
            MotorConfig(index=16, label="RFAN 09",     motor_type="rfan"),
            MotorConfig(index=17, label="Barredora S3", motor_type="barredora"),
        ],
        level_sensors=[
            LevelSensorConfig(label="HL-S3", sensor_type="hl"),
            LevelSensorConfig(label="LL-S3", sensor_type="ll"),
        ],
        gates=[
            GateConfig(index=5, label="Distrib. S3",         gate_type="distribucion"),
            GateConfig(index=6, label="Descarga Central S3", gate_type="descarga_central"),
            GateConfig(index=7, label="Descarga Lateral S3", gate_type="descarga_lateral"),
        ],
    ),
    # ── SILO 4 ────────────────────────────────────────────────────────────
    SiloDefinition(
        name="Silo 4",
        sensors=[
            SensorConfig(index=6, label="T-S4", show_temp=True,  show_humidity=False),
            SensorConfig(index=7, label="H-S4", show_temp=False, show_humidity=True),
        ],
        motors=[
            MotorConfig(index=18, label="Silo Fan 7",  motor_type="silo_fan"),
            MotorConfig(index=19, label="Silo Fan 8",  motor_type="silo_fan"),
            MotorConfig(index=20, label="RFAN 10",     motor_type="rfan"),
            MotorConfig(index=21, label="RFAN 11",     motor_type="rfan"),
            MotorConfig(index=22, label="RFAN 12",     motor_type="rfan"),
            MotorConfig(index=23, label="Barredora S4", motor_type="barredora"),
        ],
        level_sensors=[
            LevelSensorConfig(label="HL-S4", sensor_type="hl"),
            LevelSensorConfig(label="LL-S4", sensor_type="ll"),
        ],
        gates=[
            GateConfig(index=8,  label="Distrib. S4",         gate_type="distribucion"),
            GateConfig(index=9,  label="Descarga Central S4", gate_type="descarga_central"),
            GateConfig(index=10, label="Descarga Lateral S4", gate_type="descarga_lateral"),
        ],
    ),
]


# ══════════════════════════════════════════════════════════════════════════════
# CONTEOS DERIVADOS — NO EDITAR (se calculan solos desde SILOS)
# ══════════════════════════════════════════════════════════════════════════════

def _derive_counts() -> tuple:
    """Calcula sensor_count, motor_count y gate_count a partir de SILOS."""
    all_sensor_indices = [s.index for silo in SILOS for s in silo.sensors]
    all_motor_indices  = [m.index for silo in SILOS for m in silo.motors]
    all_gate_indices   = [g.index for silo in SILOS for g in silo.gates]
    sc = (max(all_sensor_indices) + 1) if all_sensor_indices else 0
    mc = (max(all_motor_indices)  + 1) if all_motor_indices  else 0
    gc = (max(all_gate_indices)   + 1) if all_gate_indices   else 0
    return sc, mc, gc

SENSOR_COUNT, MOTOR_COUNT, GATE_COUNT = _derive_counts()


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
    0:  (0,  "temp"),   # T-S1  — Silo 1 temperatura
    1:  (1,  "hum"),    # H-S1  — Silo 1 humedad
    2:  (2,  "temp"),   # T-S2  — Silo 2 temperatura
    3:  (3,  "hum"),    # H-S2  — Silo 2 humedad
    4:  (4,  "temp"),   # T-S3  — Silo 3 temperatura
    5:  (5,  "hum"),    # H-S3  — Silo 3 humedad
    6:  (6,  "temp"),   # T-S4  — Silo 4 temperatura
    7:  (7,  "hum"),    # H-S4  — Silo 4 humedad
}

# Escala y valor invalido de registros Modbus
TMS_REGISTER_SCALE = 0.1
TMS_NO_SENSOR_VALUE = 0x7FFF

# Comportamiento al perder lectura del TMS:
# True  -> desactiva sensores en PLC
# False -> conserva ultimo valor en DB1
TMS_MARK_INACTIVE_ON_FAILURE = True
