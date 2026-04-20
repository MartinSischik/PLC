# Scada_Control

Nuevo SCADA de solo visualizacion, separado del sistema legado y autocontenido en esta carpeta.

Todo lo necesario para este modulo vive dentro de esta carpeta.

## Objetivo

- Mantener el sistema viejo intacto para respaldo.
- Construir un servicio nuevo read-only (sin comandos al PLC).
- Construir una web nueva enfocada unicamente en monitoreo.
- Reutilizar topologia y contrato de datos ya modelado en TIA/PLC.

## Estructura

- `backend/`: FastAPI + WebSocket read-only.
- `web/`: interfaz web nueva (HTML/CSS/JS) sin controles de actuacion.
- `Dockerfile` + `docker-compose.yml`: despliegue contenedorizado.
- `run_docker_*.ps1`: atajos de operacion docker desde esta carpeta.

## Contrato PLC reutilizado

Se reutiliza el layout existente como base:

- DB1: sensores analogicos (temperatura, humedad, activo).
- DB2: estados de motores (solo lectura).
- DB3: umbrales de proceso (solo lectura).
- DB13: estados de compuertas (solo lectura).

Y se deja preparado un bloque opcional para evolucion de sensores de nivel y gas desde TIA.

## Como ejecutar (desarrollo)

1. Activar entorno Python.
2. Instalar dependencias:
   - `pip install -r backend/requirements.txt`
3. Ejecutar API:
   - `uvicorn app.main:app --reload --host 0.0.0.0 --port 8100 --app-dir backend`
4. Abrir navegador en:
   - `http://localhost:8100`

## Docker (desde esta misma carpeta)

1. Copiar variables de entorno:
   - `Copy-Item .env.example .env`
2. Ajustar valores PLC en `.env` si aplica.
   - Seleccionar DB de puertas con `SCADA_DB_GATES` (ejemplo: 13 o 30).
   - Si DB13 es `ARRAY[..] OF BYTE`, usar `SCADA_GATE_BLOCK_SIZE=1`.
   - Si DB13 es `ARRAY[..] OF STRUCT` de 2 bytes, usar `SCADA_GATE_BLOCK_SIZE=2`.
   - Para UDT de motor compacto, usar `SCADA_MOTOR_BLOCK_SIZE=2` y `SCADA_MOTOR_FLAGS_BYTE_OFFSET=0`.
   - Para UDT de motor con `motor_type(INT)` + bools + reals, usar `SCADA_MOTOR_BLOCK_SIZE=12` y `SCADA_MOTOR_FLAGS_BYTE_OFFSET=2`.
3. Levantar servicio:
   - `docker compose --env-file .env up -d --build`
4. Ver logs:
   - `docker compose logs -f scada_control`
5. Bajar servicio:
   - `docker compose down`

Atajos PowerShell incluidos:

- `./run_docker_up.ps1`
- `./run_docker_logs.ps1`
- `./run_docker_down.ps1`

## Endpoints clave

- `GET /api/health`
- `GET /api/config`
- `GET /api/snapshot`
- `WS  /ws/monitor`

No existen endpoints `POST`, `PATCH`, `PUT` ni `DELETE` para control de actuadores.
