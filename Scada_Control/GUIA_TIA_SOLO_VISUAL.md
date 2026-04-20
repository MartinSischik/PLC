# Guia TIA Portal - Solo Visual (muy detallada)

## 0) Objetivo

Configurar desde cero un PLC en modo solo visualizacion para Scada_Control:

1. Leer sensores de temperatura y humedad.
2. Leer estados de motores.
3. Leer estados de compuertas.
4. Leer nivel y gas.
5. No enviar comandos desde SCADA a actuadores.

## 1) Arquitectura final recomendada

Usaremos estos DB:

1. DB1 -> SensorData (temperatura/humedad)
2. DB2 -> MotorControl (estados de motor)
3. DB30 -> GateControl (estados de puertas, 1 BYTE por puerta)
4. DB100 -> MonitorData (nivel + gas)

Notas:

1. Si usas otro numero para puertas, esta bien. Solo ajusta .env de Scada_Control.
2. Todos estos DB deben estar con optimized block access desactivado.

## 2) Paso previo obligatorio

1. Haz backup del proyecto TIA.
2. Compila el proyecto actual para confirmar que parte de una base sana.
3. Elimina o desactiva la logica de automatizacion (FB2/DB4) si aun existe.

## 3) Crear tipos de datos PLC (PLC data types)

Ruta en TIA:

1. Program blocks
2. PLC data types
3. Add new data type

En TIA los UDT se editan como tabla (grilla):

1. Columna Name: nombre del campo.
2. Columna Data type: tipo (Bool, Int, Real, Byte, etc.).
3. Columna Default value: valor inicial.

Debes cargar una fila por cada campo del UDT.

### 3.1 Crear UDT_SensorData

Nombre: UDT_SensorData

Como hacerlo en la tabla de TIA (sin escribir STRUCT):

1. Crea el data type UDT_SensorData.
2. En la grilla agrega 4 filas:
   1. Name = temperature, Data type = Real, Default = 0.0
   2. Name = humidity, Data type = Real, Default = 0.0
   3. Name = active, Data type = Bool, Default = false
   4. Name = reserve, Data type = Byte, Default = 0
3. Guarda y compila ese data type.

Resultado esperado:

1. stride de 10 bytes por sensor
2. compatible con lectura de Scada_Control

### 3.2 Crear UDT_MotorState

Nombre: UDT_MotorState

Como hacerlo en tabla, opcion A (compacta recomendada):

1. Crea el data type UDT_MotorState.
2. En la grilla agrega 6 filas:
   1. cmd_run, Bool, false
   2. is_running, Bool, false
   3. auto_mode, Bool, false
   4. enabled, Bool, false
   5. fault, Bool, false
   6. reserve, Byte, 0
3. Guarda y compila.

Como hacerlo en tabla, opcion B (tu formato actual de captura):

1. motor_type, Int, 0
2. cmd_run, Bool, false
3. is_running, Bool, false
4. auto_mode, Bool, false
5. enabled, Bool, false
6. speed_sp, Real, 0.0
7. speed_fb, Real, 0.0

Si usas opcion B, en Scada_Control debes usar:

1. SCADA_MOTOR_BLOCK_SIZE=12
2. SCADA_MOTOR_FLAGS_BYTE_OFFSET=2

Si ya tienes UDT_MotorState en formato tabla como este:

1. motor_type : Int
2. cmd_run : Bool
3. is_running : Bool
4. auto_mode : Bool
5. enabled : Bool
6. speed_sp : Real
7. speed_fb : Real

puedes mantenerlo, pero debes configurar Scada_Control para ese layout:

1. SCADA_MOTOR_BLOCK_SIZE=12
2. SCADA_MOTOR_FLAGS_BYTE_OFFSET=2

Esto es porque los bits bool suelen quedar en el byte 2 cuando hay un INT al inicio.

### 3.3 Crear UDT_MonitorSilo (nivel + gas)

Nombre: UDT_MonitorSilo

Como hacerlo en tabla paso a paso (este es el que te esta costando):

