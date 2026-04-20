from dataclasses import dataclass, field
import os


@dataclass
class SensorConfig:
    index: int
    label: str
    show_temp: bool = True
    show_humidity: bool = False


@dataclass
class LevelSensorConfig:
    label: str
    sensor_type: str = "hl"


@dataclass
class GasSensorConfig:
    label: str
    gas_type: str = "ch4"
    unit: str = "ppm"


@dataclass
class MotorConfig:
    index: int
    label: str
    motor_type: str = "contactor"


@dataclass
class GateConfig:
    index: int
    label: str
    gate_type: str = "descarga_central"


@dataclass
class SiloDefinition:
    name: str
    sensors: list[SensorConfig] = field(default_factory=list)
    motors: list[MotorConfig] = field(default_factory=list)
    level_sensors: list[LevelSensorConfig] = field(default_factory=list)
    gas_sensors: list[GasSensorConfig] = field(default_factory=list)
    gates: list[GateConfig] = field(default_factory=list)


SILOS: list[SiloDefinition] = [
    SiloDefinition(
        name="Silo 1",
        sensors=[
            SensorConfig(index=0, label="T-S1", show_temp=True, show_humidity=False),
            SensorConfig(index=1, label="H-S1", show_temp=False, show_humidity=True),
        ],
        motors=[
            MotorConfig(index=0, label="Silo Fan 1", motor_type="silo_fan"),
            MotorConfig(index=1, label="Silo Fan 2", motor_type="silo_fan"),
            MotorConfig(index=2, label="RFAN 01", motor_type="rfan"),
            MotorConfig(index=3, label="RFAN 02", motor_type="rfan"),
            MotorConfig(index=4, label="RFAN 03", motor_type="rfan"),
            MotorConfig(index=5, label="Barredora S1", motor_type="barredora"),
        ],
        level_sensors=[
            LevelSensorConfig(label="HL-S1", sensor_type="hl"),
            LevelSensorConfig(label="LL-S1", sensor_type="ll"),
        ],
        gas_sensors=[
            GasSensorConfig(label="Gas-S1", gas_type="ch4", unit="ppm"),
        ],
        gates=[
            GateConfig(index=0, label="Distrib. S1", gate_type="distribucion"),
            GateConfig(index=1, label="Descarga S1", gate_type="descarga_central"),
        ],
    ),
    SiloDefinition(
        name="Silo 2",
        sensors=[
            SensorConfig(index=2, label="T-S2", show_temp=True, show_humidity=False),
            SensorConfig(index=3, label="H-S2", show_temp=False, show_humidity=True),
        ],
        motors=[
            MotorConfig(index=6, label="Silo Fan 3", motor_type="silo_fan"),
            MotorConfig(index=7, label="Silo Fan 4", motor_type="silo_fan"),
            MotorConfig(index=8, label="RFAN 04", motor_type="rfan"),
            MotorConfig(index=9, label="RFAN 05", motor_type="rfan"),
            MotorConfig(index=10, label="RFAN 06", motor_type="rfan"),
            MotorConfig(index=11, label="Barredora S2", motor_type="barredora"),
        ],
        level_sensors=[
            LevelSensorConfig(label="HL-S2", sensor_type="hl"),
            LevelSensorConfig(label="LL-S2", sensor_type="ll"),
        ],
        gas_sensors=[
            GasSensorConfig(label="Gas-S2", gas_type="ch4", unit="ppm"),
        ],
        gates=[
            GateConfig(index=2, label="Distrib. S2", gate_type="distribucion"),
            GateConfig(index=3, label="Descarga Central S2", gate_type="descarga_central"),
            GateConfig(index=4, label="Descarga Lateral S2", gate_type="descarga_lateral"),
        ],
    ),
    SiloDefinition(
        name="Silo 3",
        sensors=[
            SensorConfig(index=4, label="T-S3", show_temp=True, show_humidity=False),
            SensorConfig(index=5, label="H-S3", show_temp=False, show_humidity=True),
        ],
        motors=[
            MotorConfig(index=12, label="Silo Fan 5", motor_type="silo_fan"),
            MotorConfig(index=13, label="Silo Fan 6", motor_type="silo_fan"),
            MotorConfig(index=14, label="RFAN 07", motor_type="rfan"),
            MotorConfig(index=15, label="RFAN 08", motor_type="rfan"),
            MotorConfig(index=16, label="RFAN 09", motor_type="rfan"),
            MotorConfig(index=17, label="Barredora S3", motor_type="barredora"),
        ],
        level_sensors=[
            LevelSensorConfig(label="HL-S3", sensor_type="hl"),
            LevelSensorConfig(label="LL-S3", sensor_type="ll"),
        ],
        gas_sensors=[
            GasSensorConfig(label="Gas-S3", gas_type="ch4", unit="ppm"),
        ],
        gates=[
            GateConfig(index=5, label="Distrib. S3", gate_type="distribucion"),
            GateConfig(index=6, label="Descarga Central S3", gate_type="descarga_central"),
            GateConfig(index=7, label="Descarga Lateral S3", gate_type="descarga_lateral"),
        ],
    ),
    SiloDefinition(
        name="Silo 4",
        sensors=[
            SensorConfig(index=6, label="T-S4", show_temp=True, show_humidity=False),
            SensorConfig(index=7, label="H-S4", show_temp=False, show_humidity=True),
        ],
        motors=[
            MotorConfig(index=18, label="Silo Fan 7", motor_type="silo_fan"),
            MotorConfig(index=19, label="Silo Fan 8", motor_type="silo_fan"),
            MotorConfig(index=20, label="RFAN 10", motor_type="rfan"),
            MotorConfig(index=21, label="RFAN 11", motor_type="rfan"),
            MotorConfig(index=22, label="RFAN 12", motor_type="rfan"),
            MotorConfig(index=23, label="Barredora S4", motor_type="barredora"),
        ],
        level_sensors=[
            LevelSensorConfig(label="HL-S4", sensor_type="hl"),
            LevelSensorConfig(label="LL-S4", sensor_type="ll"),
        ],
        gas_sensors=[
            GasSensorConfig(label="Gas-S4", gas_type="ch4", unit="ppm"),
        ],
        gates=[
            GateConfig(index=8, label="Distrib. S4", gate_type="distribucion"),
            GateConfig(index=9, label="Descarga Central S4", gate_type="descarga_central"),
            GateConfig(index=10, label="Descarga Lateral S4", gate_type="descarga_lateral"),
        ],
    ),
]


