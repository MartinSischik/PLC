# core/tms6000_provider.py
# Lectura de sensores logicos desde TMS6000/NL6000 por Modbus TCP.

from dataclasses import dataclass
from typing import Optional

from pymodbus.client import ModbusTcpClient

from config import (
    TMS_IP,
    TMS_PORT,
    TMS_UNIT,
    TMS_TIMEOUT_SECONDS,
    TMS_REG_TEMP_T0,
    TMS_REG_TEMP_T1,
    TMS_REG_HUM_T2,
    TMS_REGISTER_SCALE,
    TMS_NO_SENSOR_VALUE,
)


@dataclass
class TmsLogicalReadings:
    """Modelo logico del proyecto: T0/T1 temperatura, T2 humedad."""

    t0_temp: Optional[float]
    t1_temp: Optional[float]
    t2_hum: Optional[float]

    @property
    def ok(self) -> bool:
        return (
            self.t0_temp is not None
            and self.t1_temp is not None
            and self.t2_hum is not None
        )


class Tms6000Provider:
    """Cliente de lectura Modbus para TMS6000 (NL6000)."""

    def __init__(
        self,
        ip: str = TMS_IP,
        port: int = TMS_PORT,
        unit: int = TMS_UNIT,
        timeout: float = TMS_TIMEOUT_SECONDS,
    ) -> None:
        self._ip = ip
        self._port = port
        self._unit = unit
        self._timeout = timeout
        self._client = ModbusTcpClient(host=self._ip, port=self._port, timeout=self._timeout)

    def connect(self) -> bool:
        try:
            ok = self._client.connect()
            if ok:
                print(f"[TMS] Conectado a {self._ip}:{self._port}")
            else:
                print(f"[TMS] No se pudo conectar a {self._ip}:{self._port}")
            return ok
        except Exception as e:
            print(f"[TMS] Error conectando: {e}")
            return False

    def disconnect(self) -> None:
        try:
            self._client.close()
        except Exception:
            pass

    def is_connected(self) -> bool:
        try:
            return self._client.is_socket_open()
        except Exception:
            return False

    def read_logical_sensors(self) -> TmsLogicalReadings:
        """Lee T0/T1/T2 usando direcciones configuradas."""
        try:
            t0 = self._read_scaled_register(TMS_REG_TEMP_T0)
            t1 = self._read_scaled_register(TMS_REG_TEMP_T1)
            h2 = self._read_scaled_register(TMS_REG_HUM_T2)
            return TmsLogicalReadings(t0_temp=t0, t1_temp=t1, t2_hum=h2)
        except Exception as e:
            print(f"[TMS] Error leyendo sensores: {e}")
            return TmsLogicalReadings(t0_temp=None, t1_temp=None, t2_hum=None)

    def _read_scaled_register(self, address: int) -> Optional[float]:
        rr = self._client.read_holding_registers(address=address, count=1, device_id=self._unit)
        if rr.isError():
            return None
        raw = rr.registers[0]
        if raw == TMS_NO_SENSOR_VALUE:
            return None
        # INT16 con signo, factor configurable.
        signed = raw if raw < 0x8000 else raw - 0x10000
        return round(signed * TMS_REGISTER_SCALE, 2)
