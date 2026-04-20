@echo off
title SCADA Demo

set "ROOT=%~dp0.."




REM Backend FastAPI (expuesto en toda la red)
REM (el simulador corre internamente dentro del backend cuando SENSOR_SOURCE="sim")
start "SCADA Backend" cmd /k "cd /d %ROOT% && call ..\entorno\Scripts\activate && uvicorn api.main:app --reload --host 0.0.0.0 --port 8090"

timeout /t 2 /nobreak >nul

REM Frontend Vite (expuesto en toda la red)
start "SCADA Frontend" cmd /k "cd /d %ROOT%\web && npm run dev -- --host 0.0.0.0"

pause