1. En PLC data types, click derecho en Add new data type.
2. Nombre: UDT_MonitorSilo.
3. En la grilla, agrega estas filas exactamente en este orden:
   1. Name = flags, Data type = Byte, Default = 0
   2. Name = reserved_a, Data type = Array[0..2] of Byte, Default = vacio
   3. Name = gas_ppm, Data type = Real, Default = 0.0
   4. Name = gas_flags, Data type = Byte, Default = 0
   5. Name = reserved_b, Data type = Array[0..6] of Byte, Default = vacio
4. Guarda el UDT.
5. Compila solo este UDT (click derecho -> Compile).

Notas importantes:

1. No tienes que escribir TYPE ni STRUCT en ningun lado.
2. Todo se hace en filas de tabla.
3. Si no te deja escribir Array[0..2] of Byte, usa el selector de tipo y busca ARRAY.
4. El orden de filas importa para los offsets.

Checklist rapido para verificar que quedo bien:

1. flags en fila 1
2. reserved_a en fila 2
3. gas_ppm en fila 3
4. gas_flags en fila 4
5. reserved_b en fila 5
6. El UDT compila sin errores

Objetivo de tamano:

1. 16 bytes por silo
2. asi DB100 con 4 silos ocupa 64 bytes

Mapeo de bits recomendado:

1. flags.%X0 -> level_high
2. flags.%X1 -> level_low
3. gas_flags.%X0 -> gas_active
4. gas_flags.%X1 -> gas_warn
5. gas_flags.%X2 -> gas_trip

## 4) Crear Data Blocks desde cero

Ruta en TIA:

1. Program blocks
2. Add new block
3. Data block

Para cada DB:

1. Quita optimized block access.
2. Define solo variables necesarias.

En la tabla del DB se crea una sola fila principal cuando el DB contiene un ARRAY.

Ejemplo DB1:

1. Name = sensor
2. Data type = ARRAY[0..15] OF UDT_SensorData

### 4.1 DB1 SensorData

Nombre: SensorData
Numero: 1

Contenido:

```pascal
sensor : ARRAY[0..15] OF UDT_SensorData;
```

### 4.2 DB2 MotorControl

Nombre: MotorControl
Numero: 2

Contenido:

```pascal
motor : ARRAY[0..23] OF UDT_MotorState;
```

### 4.3 DB de puertas (reemplazo de DB13)

Nombre: GateControl
Numero recomendado: 30

Contenido:

```pascal
gate : ARRAY[0..21] OF BYTE;
```

Mapeo fijo por puerta gate[i]:

1. %X0 cmd_open reservado -> FALSE
2. %X1 cmd_close reservado -> FALSE
3. %X2 is_open
4. %X3 is_closed
5. %X4 in_motion
6. %X5 fault
7. %X6 reservado -> FALSE
8. %X7 reservado -> FALSE

### 4.4 DB100 MonitorData

Nombre: MonitorData
Numero: 100

Contenido:

```pascal
silo : ARRAY[0..3] OF UDT_MonitorSilo;
```

## 5) Configurar entradas fisicas con direcciones absolutas (%I / %IW)

Esta version no usa PLC tags. Todo va por direccion directa.

### 5.1 Obtener direcciones fisicas

1. Ve a Device configuration.
2. Selecciona CPU o modulo de entradas.
3. En Properties busca Addresses.
4. Anota rangos de entradas digitales (I...) y analogicas (IW...).

Ejemplo de direcciones (solo referencia):

1. Puertas digitales: %I0.0 ... %I10.7
2. Nivel/gas digital: %I11.0 ... %I11.7
3. Analogicas: %IW64, %IW66, %IW68, %IW70, ...

### 5.2 Regla de uso

1. Bool digital siempre con %Ibyte.bit, por ejemplo %I0.0
2. Entero analogico crudo con %IWxx, por ejemplo %IW64
3. Escribe esas direcciones directamente en FC1 y OB1

### 5.3 Mapa base sugerido (prueba)

Puerta 0:

1. abierta -> %I0.0
2. cerrada -> %I0.1
3. moviendo -> %I0.2
4. falla -> %I0.3

Puerta 1:

1. abierta -> %I0.4
2. cerrada -> %I0.5
3. moviendo -> %I0.6
4. falla -> %I0.7

Repite la secuencia por bytes para las puertas 2..21.

Nivel y gas (ejemplo):

