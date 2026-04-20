# Notas TIA para Scada_Control

Este modulo nuevo asume un esquema de solo lectura.

## Base activa reutilizada

- DB1: sensores analogicos
- DB2: estado motores
- DB3: umbrales
- DB13: estado compuertas

## Extension recomendada para TIA (nivel + gas)

Crear DB de monitoreo dedicado (ejemplo DB100) para sensores de nivel y gas.

Propuesta minima por silo:

- Byte 0, bit 0: nivel_alto_activo
- Byte 0, bit 1: nivel_bajo_activo
- Byte 4..7: gas_ppm (REAL)
- Byte 8, bit 0: gas_sensor_activo
- Byte 8, bit 1: gas_alarm_warn
- Byte 8, bit 2: gas_alarm_trip

Tamano sugerido por silo: 16 bytes.

Con 4 silos: 64 bytes.

El backend nuevo ya soporta este layout de forma opcional.
