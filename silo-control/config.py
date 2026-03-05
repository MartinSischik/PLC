# config.py
# Configuracion global del monitor de silo para S7-1515-2 PN (TIA/PLCSIM).

# ── Conexion al PLC S7-1515-2 PN (Snap7 / PLCSIM) ────────────────────────────
PLC_IP   = "192.168.0.1"      # IP de la CPU real o instancia PLCSIM
PLC_RACK = 0                   # S7-1500 usa rack 0
PLC_SLOT = 1                   # CPU en slot 1

# ── Topologia del silo ─────────────────────────────────────────────────────────
SENSOR_COUNT = 8         # Sensores en DB1
FAN_COUNT    = 4         # Motores/ventiladores en DB2

# ── Simulador de sensores ──────────────────────────────────────────────────────
SIMULATION_INTERVAL = 2.0