1. HL S1 -> %I11.0
2. LL S1 -> %I11.1
3. GAS ACTIVE S1 -> %I11.2
4. GAS PPM S1 -> %IW80

## 6) Crear FC1 ScaleAnalogInputs (con %IW)

## 6) Crear FC1 ScaleAnalogInputs

Ruta:

1. Program blocks
2. Add new block
3. Function (FC)
4. Nombre: ScaleAnalogInputs

Codigo base con direcciones absolutas (ajusta segun tu hardware):

```pascal
// TEMP vars FC1:
// #raw_value : INT;
// #scaled    : REAL;

// T-S1 -> sensor[0]
#raw_value := %IW64;
#scaled := INT_TO_REAL(#raw_value) / 10.0; // PT100 ejemplo
"SensorData".sensor[0].temperature := #scaled;
"SensorData".sensor[0].humidity := 0.0;
"SensorData".sensor[0].active := TRUE;

// H-S1 -> sensor[1]
#raw_value := %IW66;
#scaled := INT_TO_REAL(#raw_value) * 100.0 / 27648.0; // 4-20mA ejemplo
IF #scaled < 0.0 THEN #scaled := 0.0; END_IF;
IF #scaled > 100.0 THEN #scaled := 100.0; END_IF;
"SensorData".sensor[1].temperature := 0.0;
"SensorData".sensor[1].humidity := #scaled;
"SensorData".sensor[1].active := TRUE;

// T-S2 -> sensor[2]
#raw_value := %IW68;
#scaled := INT_TO_REAL(#raw_value) / 10.0;
"SensorData".sensor[2].temperature := #scaled;
"SensorData".sensor[2].humidity := 0.0;
"SensorData".sensor[2].active := TRUE;

// H-S2 -> sensor[3]
#raw_value := %IW70;
#scaled := INT_TO_REAL(#raw_value) * 100.0 / 27648.0;
IF #scaled < 0.0 THEN #scaled := 0.0; END_IF;
IF #scaled > 100.0 THEN #scaled := 100.0; END_IF;
"SensorData".sensor[3].temperature := 0.0;
"SensorData".sensor[3].humidity := #scaled;
"SensorData".sensor[3].active := TRUE;

// T-S3 -> sensor[4]
#raw_value := %IW72;
#scaled := INT_TO_REAL(#raw_value) / 10.0;
"SensorData".sensor[4].temperature := #scaled;
"SensorData".sensor[4].humidity := 0.0;
"SensorData".sensor[4].active := TRUE;

// H-S3 -> sensor[5]
#raw_value := %IW74;
#scaled := INT_TO_REAL(#raw_value) * 100.0 / 27648.0;
IF #scaled < 0.0 THEN #scaled := 0.0; END_IF;
IF #scaled > 100.0 THEN #scaled := 100.0; END_IF;
"SensorData".sensor[5].temperature := 0.0;
"SensorData".sensor[5].humidity := #scaled;
"SensorData".sensor[5].active := TRUE;

// T-S4 -> sensor[6]
#raw_value := %IW76;
#scaled := INT_TO_REAL(#raw_value) / 10.0;
"SensorData".sensor[6].temperature := #scaled;
"SensorData".sensor[6].humidity := 0.0;
"SensorData".sensor[6].active := TRUE;

// H-S4 -> sensor[7]
#raw_value := %IW78;
#scaled := INT_TO_REAL(#raw_value) * 100.0 / 27648.0;
IF #scaled < 0.0 THEN #scaled := 0.0; END_IF;
IF #scaled > 100.0 THEN #scaled := 100.0; END_IF;
"SensorData".sensor[7].temperature := 0.0;
"SensorData".sensor[7].humidity := #scaled;
"SensorData".sensor[7].active := TRUE;
```

## 7) Programar OB1 (Main) con direcciones absolutas

Este OB1 no controla actuadores. Solo llena DB para SCADA.

