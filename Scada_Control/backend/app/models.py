from typing import Literal

from pydantic import BaseModel, Field


class AnalogSensorReading(BaseModel):
    index: int
    label: str
    temperature: float | None = None
    humidity: float | None = None
    active: bool = False


class MotorState(BaseModel):
    index: int
    label: str
    motor_type: str
    is_running: bool = False
    auto_mode: bool = False
    enabled: bool = False
    fault: bool = False


class GateState(BaseModel):
    index: int
    label: str
    gate_type: str
    is_open: bool = False
    is_closed: bool = False
    in_motion: bool = False
    fault: bool = False


class LevelReading(BaseModel):
    high: bool | None = None
    low: bool | None = None
    source: str = "unknown"


class GasReading(BaseModel):
    label: str
    gas_type: str
    unit: str = "ppm"
    ppm: float | None = None
    active: bool = False
    alarm_warn: bool = False
    alarm_trip: bool = False
    source: str = "unknown"


class ThresholdReading(BaseModel):
    temp_max: float
    temp_min: float
    humid_max: float
    auto_global: bool
    alarm_active: bool


class SiloSnapshot(BaseModel):
    silo_index: int
    silo_name: str
    sensors: list[AnalogSensorReading]
    levels: LevelReading
    gases: list[GasReading]
    motors: list[MotorState]
    gates: list[GateState]


class SnapshotSummary(BaseModel):
    silo_count: int
    sensor_count: int
    active_sensor_count: int
    alarm_count: int


class ScadaSnapshot(BaseModel):
    type: Literal["monitor_update"] = "monitor_update"
    timestamp: str
    connected: bool
    silos: list[SiloSnapshot]
    thresholds: ThresholdReading | None = None
    alerts: list[str] = Field(default_factory=list)
    summary: SnapshotSummary
