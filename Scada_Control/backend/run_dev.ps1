Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

uvicorn app.main:app --reload --host 0.0.0.0 --port 8100 --app-dir backend