```pascal
// TEMP vars OB1:
// #i : INT;
// #gasWarnTh : REAL;
// #gasTripTh : REAL;

// 1) Sensores analogicos
"ScaleAnalogInputs"();

// 2) Estados de motores (DB2)
FOR #i := 0 TO 23 DO
    "MotorControl".motor[#i].cmd_run := FALSE; // reservado
   // Si no tienes arrays de señales de motor, deja FALSE temporal
   // o reemplaza por asignaciones directas motor por motor.
   "MotorControl".motor[#i].is_running := FALSE;
   "MotorControl".motor[#i].auto_mode  := FALSE;
   "MotorControl".motor[#i].enabled    := TRUE;
   "MotorControl".motor[#i].fault      := FALSE;
END_FOR;

// 3) Estados de puertas (DB30 BYTE)
FOR #i := 0 TO 21 DO
    "GateControl".gate[#i].%X0 := FALSE;
    "GateControl".gate[#i].%X1 := FALSE;
    "GateControl".gate[#i].%X6 := FALSE;
    "GateControl".gate[#i].%X7 := FALSE;

   // Opcion general: reemplazar con tus %I reales, puerta por puerta.
END_FOR;

// Ejemplo directo de 2 puertas con %I
"GateControl".gate[0].%X2 := %I0.0;
"GateControl".gate[0].%X3 := %I0.1;
"GateControl".gate[0].%X4 := %I0.2;
"GateControl".gate[0].%X5 := %I0.3;

"GateControl".gate[1].%X2 := %I0.4;
"GateControl".gate[1].%X3 := %I0.5;
"GateControl".gate[1].%X4 := %I0.6;
"GateControl".gate[1].%X5 := %I0.7;

// 4) Nivel + gas (DB100)
#gasWarnTh := 20.0;
#gasTripTh := 40.0;

"MonitorData".silo[0].flags.%X0 := %I11.0;
"MonitorData".silo[0].flags.%X1 := %I11.1;
"MonitorData".silo[0].gas_ppm := INT_TO_REAL(%IW80);
"MonitorData".silo[0].gas_flags.%X0 := %I11.2;
"MonitorData".silo[0].gas_flags.%X1 := "MonitorData".silo[0].gas_ppm >= #gasWarnTh;
"MonitorData".silo[0].gas_flags.%X2 := "MonitorData".silo[0].gas_ppm >= #gasTripTh;

"MonitorData".silo[1].flags.%X0 := %I11.3;
"MonitorData".silo[1].flags.%X1 := %I11.4;
"MonitorData".silo[1].gas_ppm := INT_TO_REAL(%IW82);
"MonitorData".silo[1].gas_flags.%X0 := %I11.5;
"MonitorData".silo[1].gas_flags.%X1 := "MonitorData".silo[1].gas_ppm >= #gasWarnTh;
"MonitorData".silo[1].gas_flags.%X2 := "MonitorData".silo[1].gas_ppm >= #gasTripTh;

"MonitorData".silo[2].flags.%X0 := %I11.6;
"MonitorData".silo[2].flags.%X1 := %I11.7;
"MonitorData".silo[2].gas_ppm := INT_TO_REAL(%IW84);
"MonitorData".silo[2].gas_flags.%X0 := %I12.0;
"MonitorData".silo[2].gas_flags.%X1 := "MonitorData".silo[2].gas_ppm >= #gasWarnTh;
"MonitorData".silo[2].gas_flags.%X2 := "MonitorData".silo[2].gas_ppm >= #gasTripTh;

"MonitorData".silo[3].flags.%X0 := %I12.1;
"MonitorData".silo[3].flags.%X1 := %I12.2;
"MonitorData".silo[3].gas_ppm := INT_TO_REAL(%IW86);
"MonitorData".silo[3].gas_flags.%X0 := %I12.3;
"MonitorData".silo[3].gas_flags.%X1 := "MonitorData".silo[3].gas_ppm >= #gasWarnTh;
"MonitorData".silo[3].gas_flags.%X2 := "MonitorData".silo[3].gas_ppm >= #gasTripTh;
```

Si no conoces todas las direcciones aun:

1. Arranca con 2 puertas y 1 silo de gas/nivel usando direcciones de prueba.
2. Valida en Watch table.
3. Expande al resto copiando el mismo patron.

## 8) Como saber exactamente que bit es de cada puerta

La regla es siempre la misma:

1. gate[0] es puerta 0
2. gate[1] es puerta 1
3. gate[21] es puerta 21