def _max_index(values: list[int]) -> int:
    return max(values) + 1 if values else 0


SENSOR_COUNT = _max_index([s.index for silo in SILOS for s in silo.sensors])
MOTOR_COUNT = _max_index([m.index for silo in SILOS for m in silo.motors])
GATE_COUNT = _max_index([g.index for silo in SILOS for g in silo.gates])
PLC_GATE_BLOCK_SIZE = int(os.getenv("SCADA_GATE_BLOCK_SIZE", "2"))
PLC_DB_GATES = int(os.getenv("SCADA_DB_GATES", "13"))
PLC_MOTOR_BLOCK_SIZE = int(os.getenv("SCADA_MOTOR_BLOCK_SIZE", "2"))
PLC_MOTOR_FLAGS_BYTE_OFFSET = int(os.getenv("SCADA_MOTOR_FLAGS_BYTE_OFFSET", "0"))

PLC_IP = os.getenv("SCADA_PLC_IP", "192.168.0.1")
PLC_RACK = int(os.getenv("SCADA_PLC_RACK", "0"))
PLC_SLOT = int(os.getenv("SCADA_PLC_SLOT", "1"))

REFRESH_SECONDS = float(os.getenv("SCADA_REFRESH_SECONDS", "1.0"))

DB_MONITOR = int(os.getenv("SCADA_DB_MONITOR", "100"))
MONITOR_STRIDE = int(os.getenv("SCADA_MONITOR_STRIDE", "16"))

TEMP_WARN_MARGIN = float(os.getenv("SCADA_TEMP_WARN_MARGIN", "5.0"))
HUMID_WARN_MARGIN = float(os.getenv("SCADA_HUMID_WARN_MARGIN", "10.0"))

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("SCADA_CORS_ORIGINS", "http://localhost:8100,http://127.0.0.1:8100").split(",")
    if origin.strip()
]
