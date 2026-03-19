# core/tms6000_provider.py
# Lectura de sensores desde TMS6000/NL6000 por Modbus TCP.
#
# Interfaz generica config-driven: lee N sensores segun TMS_SENSOR_MAP.

from typing import Optional

from pymodbus.client import ModbusTcpClient

from config import (
    TMS_IP,
    TMS_PORT,
    TMS_UNIT,
    TMS_TIMEOUT_SECONDS,
    TMS_REGISTER_SCALE,
    TMS_NO_SENSOR_VALUE,
    TMS_SENSOR_MAP,
)


class Tms6000Provider:
    """Cliente de lectura Modbus para TMS6000 (NL6000).

    Metodo principal: read_sensors() retorna un dict generico
    {db1_index: (kind, value)} para cada entrada en TMS_SENSOR_MAP.
    """

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

    def read_sensors(
        self,
        sensor_map: dict | None = None,
    ) -> dict:
        """Lee sensores segun el mapa proporcionado.

        Args:
            sensor_map: Diccionario {db1_index: (modbus_register, kind)}.
                        Si es None usa TMS_SENSOR_MAP de config.

        Returns:
            dict {db1_index: (kind, value_or_None)} para cada entrada del mapa.
        """
        if sensor_map is None:
            sensor_map = TMS_SENSOR_MAP

        result: dict = {}
        for db_idx, (reg, kind) in sensor_map.items():
            try:
                val = self._read_scaled_register(reg)
            except Exception as e:
                print(f"[TMS] Error leyendo registro {reg} (sensor {db_idx}): {e}")
                val = None
            result[db_idx] = (kind, val)
        return result

    def _read_scaled_register(self, address: int) -> Optional[float]:
        rr = self._client.read_holding_registers(address=address, count=1, device_id=self._unit)
        if rr.isError():
            return None
        raw = rr.registers[0]
        if raw == TMS_NO_SENSOR_VALUE:
            return None
        signed = raw if raw < 0x8000 else raw - 0x10000
        return round(signed * TMS_REGISTER_SCALE, 2)