Dentro de cada gate[i]:

1. %X2 abierta
2. %X3 cerrada
3. %X4 moviendo
4. %X5 falla

Ejemplo:

1. gate[7].%X2 = estado abierta de puerta 7
2. gate[7].%X5 = estado falla de puerta 7

## 9) Configurar Scada_Control (.env)

Editar Scada_Control/.env:

1. SCADA_PLC_IP=IP_DE_LA_CPU
2. SCADA_PLC_RACK=0
3. SCADA_PLC_SLOT=1
4. SCADA_DB_GATES=30
5. SCADA_GATE_BLOCK_SIZE=1
6. SCADA_MOTOR_BLOCK_SIZE=2
7. SCADA_MOTOR_FLAGS_BYTE_OFFSET=0
8. SCADA_DB_MONITOR=100
9. SCADA_MONITOR_STRIDE=16

Si mantienes tu UDT_MotorState actual (motor_type, speed_sp, speed_fb):

1. SCADA_MOTOR_BLOCK_SIZE=12
2. SCADA_MOTOR_FLAGS_BYTE_OFFSET=2

Reiniciar servicio:

1. docker compose --env-file .env up -d --build

## 10) Validacion completa (TIA + SCADA)

1. Compilar software completo en TIA.
2. Download a CPU/PLCSIM.
3. Watch table:
   1. DB1.sensor[0..7] cambia con entradas analogicas.
   2. DB2.motor[0..23] cambia con feedback real.
   3. DB30.gate[0..21].%X2/%X3/%X4/%X5 cambia con feedback de puertas.
   4. DB100.silo[0..3] cambia en nivel/gas.
4. En web de Scada_Control valida que valores coinciden.

## 11) Errores frecuentes y solucion

1. No lee nada en Python:
   1. Revisar optimized block access desactivado.
   2. Revisar numero de DB en .env (SCADA_DB_GATES/SCADA_DB_MONITOR).
    3. Revisar layout motor en .env (SCADA_MOTOR_BLOCK_SIZE y SCADA_MOTOR_FLAGS_BYTE_OFFSET).
2. Estados de puerta invertidos:
   1. Revisar mapeo de DI en OB1 (abierta/cerrada).
3. Humedad/temperatura cruzada:
   1. Revisar indices en FC1 contra contrato de DB1.
4. Gas siempre en cero:
   1. Revisar escala AI y tipo de dato REAL en DB100.
5. Motores siempre OFF en web con DB2 lleno:
    1. Revisar si UDT_MotorState tiene campos extra (INT/REAL).
    2. Ajustar SCADA_MOTOR_BLOCK_SIZE y SCADA_MOTOR_FLAGS_BYTE_OFFSET.

## 12) Proximo paso recomendado

Cuando tengas el modelo exacto de sensor de gas:

1. Ajustar escala real en OB1 (ppm, %LEL, mg/m3).
2. Ajustar umbrales warn/trip por fabricante.
3. Agregar flag de fault del transmisor de gas.

## 13) Tutorial principiante: arrancar sin conocer el cableado DI/AI

Este camino es para ti si:

1. Tienes CPU y hardware, pero no sabes aun que canal fisico corresponde a cada senal.
2. Quieres que la web funcione ya en modo solo visualizacion.
3. Quieres evitar depender de %I/%IW mientras levantas el sistema.

Idea central:

1. El PLC llena los DB de SCADA con senales internas de CPU (M/MW/MD o variables ya existentes).
2. La web lee esos DB por Snap7.
3. Mas adelante cambias el origen de datos (de M a %I/%IW o a DB reales) sin romper la web.

### 13.1 Resultado final que debes lograr

Al final de esta seccion debes tener:

1. DB1, DB2, DB30 y DB100 compilados y con datos.
2. OB1 escribiendo esos DB en cada ciclo.
3. Scada_Control mostrando estados y valores en la web.
4. Cero escritura desde web al PLC.

### 13.2 Preparacion minima (10 minutos)

1. Haz backup del proyecto TIA.
2. Compila All para asegurar base sana.
3. Verifica que estos DB existan y no sean optimized:
   1. DB1 SensorData
   2. DB2 MotorControl
   3. DB30 GateControl
   4. DB100 MonitorData

