# config.py
# Configuracion global del monitor de silo para S7-1515-2 PN (TIA/PLCSIM).

# ── Conexion al PLC S7-1515-2 PN (Snap7 / PLCSIM) ────────────────────────────
PLC_IP   = "192.168.0.1"      # IP de la CPU real o instancia PLCSIM
PLC_RACK = 0                   # S7-1500 usa rack 0
PLC_SLOT = 1                   # CPU en slot 1

# ── Topologia del silo ─────────────────────────────────────────────────────────
SENSOR_COUNT = 8         # Sensores en DB1
FAN_COUNT    = 4         # Motores/ventiladores en DB2

# Fuente externa de sensores que alimenta DB1:
# - "tms": puente TMS6000 -> PLC
# - "sim": script simulate_temperatures.py
# - "none": no hay escritor externo (DB1 quedara con lo que escriba el PLC)
SENSOR_SOURCE = "sim"
# tms o sim para usar el simulador

# ── Simulador de sensores ──────────────────────────────────────────────────────
SIMULATION_INTERVAL = 2.0

# ── Puente TMS6000 -> PLC (Opcion 1) ─────────────────────────────────────────
# Activa lectura de sensores desde TMS6000 y escritura en DB1 por Snap7.
ENABLE_TMS_BRIDGE = True

# Conexion Modbus TCP al NL6000/TMS6000
TMS_IP   = "192.168.0.50"
TMS_PORT = 502
TMS_UNIT = 1

# Ciclo del bridge (segundos)
TMS_BRIDGE_INTERVAL = 2.0
TMS_TIMEOUT_SECONDS = 2.0

# Mapeo logico actual del proyecto:
# - T0 y T1 = temperatura
# - T2       = humedad
# Direcciones Modbus de ejemplo (ajustar segun manual real).
TMS_REG_TEMP_T0 = 0
TMS_REG_TEMP_T1 = 1
TMS_REG_HUM_T2  = 2

# Escala y valor invalido de registros
TMS_REGISTER_SCALE = 0.1
TMS_NO_SENSOR_VALUE = 0x7FFF

# Comportamiento al perder lectura del TMS:
# True  -> desactiva sensores en PLC
# False -> conserva ultimo valor en DB1
TMS_MARK_INACTIVE_ON_FAILURE = True
