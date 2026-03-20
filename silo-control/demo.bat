@echo off
title SCADA Demo




REM Simulate temperatures
start "SCADA Simulate" cmd /k "cd /d %~dp0 && call ..\entorno\Scripts\activate && python simulate_temperatures.py"

timeout /t 2 /nobreak >nul

REM Backend FastAPI (expuesto en toda la red)
start "SCADA Backend" cmd /k "cd /d %~dp0 && call ..\entorno\Scripts\activate && uvicorn api.main:app --reload --host 0.0.0.0 --port 8090"

timeout /t 2 /nobreak >nul

REM Frontend Vite (expuesto en toda la red)
start "SCADA Frontend" cmd /k "cd /d %~dp0web && npm run dev -- --host 0.0.0.0"

pause