Si no existen, crealos con las secciones 3 y 4 de esta guia.

### 13.3 Crear una fuente temporal de datos dentro de CPU

No usaremos entradas fisicas aun. Usaremos memoria interna.

Reserva este bloque de marcas (puedes cambiarlo despues):

1. M100.0..M110.7 para estados de compuertas.
2. M120.0..M130.7 para estados de motores.
3. MW200..MW230 para analogicos (temperatura/humedad/gas).
4. M140.0..M141.7 para nivel alto/bajo y gas activo.

### 13.4 OB1 minimo para poblar DB de SCADA

Usa este patron en OB1 para arrancar. Si ya tienes parte del OB1, integra solo estas asignaciones.

```pascal
// TEMP vars OB1:
// #i : INT;
// #gasWarnTh : REAL;
// #gasTripTh : REAL;
// #raw : INT;

#gasWarnTh := 20.0;
#gasTripTh := 40.0;

// 1) Sensores DB1 usando MW (sin %IW por ahora)
// sensor[0] temp
#raw := MW200;
"SensorData".sensor[0].temperature := INT_TO_REAL(#raw) / 10.0;
"SensorData".sensor[0].humidity := 0.0;
"SensorData".sensor[0].active := TRUE;

// sensor[1] humedad
#raw := MW202;
"SensorData".sensor[1].temperature := 0.0;
"SensorData".sensor[1].humidity := INT_TO_REAL(#raw) * 100.0 / 27648.0;
"SensorData".sensor[1].active := TRUE;

// sensor[2] temp
#raw := MW204;
"SensorData".sensor[2].temperature := INT_TO_REAL(#raw) / 10.0;
"SensorData".sensor[2].humidity := 0.0;
"SensorData".sensor[2].active := TRUE;

// sensor[3] humedad
#raw := MW206;
"SensorData".sensor[3].temperature := 0.0;
"SensorData".sensor[3].humidity := INT_TO_REAL(#raw) * 100.0 / 27648.0;
"SensorData".sensor[3].active := TRUE;

// 2) Motores DB2: toma bits de marcas internas
FOR #i := 0 TO 23 DO
    "MotorControl".motor[#i].cmd_run := FALSE;
    "MotorControl".motor[#i].is_running := M120.0;
    "MotorControl".motor[#i].auto_mode := M120.1;
    "MotorControl".motor[#i].enabled := TRUE;
    "MotorControl".motor[#i].fault := M120.2;
END_FOR;

// 3) Compuertas DB30: usa 4 bits por puerta (open/closed/moving/fault)
// Gate 0 ejemplo con M100.x
"GateControl".gate[0].%X0 := FALSE;
"GateControl".gate[0].%X1 := FALSE;
"GateControl".gate[0].%X2 := M100.0;
"GateControl".gate[0].%X3 := M100.1;
"GateControl".gate[0].%X4 := M100.2;
"GateControl".gate[0].%X5 := M100.3;
"GateControl".gate[0].%X6 := FALSE;
"GateControl".gate[0].%X7 := FALSE;

// Gate 1 ejemplo con M100.x
"GateControl".gate[1].%X0 := FALSE;
"GateControl".gate[1].%X1 := FALSE;
"GateControl".gate[1].%X2 := M100.4;
"GateControl".gate[1].%X3 := M100.5;
"GateControl".gate[1].%X4 := M100.6;
"GateControl".gate[1].%X5 := M100.7;
"GateControl".gate[1].%X6 := FALSE;
"GateControl".gate[1].%X7 := FALSE;

// Repite patron para gate[2]..gate[21] usando M101.x, M102.x, etc.

// 4) Monitor DB100 (4 silos) con marcas y palabras internas
"MonitorData".silo[0].flags.%X0 := M140.0;
"MonitorData".silo[0].flags.%X1 := M140.1;
"MonitorData".silo[0].gas_ppm := INT_TO_REAL(MW220);
"MonitorData".silo[0].gas_flags.%X0 := M140.2;
"MonitorData".silo[0].gas_flags.%X1 := "MonitorData".silo[0].gas_ppm >= #gasWarnTh;
"MonitorData".silo[0].gas_flags.%X2 := "MonitorData".silo[0].gas_ppm >= #gasTripTh;

"MonitorData".silo[1].flags.%X0 := M140.3;
"MonitorData".silo[1].flags.%X1 := M140.4;
"MonitorData".silo[1].gas_ppm := INT_TO_REAL(MW222);
"MonitorData".silo[1].gas_flags.%X0 := M140.5;
"MonitorData".silo[1].gas_flags.%X1 := "MonitorData".silo[1].gas_ppm >= #gasWarnTh;
"MonitorData".silo[1].gas_flags.%X2 := "MonitorData".silo[1].gas_ppm >= #gasTripTh;

"MonitorData".silo[2].flags.%X0 := M140.6;
"MonitorData".silo[2].flags.%X1 := M140.7;
"MonitorData".silo[2].gas_ppm := INT_TO_REAL(MW224);
"MonitorData".silo[2].gas_flags.%X0 := M141.0;
"MonitorData".silo[2].gas_flags.%X1 := "MonitorData".silo[2].gas_ppm >= #gasWarnTh;
"MonitorData".silo[2].gas_flags.%X2 := "MonitorData".silo[2].gas_ppm >= #gasTripTh;

"MonitorData".silo[3].flags.%X0 := M141.1;
"MonitorData".silo[3].flags.%X1 := M141.2;
"MonitorData".silo[3].gas_ppm := INT_TO_REAL(MW226);
"MonitorData".silo[3].gas_flags.%X0 := M141.3;
"MonitorData".silo[3].gas_flags.%X1 := "MonitorData".silo[3].gas_ppm >= #gasWarnTh;
"MonitorData".silo[3].gas_flags.%X2 := "MonitorData".silo[3].gas_ppm >= #gasTripTh;
```

Nota para motores:

1. Si tu UDT_MotorState es el formato largo (12 bytes), mantiene:
   1. SCADA_MOTOR_BLOCK_SIZE=12
   2. SCADA_MOTOR_FLAGS_BYTE_OFFSET=2
2. Si usas formato corto, usa:
   1. SCADA_MOTOR_BLOCK_SIZE=2
   2. SCADA_MOTOR_FLAGS_BYTE_OFFSET=0

### 13.5 Probar sin hardware real (Watch table)

1. Crea una watch table.
2. Agrega estas variables para forzar cambios manuales:
   1. M100.0, M100.1, M100.2, M100.3
   2. M140.0, M140.1, M140.2
   3. MW220
3. Cambia valores en runtime:
   1. M100.0 = 1 y M100.1 = 0 -> puerta abierta
   2. MW220 = 35 -> gas en warning/trip segun umbral
4. Verifica DB30 y DB100 en la misma watch table.

### 13.6 Configurar la web para leer esos DB

En Scada_Control/.env deja:

1. SCADA_PLC_IP=IP_DE_TU_CPU
2. SCADA_PLC_RACK=0
3. SCADA_PLC_SLOT=1
4. SCADA_DB_GATES=30
5. SCADA_GATE_BLOCK_SIZE=1
6. SCADA_DB_MONITOR=100
7. SCADA_MONITOR_STRIDE=16
8. SCADA_MOTOR_BLOCK_SIZE=12 o 2 segun tu UDT
9. SCADA_MOTOR_FLAGS_BYTE_OFFSET=2 o 0 segun tu UDT

Arrancar servicio:

1. docker compose --env-file .env up -d --build
2. Abrir web de Scada_Control
3. Confirmar que cambios en M/MW se reflejan en pantalla

### 13.7 Migracion futura a senales reales sin romper la web

Cuando ya conozcas el cableado:

1. Reemplaza en OB1 cada origen M/MW por %I/%IW o DB de campo.
2. No cambies estructura de DB1/DB2/DB30/DB100.
3. No cambies .env salvo que cambie numero de DB.

Con esto mantienes estable el contrato PLC <-> Web.

### 13.8 Checklist final de principiante

1. Compila sin errores en TIA.
2. Download a CPU o PLCSIM.
3. DB1/DB2/DB30/DB100 se actualizan online.
4. La web muestra cambios al modificar M/MW.
5. No hay ninguna escritura desde la web al PLC.